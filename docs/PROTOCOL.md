# Legacy K2 RGB protocol (observed/inferred)

**Scope:** USB-connected Keychron K2 RGB V2, `05ac:024f`, HID interface 0 (physical path ends `/input0`). Its USB HID descriptor includes a 64-byte **Feature** report. The working Linux transfer uses report ID `0x00` followed by 64 data bytes; Linux's `HIDIOCSFEATURE(65)` and `HIDIOCGFEATURE(65)` ioctls send/read it.

This protocol was adapted from published OpenRGB/Artemis implementations and its **whole 22-write sequence** was visually confirmed to produce a white V/T/F pattern. Only the whole transaction is validated; individual commands were not tested in isolation.

## Transaction

| Step | Direction | Content | Count |
|---|---|---|---:|
| 1 | Host → K2 | Header `04 18` (enable customization) | 1 |
| 2 | K2 → Host | Get Feature report | 1 |
| 3 | Host → K2 | Header `04 13`, byte 8 = `0x12` (begin 18 effect pages) | 1 |
| 4 | K2 → Host | Get Feature report | 1 |
| 5 | Host → K2 | Five 64-byte effect-definition pages | 5 |
| 6 | Host → K2 | Three zero pages | 3 |
| 7 | Host → K2 | Nine 64-byte RGB pages (576 bytes total) | 9 |
| 8 | Host → K2 | Selected mode (`0x80`, brightness `0x0f`, trailer `AA 55`) | 1 |
| 9 | Host → K2 | Header `04 02` (communication end) | 1 |
| 10 | K2 → Host | Get Feature report | 1 |
| 11 | Host → K2 | Header `04 F0` (start effect) | 1 |

Total: **22 writes, 3 reads**. One-millisecond software pacing is added after each operation; the prior physical script measured 174.5 ms for the transaction including other overhead.

## Colour payload

The 576-byte colour buffer consists of 144 records (`flag,red,green,blue`). For each of the mapped 84 keys, `flag=0x80`; unlit keys have `red=green=blue=0`. `LED_SEQUENCE_POSITIONS` maps an 84-key ordinal to the record number. `KEY_INDICES` maps a named key to its ordinal.

The three physically verified records are: `V → 70`, `T → 39`, `F → 54`. White is `80 FF FF FF` at each of those records.

**Do not assume:** the command `0x13` writes only RAM, or that `0xF1/0xF2/0xF3` (sync commands seen in driver source) are supported on this particular K2 firmware. The safe protocol for repeated, transient updates is not yet known.

## Reference implementations

- [WestSmit, KeychronLegacyLighting/RgbController.cs](https://github.com/WestSmit/Artemis.Plugins.KeychronK2/blob/main/KeychronLegacyLighting/RgbController.cs)
- [WestSmit, KeychronLegacyLighting/LedsSequencePositions.cs](https://github.com/WestSmit/Artemis.Plugins.KeychronK2/blob/main/KeychronLegacyLighting/LedsSequencePositions.cs)
- [WestSmit, KeychronLegacyLighting/RGB.NET/LedMapings.cs](https://github.com/WestSmit/Artemis.Plugins.KeychronK2/blob/main/KeychronLegacyLighting/RGB.NET/LedMapings.cs)
- [OpenRGB, KeychronKeyboardController.cpp](https://github.com/CalcProgrammer1/OpenRGB/blob/master/Controllers/KeychronKeyboardController/KeychronKeyboardController.cpp) (same USB ID used for K3 V2, so not a safe independent K2 detector)
