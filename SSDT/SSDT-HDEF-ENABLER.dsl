/*
 * SSDT-HDEF-ENABLER.dsl
 * GA-EP45T-UD3LR / macOS 10.6.8 Snow Leopard, Lion and 10.8.5 Mountain Lion
 * AppleALC-Mod-ALC888-Layout-9-Codec-Address-2
 *
 * Provides AppleALC layout 9 and reports AppleHDA layout 9.
 * Includes cosmetic model and name properties for System Information.
 *
 * Required OpenCore ACPI rename:
 *     AZAL -> HDEF
 */
DefinitionBlock ("", "SSDT", 2, "OCLT", "HDA-L9", 0x00000006)
{
    External (_SB_.PCI0.HDEF, DeviceObj)

    Scope (\_SB.PCI0.HDEF)
    {
        Method (_DSM, 4, NotSerialized)  // _DSM: Device-Specific Method
        {
            If (_OSI ("Darwin"))
            {
                If ((Arg2 == Zero))
                {
                    Return (Buffer (One)
                    {
                        0x03
                    })
                }

                Return (Package (0x14)
                {
                    "AAPL,slot-name",
                    Buffer (0x09)
                    {
                        "Built in"
                    },

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

                    "device_type",
                    Buffer (0x11)
                    {
                        "Audio Controller"
                    },

                    "built-in",
                    Buffer (One)
                    {
                        0x00
                    },

                    "PinConfigurations",
                    Buffer (Zero) {},

                    "hda-gfx",
                    Buffer (0x0A)
                    {
                        "onboard-1"
                    },

                    "model",
                    Buffer (0x20)
                    {
                        "Realtek ALC888 Audio Controller"
                    },

                    "name",
                    Buffer (0x20)
                    {
                        "Realtek ALC888 Audio Controller"
                    }
                })
            }

            Return (Buffer (One)
            {
                0x00
            })
        }
    }
}
