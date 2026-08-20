# AppleALC 1.6.8 – ALC888 Layout 9 / Codec Address 2 Mod

## Bring Vanilla-Style AppleHDA Audio Back to Classic Hackintosh Hardware

This mod brings **native AppleHDA audio through AppleALC** to the **Gigabyte GA-EP45T-UD3LR** and its onboard **Realtek ALC888** — without installing a permanently patched `AppleHDA.kext`.

It was created specifically for the unusual but fully working combination of **ALC888 + Layout 9 + codec address 2**, making proper legacy audio possible on retro macOS installations from the **Snow Leopard / Darwin 10 era through the Yosemite / Darwin 14 era**.

**Production 1.2 is live-tested on Mac OS X Snow Leopard 10.6.8 and OS X Mountain Lion 10.8.5.** The build targets the wider Darwin 10–14 range; later systems in that range, including **OS X Yosemite 10.10 (Darwin 14)**, are compatibility targets and have not all been live-tested on this machine.

The same mod may also be useful on **other motherboards using a Realtek ALC888 at codec address 2**, provided their audio pin routing is compatible with this Layout 9 profile.

### Other ALC888 / Codec Address 2 Motherboards Worth Testing

The following boards are useful search targets for this mod because Linux codec dumps or historical AppleHDA/LegacyHDA reports show **Realtek ALC888 with codec address 2**, or successful use of the same classic Gigabyte ALC888 address-2 configuration:

```text
Gigabyte GA-EP45T-UD3LR   - tested with this AppleALC mod
Gigabyte GA-P43-DS3       - confirmed ALC888, codec address 2
Gigabyte GA-EX58-UD3R     - confirmed ALC888, codec address 2
Gigabyte GA-EP43-UD3L     - historical ALC888 address-2 AppleHDA success reports
Gigabyte GA-EP45-UD3LR    - historical ALC888 address-2 AppleHDA success reports
Gigabyte GA-EP45-UD3L     - historical ALC888 address-2 AppleHDA success reports
Gigabyte GA-EP35-DS3L     - historical ALC888 address-2 LegacyHDA/AppleHDA reports
Gigabyte GA-EP43-DS3L     - reported as a closely related candidate
```

These names are intentionally listed here so users searching for combinations such as **"GA-EP45-UD3L AppleALC"**, **"GA-P43-DS3 ALC888"**, **"EX58-UD3R AppleALC"** or **"EP35-DS3L ALC888 codec address 2"** can find this project.

**Only the GA-EP45T-UD3LR has been confirmed with this exact Production 1.2 AppleALC mod.** The other boards are candidates, not guaranteed-compatible systems. Gigabyte also shipped different audio implementations across some board revisions, so always verify the actual codec before installing.

Under Linux, check all HDA codecs with:

```bash
grep -H -E '^(Codec|Address|Vendor Id|Subsystem Id):' /proc/asound/card*/codec#*
```

For this profile, the expected codec should look like:

```text
Codec: Realtek ALC888
Address: 2
Vendor Id: 0x10ec0888
```

and will normally be available as:

```bash
cat /proc/asound/card0/codec#2
```

A matching **ALC888 + Address 2** is the first requirement, but it is not by itself proof of compatibility. The board's pin defaults/routing must also be compatible with this mod's **Layout 9 / Platforms9 / PinConfig** profile.

> **This is not an official Acidanthera release.**
>
> It is a hardware-specific modification based on AppleALC 1.6.8.

---

## Quick Start

The release package contains:

```text
AppleALC.kext
AppleALC.kext.dSYM
SSDT-HDEF-ENABLER.aml
SSDT-HDEF-ENABLER.dsl
```

For normal use you need:

```text
AppleALC.kext
SSDT-HDEF-ENABLER.aml
```

### OpenCore

1. Copy `AppleALC.kext` to:

```text
EFI/OC/Kexts/
```

and add it under:

```text
Kernel -> Add
```

`Lilu.kext` must be loaded before `AppleALC.kext`.

2. Copy `SSDT-HDEF-ENABLER.aml` to:

```text
EFI/OC/ACPI/
```

and add it under:

```text
ACPI -> Add
```

**The supplied HDEF SSDT is required for this profile.**

3. **Do not set any `alcid=` boot argument.**

Do not use, for example:

```text
alcid=9
```

and do not inject a second/different `layout-id` through OpenCore `DeviceProperties`.

The supplied SSDT already injects the required:

```text
layout-id       = 9
apple-layout-id = 9
use-layout-id   = 1
```

For this mod, keep the audio configuration simple: **Lilu + AppleALC + the supplied HDEF SSDT, with no `alcid` override.**

---

## Checking the Codec Under Linux

Before trying this mod on another motherboard, Linux can be used to verify the actual HDA codec and its hardware address.

A convenient overview is:

```bash
grep -H -E '^(Codec|Address|Vendor Id|Subsystem Id):' /proc/asound/card*/codec#*
```

For a codec located at address 2, the relevant file is typically:

```bash
cat /proc/asound/card0/codec#2
```

For the target hardware you should see an ALC888 / Realtek codec with vendor ID:

```text
0x10ec0888
```

and:

```text
Address: 2
```

The filename `codec#2` also indicates HDA codec address 2.

**Important:** AppleALC `Layout ID 9` is a macOS/AppleHDA profile selection, not a hardware value reported by Linux. Linux can confirm the codec model, codec address and pin configuration, but it cannot tell you that your board is “Layout 9”. Compatibility with this mod therefore also depends on the board's pin routing matching the included Layout 9 / Platforms9 / PinConfig profile.

---

## Purpose

The stock AppleALC 1.6.8 release supports the Realtek ALC888 family, but it does not contain the exact profile required by this motherboard.

The GA-EP45T-UD3LR used here needs:

- Realtek **ALC888**
- Codec ID **0x10EC0888**
- **Layout ID 9**
- Codec address **2**
- A matching custom `Platforms9` configuration
- Matching ALC888 pin configuration data

The important point is that generic ALC888 support alone is not enough.

On this board the codec is enumerated at **HDA codec address 2**, and the working audio routing is tied to the custom **layout 9 / Platforms9 / pin-config profile** contained in this mod.

The normal upstream AppleALC 1.6.8 does not provide this exact board-specific ALC888 layout 9 profile, so simply injecting `layout-id = 9` into an unmodified AppleALC 1.6.8 is not sufficient.

This mod adds and preserves the exact working profile.

---

## Target Hardware

Test system:

```text
Mainboard:        Gigabyte GA-EP45T-UD3LR
Audio codec:      Realtek ALC888
Codec ID:         0x10EC0888
Codec ID decimal: 283904136
Codec address:    2
Layout ID:        9
```

The build is intentionally specific to this configuration.

It should not be considered a general-purpose replacement for the normal AppleALC release.

---

## What Was Added / Changed

The mod contains the following board-specific audio configuration:

```text
Resources/ALC888/layout9.xml
Resources/ALC888/Platforms9-...
Resources/ALC888/Info.plist
Resources/PinConfigs.kext/Contents/Info.plist
```

The relevant HDA configuration uses:

```text
CodecID:    283904136  (0x10EC0888)
LayoutID:   9
FuncGroup:  1
Codec Addr: 2
```

The custom `layout9` and `Platforms9` data provide the actual audio topology and routing required by this board.

The pin configuration is supplied by AppleALC itself rather than injected through ACPI.

---

## Software DSP / Stable Output Level

The custom layout also retains the working signal-processing path used by this profile.

The relevant layout structure includes:

```text
SignalProcessing
└── SoftwareDSP
```

This was important for the final behavior of the analog output path.

With the final Production 1.2 build:

- analog output works
- microphone input works
- output level remains stable
- the output level no longer jumps back and forth

---

## HDEF / ACPI Configuration

The tested setup uses an HDEF SSDT that injects layout 9.

Important properties:

```text
layout-id       = 09 00 00 00
apple-layout-id = 09 00 00 00
use-layout-id   = 01
PinConfigurations = empty
```

Example:

```asl
"layout-id",
Buffer (0x04)
{
    0x09, 0x00, 0x00, 0x00
},

"use-layout-id",
Buffer (One)
{
    0x01
},

"apple-layout-id",
Buffer (0x04)
{
    0x09, 0x00, 0x00, 0x00
},

"PinConfigurations",
Buffer (Zero){}
```

The SSDT selects **layout 9**, but it does **not** set codec address 2.

Codec address 2 is the hardware HDA bus address at which this ALC888 is enumerated. The custom AppleALC profile is built for that configuration.

---

## Why the Kext Is So Small

A normal AppleALC binary contains resources for a very large number of codecs, layouts and platform configurations.

This custom build was reduced to the resources actually needed by this machine.

During verification, the old full/fat mod contained more than one thousand compressed XML resources, while the new Production 1.2 binary contains only the two audio resources needed by this profile:

```text
layout9
Platforms9
```

The resulting Production 1.2 AppleALC binary is therefore only about:

```text
75 KB
```

instead of roughly:

```text
1.65 MB
```

for the x86_64 slice of the old full build.

The small size is intentional.

The actual AppleALC program code and symbol interface remain essentially unchanged; the large reduction comes mainly from removing unused codec/layout resources.

---

## Binary Verification

The new Production 1.2 build was compared against the previously working full mod.

Verified items include:

- same AppleALC base version: **1.6.8**
- same bundle identifier
- same relevant ALC888 codec configuration
- same Layout ID 9
- same FuncGroup
- same ALC888 `ConfigData`
- same custom `layout9` after decompression
- same custom `Platforms9` after decompression
- required AppleHDA patch byte patterns still present
- same set of **444 x86_64 symbol names**
- same AppleALC/Lilu interface

The machine code is not byte-for-byte identical because the old kext and the new kext were built with different compiler/Xcode versions.

---

## Production Release Metadata

The upstream AppleALC version remains:

```text
1.6.8
```

This is intentionally **not** changed to `1.2`.

`1.2` is only the local production release number of this hardware-specific mod.

The kext contains additional descriptive metadata such as:

```text
Mainboard:            Gigabyte GA-EP45T-UD3LR
Codec:                Realtek ALC888 (0x10EC0888)
LayoutID:             9
CodecAddress:         2
ProductionRelease:    1.2
DarwinCompatibility:  Darwin 10-14
```

---

## Compatibility

The AppleALC target is built for:

```text
x86_64-apple-macos10.6
```

and is intended for the legacy Darwin range used by this project:

```text
Darwin 10 – Darwin 14
```

The current Production 1.2 binary is **x86_64 only**.

The older full build also contained an i386 slice, but the new reduced Production 1.2 build does not.

Therefore:

- 64-bit Snow Leopard: tested
- Mountain Lion: tested
- 32-bit i386 kernel: not supported by this particular binary

---

## Tested Operating Systems

### Mac OS X Snow Leopard

Tested successfully.

Working:

- AppleALC loads
- analog output works
- microphone input works
- custom Layout 9 profile works

### OS X Mountain Lion 10.8.5

Tested successfully.

Working:

- AppleALC loads
- analog output works
- microphone input works
- stable output level
- no unwanted output-level jumping

---

## Required Lilu Version

The project is based on:

```text
Lilu 1.5.9
```

For the actual Hackintosh installation, use the **Release** version of Lilu 1.5.9.

The Debug Lilu build is only required while compiling AppleALC because it contains the development resources used by AppleALC:

```text
Lilu.kext/Contents/Resources/Headers
Lilu.kext/Contents/Resources/Library
```

---

## Build Environment Used

The successful Production 1.2 build was created with:

```text
Host OS:       macOS 12.6.7 Monterey
Xcode:         13.3
Xcode build:   13E113
Apple clang:   13.1.6
SDK:           MacOSX12.3.sdk
AppleALC:      1.6.8
Lilu:          1.5.9
MacKernelSDK:  latest/current version used at build time
Architecture:  x86_64
Deployment:    macOS 10.6 for AppleALC
```

Xcode 13.3 warns that deployment targets below macOS 10.9 are outside its officially supported range, but the project still compiles and links AppleALC with:

```text
-target x86_64-apple-macos10.6
```

The resulting kext has been live-tested successfully on legacy macOS.

---

## Basic Installation

Use the kext together with the matching Lilu release and the required HDEF layout injection.

Typical OpenCore order:

```text
Lilu.kext
AppleALC.kext
```

The tested HDEF configuration injects:

```text
layout-id = 9
```

Do not additionally inject a different AppleALC layout through OpenCore boot arguments or DeviceProperties.

For a clean test, replace only `AppleALC.kext` and keep the rest of the known-good EFI configuration unchanged.

---

## Verify That AppleALC Loaded

On older macOS versions:

```bash
kextstat | grep -i applealc
```

The kext should appear as:

```text
as.vit9696.AppleALC
```

---

## Important Notes

This mod is intentionally hardware-specific.

It is designed around the exact ALC888 configuration of the tested Gigabyte GA-EP45T-UD3LR and should not automatically be expected to work on:

- other ALC888 boards
- boards where the codec appears at another codec address
- other pin configurations
- other layout IDs
- systems requiring a different `Platforms.xml`

For another motherboard, use the normal upstream AppleALC first and create a separate codec/layout profile if required.

---

## Repository Contents

Depending on the branch/release, this repository may contain:

```text
AppleALC-1.6.8-ALC888-P9-A2-ProductionRelease-1.2-Source/
AppleALC.kext
AppleALC-Mod-selbst-kompiliren.md
update-production-version.sh
README.md
```

The source tree is retained so the kext can be rebuilt later with the same board-specific resources.

---

## Preparing the Source Tree for GitHub

Before publishing the source tree, remove local build artefacts, generated checksum files and local build dependencies that should not be committed.

From the root of:

```text
AppleALC-1.6.8-ALC888-P9-A2-ProductionRelease-1.2-Source
```

run:

```bash
rm -f .DS_Store Resources.md5 Resources.tmp.md5 update-version.sh README_CN.md && rm -rf Lilu.kext .github && rm -f MacKernelSDK
```

Notes:

- `update-version.sh` is the old version-update helper and should not be published.
- Use the safer `update-production-version.sh` instead.
- `Lilu.kext` is only a local build dependency and should be rebuilt from Lilu 1.5.9.
- `MacKernelSDK` is normally a local symlink to a checkout outside this repository and should not be committed.
- `.github` from the original upstream tree is not required for this board-specific repository.
- `README_CN.md` belongs to the original upstream project and is not needed for this mod repository.
- `Resources.md5` and `Resources.tmp.md5` are generated during resource processing and should not be committed.

Recommended `.gitignore` additions:

```gitignore
.DS_Store

build/
DerivedData/

Lilu.kext
MacKernelSDK

Resources.md5
Resources.tmp.md5

work_production_*/
*.dSYM
```

A clean source repository should contain approximately:

```text
AppleALC/
AppleALC.xcodeproj/
ResourceConverter/
Resources/
Tools/
alc-verb/

BUILD-AppleALC-Production-1.2.py
PRODUCTION-1.2-SOURCE-NOTES.md
update-production-version.sh
Changelog.md
LICENSE.txt
README.md
```

---

## Building from Source

The known-good Production 1.2 build environment was:

```text
Host OS:       macOS 12.6.7 Monterey
Xcode:         13.3
Xcode build:   13E113
Apple clang:   13.1.6
SDK:           MacOSX12.3.sdk
AppleALC:      1.6.8
Lilu:          1.5.9
MacKernelSDK:  latest/current version used at build time
Architecture:  x86_64
Deployment:    macOS 10.6 for AppleALC
```

### 1. Download the required sources

AppleALC 1.6.8:

```bash
git clone --branch 1.6.8 --depth 1 \
  https://github.com/acidanthera/AppleALC.git \
  AppleALC-1.6.8
```

Lilu 1.5.9:

```bash
git clone --branch 1.5.9 --depth 1 \
  https://github.com/acidanthera/Lilu.git \
  Lilu-1.5.9
```

MacKernelSDK:

```bash
git clone https://github.com/acidanthera/MacKernelSDK.git
```

The tested directory layout was:

```text
alcbuild/
├── AppleALC-1.6.8/
├── Lilu-1.5.9/
├── MacKernelSDK/
└── AppleALC-1.6.8-ALC888-P9-A2-ProductionRelease-1.2-Source/
```

### 2. Build Lilu 1.5.9 Debug

AppleALC needs the development headers and library files contained in the **Debug** Lilu kext.

Inside `Lilu-1.5.9`:

```bash
ln -s ../MacKernelSDK MacKernelSDK
```

Then build:

```bash
rm -rf build

xcodebuild \
  -project Lilu.xcodeproj \
  -configuration Debug \
  OTHER_CFLAGS='$(inherited) -Wno-error=null-pointer-subtraction'
```

The extra warning flag is required with Xcode 13.3 because Lilu 1.5.9 otherwise hits the newer Clang `-Wnull-pointer-subtraction` diagnostic in `kern_qsort.cpp`.

The build should end with:

```text
** BUILD SUCCEEDED **
```

Verify that the development resources exist:

```bash
ls -l build/Debug/Lilu.kext/Contents/Resources/Library/plugin_start.cpp
```

### 3. Copy Debug Lilu into the AppleALC source tree

From the mod source directory:

```bash
rm -rf Lilu.kext

cp -R \
  ../Lilu-1.5.9/build/Debug/Lilu.kext \
  .
```

The Debug Lilu kext is only used while compiling AppleALC.

For the actual Hackintosh EFI, use a **Release** build of Lilu 1.5.9.

### 4. Link MacKernelSDK

Inside the mod source directory:

```bash
rm -f MacKernelSDK
ln -s ../MacKernelSDK MacKernelSDK
```

### 5. Validate the modified plist files

```bash
plutil -lint AppleALC/AppleALC-Info.plist
plutil -lint Resources/ALC888/Info.plist
plutil -lint Resources/PinConfigs.kext/Contents/Info.plist
```

All should report:

```text
OK
```

### 6. Remove old generated resource checksums

If resources were changed:

```bash
rm -f Resources.md5 Resources.tmp.md5
```

### 7. Build AppleALC Production 1.2

```bash
rm -rf build

xcodebuild \
  -project AppleALC.xcodeproj \
  -configuration Release
```

No additional `OTHER_CFLAGS` were required for AppleALC itself.

Xcode 13.3 will warn that macOS 10.6 is below its officially supported deployment range. This warning is expected.

The important part is that the AppleALC compile/link lines still use:

```text
-target x86_64-apple-macos10.6
```

and the build ends with:

```text
** BUILD SUCCEEDED **
```

The resulting kext is located at:

```text
build/Release/AppleALC.kext
```

### 8. Verify the resulting kext

Architecture:

```bash
file build/Release/AppleALC.kext/Contents/MacOS/AppleALC
```

Expected:

```text
Mach-O 64-bit kext bundle x86_64
```

Verify the upstream AppleALC version:

```bash
/usr/libexec/PlistBuddy \
  -c "Print :CFBundleVersion" \
  build/Release/AppleALC.kext/Contents/Info.plist
```

Expected:

```text
1.6.8
```

Verify the custom mod metadata:

```bash
/usr/libexec/PlistBuddy \
  -c "Print :AppleALCModInfo" \
  build/Release/AppleALC.kext/Contents/Info.plist
```

Expected values include:

```text
Mainboard = Gigabyte GA-EP45T-UD3LR
Codec = Realtek ALC888 (0x10EC0888)
LayoutID = 9
CodecAddress = 2
ProductionRelease = 1.2
DarwinCompatibility = Darwin 10-14
```

The custom Production Release number must **not** replace the upstream `CFBundleVersion`. AppleALC itself remains version **1.6.8**.

### 9. Build Lilu Release for the target system

For the actual EFI:

```bash
cd ../Lilu-1.5.9

xcodebuild \
  -project Lilu.xcodeproj \
  -configuration Release \
  OTHER_CFLAGS='$(inherited) -Wno-error=null-pointer-subtraction'
```

Use:

```text
Lilu-1.5.9/build/Release/Lilu.kext
```

together with the newly built:

```text
AppleALC.kext
```

Do not install the Debug Lilu kext used as the AppleALC build dependency.

### 10. Live test

Keep the known-good HDEF SSDT and layout injection unchanged:

```text
layout-id = 9
```

For a clean A/B test, replace only `AppleALC.kext`.

After boot:

```bash
kextstat | grep -i applealc
```

Then verify:

```text
analog output
microphone input
stable output level
sleep/wake audio state
```

Production 1.2 has been successfully tested on both Snow Leopard and Mountain Lion 10.8.5.

---

## Credits

This project is based on **AppleALC 1.6.8** and **Lilu 1.5.9** by Acidanthera / vit9696 and contributors.

Upstream projects:

- AppleALC: https://github.com/acidanthera/AppleALC
- Lilu: https://github.com/acidanthera/Lilu
- MacKernelSDK: https://github.com/acidanthera/MacKernelSDK

All credit for the original AppleALC, Lilu and MacKernelSDK code belongs to their respective authors and contributors.

This repository contains a board-specific AppleALC modification, reduced resource set, custom ALC888 profile integration, build tooling and documentation for the Gigabyte GA-EP45T-UD3LR / Realtek ALC888 configuration.

---

## License and Copyright

This repository is a derivative work based on **AppleALC 1.6.8** and therefore keeps the original **BSD 3-Clause License** for the AppleALC-derived source code.

The original `LICENSE.txt` from AppleALC must remain in the repository and must not be removed or replaced by a more restrictive repository-wide license.

Original AppleALC code:

```text
Copyright © Acidanthera / vit9696 and contributors
Licensed under the BSD 3-Clause License
```

Board-specific modifications, production build tooling and documentation created for this project:

```text
Copyright © 2026 Michael McSky
```

This includes, where originally created for this repository:

```text
GA-EP45T-UD3LR / ALC888 Layout 9 integration
Codec Address 2 production profile
Production build scripts
Version-update tooling
README / build documentation
```

These additions are distributed together with the AppleALC-derived project under the same **BSD 3-Clause License** unless a file explicitly states otherwise.

Do **not** apply a repository-wide `CC BY-NC-SA 4.0` license to this project. The `NC` restriction would conflict with the permissions granted by the upstream BSD-licensed AppleALC code.

For clarity, the recommended repository footer is:

```text
Based on AppleALC 1.6.8 by Acidanthera and contributors.
AppleALC is licensed under the BSD 3-Clause License.

GA-EP45T-UD3LR / ALC888 Layout 9 / Codec Address 2 modifications,
production build tooling and documentation:
Copyright © 2026 Michael McSky.
```

---

## Status

**Production Release 1.2**

Confirmed working on:

```text
Mac OS X Snow Leopard
OS X Mountain Lion 10.8.5
```

with:

```text
Gigabyte GA-EP45T-UD3LR
Realtek ALC888
Layout 9
Codec Address 2
Lilu 1.5.9
```
