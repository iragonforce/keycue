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

## P1.3 research update — 2026-11-23

**No verified RAM-only lighting path has been identified for this legacy firmware.**

- The stock-firmware OpenRGB controller issues `WRITE_LED_SPECIAL_EFFECT_AREA` (`0x13`) before a full multi-page effect upload, and marks its `Custom` mode `MODE_FLAG_AUTOMATIC_SAVE`. Neither the command name nor the flag independently proves whether the MCU stores RGB data in flash/EEPROM or only in RAM. Source: [OpenRGB Keychron controller](https://github.com/CalcProgrammer1/OpenRGB/blob/master/Controllers/KeychronKeyboardController/KeychronKeyboardController.cpp), [OpenRGB RGB controller](https://github.com/CalcProgrammer1/OpenRGB/blob/master/Controllers/KeychronKeyboardController/RGBController_KeychronKeyboard.cpp).
- The K2-specific [Artemis plugin](https://github.com/WestSmit/Artemis.Plugins.KeychronK2/blob/main/KeychronLegacyLighting/RgbController.cs) uses the same full page upload on every update with 1 ms pacing. This establishes a working control path but **not** a safe low-latency streaming path.
- Both reference implementations define `LED_SYNC_INITIAL` (`0xF1`), `LED_SYNC_START` (`0xF2`) and `LED_SYNC_STOP` (`0xF3`), but do not implement a documented K2 V2 live-update transaction using them. **Do not send these commands experimentally.**
- An [OpenRGB upstream issue](https://gitlab.com/CalcProgrammer1/OpenRGB/-/issues/1790) links an older translated communications protocol PDF for a **K3 V2 Optical RGB**, which shares `05ac:024f` but has a distinct board/firmware identity. That issue warns of incorrect mappings and lighting-key behaviour. The PDF has not been independently reviewed in this project, so none of its contents is treated as verified K2 behaviour.
- [Keychron's K2 V2 firmware page](https://keychron.ch/pages/firmware-for-k2-version-2) lists an RGB `V1.04` release. The observed USB `bcdDevice=1.04` is consistent with, but does not prove, that installed firmware version. No firmware change is proposed.

**Decision:** Keep the verified 22-write legacy transaction opt-in and manual only. A daily modifier-driven shortcut guide depends on documenting a transient update mechanism or obtaining reliable firmware-level evidence that the existing transaction does not cause endurance-sensitive writes.

### Diagnosing transfer overhead without changing the protocol

Run `python3 -m keycue analyze` for a hardware-free description of the 25 transfer operations. It includes report byte counts and explicit risk warnings.

A future, separately approved single manual hardware experiment can add `--trace-timing` alongside `--apply --acknowledge-persistence-risk`. Timing instrumentation does **not** add any HID reads/writes or change the 1 ms pacing; it only measures each existing ioctl and sleep. It still carries the persistence risk of the original 22-write transaction and must **not** be repeated for profiling or benchmarking until storage safety is established. These timings do **not** measure LED-visible latency.
