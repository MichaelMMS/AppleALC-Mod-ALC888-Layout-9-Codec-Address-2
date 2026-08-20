#!/usr/bin/env python3
from __future__ import annotations

import copy
import hashlib
import json
import os
import plistlib
import shutil
import struct
import zipfile
from pathlib import Path
from typing import Any

BASE = Path('/mnt/data')
WORK = BASE / 'work_production_1_2'

BASE_FINAL_ZIP = BASE / 'AppleALC-1.6.8-ALC888-P9-A2-ProductionRelease-1.1-Darwin11-14.zip'
BASE_SOURCE_ZIP = BASE / 'AppleALC-1.6.8-ALC888-P9-A2-ProductionRelease-1.1-Source.zip'
BASE_FINAL_NAME = 'AppleALC-1.6.8-ALC888-P9-A2-ProductionRelease-1.1-Darwin11-14'
BASE_SOURCE_NAME = 'AppleALC-1.6.8-ALC888-P9-A2-ProductionRelease-1.1-Source'

OUT_FINAL = BASE / 'AppleALC-1.6.8-ALC888-P9-A2-ProductionRelease-1.2-Darwin10-14'
OUT_SOURCE = BASE / 'AppleALC-1.6.8-ALC888-P9-A2-ProductionRelease-1.2-Source'
OUT_FINAL_ZIP = BASE / f'{OUT_FINAL.name}.zip'
OUT_SOURCE_ZIP = BASE / f'{OUT_SOURCE.name}.zip'
BUILD_SCRIPT_NAME = 'BUILD-AppleALC-Production-1.2.py'
INDEPENDENT_PATH = BASE / 'INDEPENDENT-VALIDATION-ProductionRelease-1.2.json'
SUMMARY_PATH = BASE / 'AppleALC-Production-1.2-build-summary.json'

EXPECTED_BASE_BINARY_SHA256 = 'dc6dd00f4c9ff9c86456afa66abe028dbf075e964cfef01e189365d4eddf9bb6'
EXPECTED_CODEC_ID = 0x10EC0888
EXPECTED_LAYOUT_ID = 9
EXPECTED_CODEC_ADDRESS = 2
EXPECTED_DARWIN_MIN_OLD = 11
EXPECTED_DARWIN_MIN_NEW = 10
EXPECTED_DARWIN_MAX = 14

# Exact KextPatch entries in the byte-identical Production 1.1/v4g Mach-O.
# Only the MinKernel uint32 field changes from Darwin 11 to Darwin 10.
I386_PATCH_ENTRY_OFFSET = 0x17241C
I386_PATCH_ENTRY_OLD = bytes.fromhex(
    'c0ca1600'  # kext pointer
    '133c0200'  # find pointer (85 08 EC 10)
    '225d0d00'  # replace pointer (88 08 EC 10)
    '04000000'  # patch length
    '02000000'  # count
    '0b000000'  # MinKernel 11
    '0c000000'  # MaxKernel 12
)
I386_PATCH_ENTRY_NEW = I386_PATCH_ENTRY_OLD[:-8] + struct.pack('<II', 10, 12)

X64_PATCH_ENTRY_OFFSET = 0x1771A0
X64_PATCH_ENTRY_OLD = bytes.fromhex(
    '6025170000000000'  # kext pointer
    'fc27010000000000'  # find pointer (85 08 EC 10)
    '65e7090000000000'  # replace pointer (88 08 EC 10)
    '0400000000000000'  # patch length
    '0200000000000000'  # count
    '0b000000'          # MinKernel 11
    '0c000000'          # MaxKernel 12
)
X64_PATCH_ENTRY_NEW = X64_PATCH_ENTRY_OLD[:-8] + struct.pack('<II', 10, 12)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def extract_zip_with_modes(zip_path: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zf:
        assert zf.testzip() is None
        for info in zf.infolist():
            zf.extract(info, destination)
            target = destination / info.filename
            mode = (info.external_attr >> 16) & 0o777
            if mode and target.exists():
                os.chmod(target, mode)


def zip_tree(root: Path, out_zip: Path) -> None:
    if out_zip.exists():
        out_zip.unlink()
    with zipfile.ZipFile(out_zip, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        parent = root.parent
        for path in sorted(root.rglob('*')):
            arc = path.relative_to(parent)
            if path.is_dir():
                zi = zipfile.ZipInfo(str(arc).rstrip('/') + '/')
                zi.date_time = (1980, 1, 1, 0, 0, 0)
                zi.external_attr = (0o40755 << 16) | 0x10
                zf.writestr(zi, b'')
            else:
                zi = zipfile.ZipInfo(str(arc))
                zi.date_time = (1980, 1, 1, 0, 0, 0)
                mode = path.stat().st_mode & 0o777
                zi.external_attr = ((0o100000 | mode) << 16)
                zi.compress_type = zipfile.ZIP_DEFLATED
                zf.writestr(zi, path.read_bytes())


def parse_fat(binary: bytes) -> list[dict[str, int]]:
    magic, nfat = struct.unpack_from('>II', binary, 0)
    assert magic == 0xCAFEBABE and nfat == 2
    arches = []
    for i in range(nfat):
        cputype, cpusubtype, offset, size, align = struct.unpack_from('>IIIII', binary, 8 + i * 20)
        arches.append({
            'cputype': cputype,
            'cpusubtype': cpusubtype,
            'offset': offset,
            'size': size,
            'align': align,
        })
    return arches


def patch_binary_min_kernel(binary: bytes) -> tuple[bytes, dict[str, Any]]:
    assert sha256_bytes(binary) == EXPECTED_BASE_BINARY_SHA256
    out = bytearray(binary)
    arches = parse_fat(binary)
    changed_absolute_offsets: list[int] = []

    for arch in arches:
        if arch['cputype'] == 0x00000007:
            rel = I386_PATCH_ENTRY_OFFSET
            old_entry = I386_PATCH_ENTRY_OLD
            new_entry = I386_PATCH_ENTRY_NEW
            arch_name = 'i386'
        elif arch['cputype'] == 0x01000007:
            rel = X64_PATCH_ENTRY_OFFSET
            old_entry = X64_PATCH_ENTRY_OLD
            new_entry = X64_PATCH_ENTRY_NEW
            arch_name = 'x86_64'
        else:
            raise AssertionError(f"Unexpected CPU type 0x{arch['cputype']:X}")

        start = arch['offset'] + rel
        end = start + len(old_entry)
        assert binary[start:end] == old_entry, f'{arch_name} ALC888 patch entry mismatch'
        out[start:end] = new_entry
        min_abs = start + len(old_entry) - 8
        changed_absolute_offsets.append(min_abs)
        assert out[min_abs:min_abs+4] == struct.pack('<I', EXPECTED_DARWIN_MIN_NEW)
        assert out[min_abs+4:min_abs+8] == struct.pack('<I', 12)

    patched = bytes(out)
    diffs = [i for i, (a, b) in enumerate(zip(binary, patched)) if a != b]
    # 11 -> 10 changes only the low byte in each architecture.
    assert diffs == changed_absolute_offsets
    assert all(binary[i] == 0x0B and patched[i] == 0x0A for i in diffs)
    return patched, {
        'changed_byte_count': len(diffs),
        'changed_absolute_offsets': [f'0x{x:X}' for x in diffs],
        'old_byte': '0x0B',
        'new_byte': '0x0A',
        'semantic_change': 'ALC888 AppleHDA 0x10EC0885 -> 0x10EC0888 patch MinKernel 11 -> 10',
    }


def decode_pin_defaults(config_data: bytes) -> dict[int, int]:
    assert len(config_data) % 4 == 0
    partial: dict[int, list[int | None]] = {}
    for i in range(0, len(config_data), 4):
        a, b, cmd, value = config_data[i:i+4]
        assert (a >> 4) == EXPECTED_CODEC_ADDRESS
        nid = ((a & 0x0F) << 4) | (b >> 4)
        if cmd in (0x1C, 0x1D, 0x1E, 0x1F):
            partial.setdefault(nid, [None, None, None, None])[cmd - 0x1C] = value
    result: dict[int, int] = {}
    for nid, values in partial.items():
        if all(v is not None for v in values):
            v = [int(x) for x in values]
            result[nid] = v[0] | (v[1] << 8) | (v[2] << 16) | (v[3] << 24)
    return result


for required in (BASE_FINAL_ZIP, BASE_SOURCE_ZIP):
    if not required.exists():
        raise FileNotFoundError(required)

if WORK.exists():
    shutil.rmtree(WORK)
WORK.mkdir(parents=True)
for path in (OUT_FINAL, OUT_SOURCE):
    if path.exists():
        shutil.rmtree(path)
for path in (OUT_FINAL_ZIP, OUT_SOURCE_ZIP, INDEPENDENT_PATH, SUMMARY_PATH):
    if path.exists():
        path.unlink()

base_final_extract = WORK / 'base_final'
base_source_extract = WORK / 'base_source'
extract_zip_with_modes(BASE_FINAL_ZIP, base_final_extract)
extract_zip_with_modes(BASE_SOURCE_ZIP, base_source_extract)
base_final = base_final_extract / BASE_FINAL_NAME
base_source = base_source_extract / BASE_SOURCE_NAME
assert base_final.is_dir() and base_source.is_dir()

shutil.copytree(base_final, OUT_FINAL, copy_function=shutil.copy2)
shutil.copytree(base_source, OUT_SOURCE, copy_function=shutil.copy2)

# ---------------------------------------------------------------------------
# Runtime Kext: exact Production 1.1 baseline, with only the embedded ALC888
# AppleHDA codec-ID patch MinKernel lowered from Darwin 11 to Darwin 10.
# ---------------------------------------------------------------------------
base_binary_path = base_final / 'AppleALC.kext/Contents/MacOS/AppleALC'
final_binary_path = OUT_FINAL / 'AppleALC.kext/Contents/MacOS/AppleALC'
base_binary = base_binary_path.read_bytes()
patched_binary, binary_delta = patch_binary_min_kernel(base_binary)
final_binary_path.write_bytes(patched_binary)
os.chmod(final_binary_path, 0o755)

# Bundle metadata and sole HDAConfigDefault remain functionally identical.
final_info_path = OUT_FINAL / 'AppleALC.kext/Contents/Info.plist'
final_info = plistlib.loads(final_info_path.read_bytes())
personality = final_info['IOKitPersonalities']['as.vit9696.AppleALC']
hda = personality['HDAConfigDefault']
assert len(hda) == 1 and hda[0]['CodecID'] == EXPECTED_CODEC_ID and hda[0]['LayoutID'] == EXPECTED_LAYOUT_ID
base_config_data = bytes(hda[0]['ConfigData'])
hda[0]['Codec'] = 'GA-EP45T-UD3LR ALC888 Profile 9 Address 2 Production Release 1.2'
final_info['CFBundleDisplayName'] = 'AppleALC ALC888 P9 A2 Production 1.2'
final_info['CFBundleGetInfoString'] = 'AppleALC 1.6.8 - ALC888 Profile 9 Address 2 - Production Release 1.2'
final_info['AppleALCCustomBuild'] = (
    'GA-EP45T-UD3LR ALC888 Profile 9 Address 2 Production Release 1.2 - '
    'Production 1.1 topology unchanged - MinKernel 10.0.0 - Darwin 10-14 target'
)
final_info['AppleALCCustomDarwinRange'] = '10.0.0-14.99.99'
final_info_path.write_bytes(plistlib.dumps(final_info, fmt=plistlib.FMT_XML, sort_keys=False))

# Rename unchanged SSDT only for release clarity.
old_ssdt = OUT_FINAL / 'SSDT-HDEF-ALC888-P9-A2-Production-1.1.dsl'
new_ssdt = OUT_FINAL / 'SSDT-HDEF-ALC888-P9-A2-Production-1.2.dsl'
if old_ssdt.exists():
    old_ssdt.rename(new_ssdt)

# Remove old provenance docs/scripts before writing 1.2 equivalents.
for stale in [
    OUT_FINAL / 'TECHNICAL-MANIFEST.txt',
    OUT_FINAL / 'VALIDATION-ProductionRelease-1.1.json',
    OUT_FINAL / 'BUILD-AppleALC-Production-1.1.py',
    OUT_FINAL / 'README-DE.txt',
    OUT_FINAL / 'OPENCORE-KERNEL-RANGE.txt',
]:
    if stale.exists():
        stale.unlink()

# ---------------------------------------------------------------------------
# Pruned source: only three functional MinKernel values change:
# layout 9, platform 9, and the first ALC885->ALC888 AppleHDA patch.
# ---------------------------------------------------------------------------
source_alc_info_path = OUT_SOURCE / 'Resources/ALC888/Info.plist'
source_alc = plistlib.loads(source_alc_info_path.read_bytes())
assert len(source_alc['Files']['Layouts']) == 1
assert len(source_alc['Files']['Platforms']) == 1
assert source_alc['Files']['Layouts'][0]['MinKernel'] == EXPECTED_DARWIN_MIN_OLD
assert source_alc['Files']['Platforms'][0]['MinKernel'] == EXPECTED_DARWIN_MIN_OLD
assert source_alc['Patches'][0]['MinKernel'] == EXPECTED_DARWIN_MIN_OLD
assert source_alc['Patches'][0]['MaxKernel'] == 12
source_alc['Files']['Layouts'][0]['MinKernel'] = EXPECTED_DARWIN_MIN_NEW
source_alc['Files']['Platforms'][0]['MinKernel'] = EXPECTED_DARWIN_MIN_NEW
source_alc['Patches'][0]['MinKernel'] = EXPECTED_DARWIN_MIN_NEW
source_alc['Files']['Layouts'][0]['Comment'] = 'GA-EP45T-UD3LR ALC888 Production 1.2 layout 9'
source_alc['Files']['Platforms'][0]['Comment'] = 'GA-EP45T-UD3LR Production 1.2 v4g topology with dual SoftwareVolume'
source_alc_info_path.write_bytes(plistlib.dumps(source_alc, fmt=plistlib.FMT_XML, sort_keys=False))

source_pin_path = OUT_SOURCE / 'Resources/PinConfigs.kext/Contents/Info.plist'
source_pin = plistlib.loads(source_pin_path.read_bytes())
source_hda = source_pin['IOKitPersonalities']['as.vit9696.AppleALC']['HDAConfigDefault']
assert len(source_hda) == 1
assert bytes(source_hda[0]['ConfigData']) == base_config_data
source_hda[0]['Codec'] = 'GA-EP45T-UD3LR ALC888 Profile 9 Address 2 Production Release 1.2'
source_pin_path.write_bytes(plistlib.dumps(source_pin, fmt=plistlib.FMT_XML, sort_keys=False))

# Replace source release notes and build provenance.
for stale in [
    OUT_SOURCE / 'PRODUCTION-1.1-SOURCE-NOTES.md',
    OUT_SOURCE / 'BUILD-AppleALC-Production-1.1.py',
]:
    if stale.exists():
        stale.unlink()

(OUT_SOURCE / 'PRODUCTION-1.2-SOURCE-NOTES.md').write_text(
    '# AppleALC 1.6.8 — GA-EP45T-UD3LR Production 1.2 source\n\n'
    'Production 1.2 is a controlled derivative of Production 1.1.\n\n'
    'Functional delta only:\n\n'
    '- Layout 9 `MinKernel`: `11` → `10`;\n'
    '- Platform 9 `MinKernel`: `11` → `10`;\n'
    '- ALC885→ALC888 AppleHDA patch `MinKernel`: `11` → `10`.\n\n'
    'Everything else remains the Production 1.1 topology: ALC888, layout/platform 9, '
    'codec address 2, Rear Mic, Front In, Rear Line-In and dual `SoftwareVolume`.\n',
    encoding='utf-8',
)

shutil.copy2(Path(__file__), OUT_SOURCE / BUILD_SCRIPT_NAME)
os.chmod(OUT_SOURCE / BUILD_SCRIPT_NAME, 0o755)
shutil.copy2(Path(__file__), OUT_FINAL / BUILD_SCRIPT_NAME)
os.chmod(OUT_FINAL / BUILD_SCRIPT_NAME, 0o755)

# Final documentation.
(OUT_FINAL / 'OPENCORE-KERNEL-RANGE.txt').write_text(
    'OpenCore -> Kernel -> Add -> AppleALC.kext\n\n'
    'MinKernel: 10.0.0\n'
    'MaxKernel: 14.99.99\n\n'
    'Darwin 10 = Mac OS X Snow Leopard\n'
    'Darwin 11 = OS X Lion\n'
    'Darwin 12 = OS X Mountain Lion\n'
    'Darwin 13 = OS X Mavericks\n'
    'Darwin 14 = OS X Yosemite\n',
    encoding='utf-8',
)

(OUT_FINAL / 'README-DE.txt').write_text(
    'AppleALC 1.6.8 — ALC888 P9 A2 Production Release 1.2\n'
    '================================================================\n\n'
    'Basis: Production Release 1.1.\n'
    'Einzige funktionale Änderung: MinKernel von Darwin 11 auf Darwin 10.\n\n'
    'Zielbereich:\n'
    '  Darwin 10 bis 14: Snow Leopard, Lion, Mountain Lion, Mavericks, Yosemite\n\n'
    'Unverändert:\n'
    '  Codec: ALC888 (0x10EC0888), Adresse 2, Layout 9\n'
    '  Rear Mic:  0x09 -> 0x22 -> 0x18\n'
    '  Front In:  0x09 -> 0x22 -> 0x19\n'
    '  Line-In:   0x08 -> 0x23 -> 0x1A\n'
    '  SoftwareVolume auf ADC 0x09 und ADC 0x08\n'
    '  Front PinConfig 0x02819060 (Anzeige als Line-In)\n\n'
    'OpenCore:\n'
    '  MinKernel = 10.0.0\n'
    '  MaxKernel = 14.99.99\n\n'
    'Hinweis: Mountain Lion ist mit Production 1.1 praktisch bestätigt.\n'
    'Die Snow-Leopard-Erweiterung dieser 1.2 muss auf dem Zielsystem noch getestet werden.\n',
    encoding='utf-8',
)

# ---------------------------------------------------------------------------
# Validation.
# ---------------------------------------------------------------------------
final_info_check = plistlib.loads(final_info_path.read_bytes())
final_hda = final_info_check['IOKitPersonalities']['as.vit9696.AppleALC']['HDAConfigDefault']
assert len(final_hda) == 1
assert final_hda[0]['CodecID'] == EXPECTED_CODEC_ID
assert final_hda[0]['LayoutID'] == EXPECTED_LAYOUT_ID
assert bytes(final_hda[0]['ConfigData']) == base_config_data
pins = decode_pin_defaults(base_config_data)
assert pins[0x18] == 0x90A09050
assert pins[0x19] == 0x02819060
assert pins[0x1A] == 0x01813070

source_alc_check = plistlib.loads(source_alc_info_path.read_bytes())
assert source_alc_check['Files']['Layouts'][0]['MinKernel'] == 10
assert source_alc_check['Files']['Layouts'][0]['MaxKernel'] == 14
assert source_alc_check['Files']['Platforms'][0]['MinKernel'] == 10
assert source_alc_check['Files']['Platforms'][0]['MaxKernel'] == 14
assert [(p['MinKernel'], p['MaxKernel']) for p in source_alc_check['Patches']] == [
    (10, 12), (13, 13), (14, 14), (13, 14), (13, 14)
]

# Resource files and topology are byte-identical to Production 1.1 source.
resource_rel_paths = [
    'Resources/ALC888/layout9.xml',
    'Resources/ALC888/layout9.xml.zlib',
    'Resources/ALC888/Platforms9-GA-EP45T-UD3LR-Production-1.1.xml',
    'Resources/ALC888/Platforms9-GA-EP45T-UD3LR-Production-1.1.xml.zlib',
]
resource_hashes = {}
for rel in resource_rel_paths:
    old = base_source / rel
    new = OUT_SOURCE / rel
    assert old.read_bytes() == new.read_bytes()
    resource_hashes[rel] = sha256_file(new)

validation = {
    'release': 'AppleALC 1.6.8 ALC888 Profile 9 Address 2 Production Release 1.2',
    'baseline': 'Production Release 1.1',
    'target': {
        'codec_id': '0x10EC0888',
        'codec_address': 2,
        'layout_id': 9,
        'darwin_min': '10.0.0',
        'darwin_max': '14.99.99',
        'macos': ['Snow Leopard', 'Lion', 'Mountain Lion', 'Mavericks', 'Yosemite'],
    },
    'functional_delta': {
        'runtime_binary': binary_delta,
        'source_layout_min_kernel': [11, 10],
        'source_platform_min_kernel': [11, 10],
        'source_alc885_to_alc888_patch_min_kernel': [11, 10],
        'all_other_source_patch_ranges_unchanged': True,
    },
    'runtime_binary': {
        'base_sha256': sha256_bytes(base_binary),
        'production_1_2_sha256': sha256_bytes(patched_binary),
        'size_unchanged': len(base_binary) == len(patched_binary),
        'size': len(patched_binary),
        'architectures': ['i386', 'x86_64'],
    },
    'unchanged_profile': {
        'hda_config_data_byte_identical': bytes(final_hda[0]['ConfigData']) == base_config_data,
        'rear_mic_route': [9, 34, 24],
        'front_input_route': [9, 34, 25],
        'rear_line_in_route': [8, 35, 26],
        'front_pin_config': '0x02819060',
        'dual_software_volume': True,
        'resource_hashes': resource_hashes,
    },
    'source_patch_ranges': [(10, 12), (13, 13), (14, 14), (13, 14), (13, 14)],
    'snow_leopard_runtime_status': 'target enabled; not yet runtime-tested on the user system',
}

manifest = (
    'TECHNICAL MANIFEST — AppleALC Production Release 1.2\n'
    '=======================================================\n'
    'Baseline:                      Production Release 1.1\n'
    'Board:                         Gigabyte GA-EP45T-UD3LR\n'
    'Codec:                         Realtek ALC888 (0x10EC0888)\n'
    'Codec address:                 2\n'
    'Layout/Profile:                9\n'
    'Target Darwin range:           10.0.0 through 14.99.99\n'
    'Only functional change:        MinKernel 11 -> 10\n'
    'Runtime binary changes:        2 bytes total (one per architecture)\n'
    f'Production 1.1 binary SHA:     {sha256_bytes(base_binary)}\n'
    f'Production 1.2 binary SHA:   {sha256_bytes(patched_binary)}\n'
    f'Binary size unchanged:         {len(base_binary) == len(patched_binary)}\n'
    'HDAConfigDefault unchanged:    yes (metadata label excluded)\n'
    'Layout/platform bytes:         byte-identical to Production 1.1\n'
    'Rear Mic:                      0x09 -> 0x22 -> 0x18\n'
    'Front input:                   0x09 -> 0x22 -> 0x19\n'
    'Rear Line-In:                  0x08 -> 0x23 -> 0x1A\n'
    'Mic SoftwareVolume:            true\n'
    'Line-In SoftwareVolume:        true\n'
    'Front PinConfig:               0x02819060\n'
    'Snow Leopard runtime status:   untested on user hardware\n'
)

(OUT_FINAL / 'VALIDATION-ProductionRelease-1.2.json').write_text(
    json.dumps(validation, indent=2), encoding='utf-8'
)
(OUT_FINAL / 'TECHNICAL-MANIFEST.txt').write_text(manifest, encoding='utf-8')

zip_tree(OUT_FINAL, OUT_FINAL_ZIP)
zip_tree(OUT_SOURCE, OUT_SOURCE_ZIP)
assert zipfile.ZipFile(OUT_FINAL_ZIP).testzip() is None
assert zipfile.ZipFile(OUT_SOURCE_ZIP).testzip() is None

# Independent extraction and verification of shipped archives.
check_final_root = WORK / 'check_final'
check_source_root = WORK / 'check_source'
extract_zip_with_modes(OUT_FINAL_ZIP, check_final_root)
extract_zip_with_modes(OUT_SOURCE_ZIP, check_source_root)
shipped_final = check_final_root / OUT_FINAL.name
shipped_source = check_source_root / OUT_SOURCE.name
shipped_binary = (shipped_final / 'AppleALC.kext/Contents/MacOS/AppleALC').read_bytes()
assert shipped_binary == patched_binary
shipped_source_alc = plistlib.loads((shipped_source / 'Resources/ALC888/Info.plist').read_bytes())
assert shipped_source_alc['Files']['Layouts'][0]['MinKernel'] == 10
assert shipped_source_alc['Files']['Platforms'][0]['MinKernel'] == 10
assert shipped_source_alc['Patches'][0]['MinKernel'] == 10
assert bytes(plistlib.loads((shipped_final / 'AppleALC.kext/Contents/Info.plist').read_bytes())
             ['IOKitPersonalities']['as.vit9696.AppleALC']['HDAConfigDefault'][0]['ConfigData']) == base_config_data

independent = {
    'release': OUT_FINAL.name,
    'final_zip_integrity': 'passed',
    'source_zip_integrity': 'passed',
    'binary_sha256': sha256_bytes(shipped_binary),
    'binary_changed_bytes_vs_production_1_1': 2,
    'binary_min_kernel_patch': {'i386': 10, 'x86_64': 10},
    'source_layout_min_kernel': 10,
    'source_platform_min_kernel': 10,
    'source_first_patch_min_kernel': 10,
    'source_other_patch_ranges': [(13, 13), (14, 14), (13, 14), (13, 14)],
    'profile_data_unchanged': True,
    'target_darwin_range': [10, 14],
}
INDEPENDENT_PATH.write_text(json.dumps(independent, indent=2), encoding='utf-8')

summary = {
    'final_zip': str(OUT_FINAL_ZIP),
    'final_zip_sha256': sha256_file(OUT_FINAL_ZIP),
    'final_zip_size': OUT_FINAL_ZIP.stat().st_size,
    'source_zip': str(OUT_SOURCE_ZIP),
    'source_zip_sha256': sha256_file(OUT_SOURCE_ZIP),
    'source_zip_size': OUT_SOURCE_ZIP.stat().st_size,
    'binary_sha256': sha256_bytes(patched_binary),
    'base_binary_sha256': sha256_bytes(base_binary),
    'binary_changed_bytes': binary_delta['changed_byte_count'],
    'independent_validation': str(INDEPENDENT_PATH),
}
SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding='utf-8')
print(json.dumps(summary, indent=2))
