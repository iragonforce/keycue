# keycue

**Context-aware shortcut lighting for a physical keyboard.** The longer-term goal is to show the actions available under the currently held modifiers and active application by illuminating their keycaps. Initially, the supported hardware is the **legacy Keychron K2 RGB V2** connected over USB to an Arch Linux / Hyprland desktop (`tensor`).

**Status: v0.1.0, manual proof-of-concept only.** In a physical test on 2026-11-22, Linux sent 22 HID feature reports in **174.5 ms** and the user visually confirmed that **V, T and F were white and all other key LEDs were off**. The runtime in this repository has passed offline tests, but has **not yet been exercised on the user's physical keyboard**.

## Phase 1: One-shot direct-HID control

- [x] Prove the K2's USB protocol and 84-key colour mapping (`V/T/F` confirmed physically).
- [x] Implement a dependency-free, one-shot Linux CLI with tests and dry-run default.
- [ ] Confirm the packaged CLI against the physical K2; verify non-white colours and alternate keys.
- [ ] Determine whether HID effect-area writes persist to flash/EEPROM. **Block rapid and automated updates until resolved.**
- [ ] Investigate a safe, nonpersistent lighting update path and benchmark actual visible latency (target <50 ms; stretch <20 ms).

See [the roadmap](docs/PLAN.md), [safety policy](docs/SAFETY.md), and [recorded evidence](docs/EXPERIMENTS.md).

## Usage on tensor

Requires Python 3.11+, Linux `hidraw`, and a **wired USB connection**. Does not require OpenRGB, QMK, hidapi, or other Python packages.

From the repository root (no installation necessary):

```bash
python3 -m unittest discover -s tests -v
python3 -m keycue identify
python3 -m keycue analyze  # offline protocol report, no USB access
python3 -m keycue keys
python3 -m keycue set --keys V,T,F --color white
python3 -m keycue set --paint 'V,T,F=#FFFFFF' --paint 'R,M,P=#0000FF'
python3 -m keycue off
```

The above `set` and `off` commands are **dry runs**: they print the planned colour map without opening the keyboard.

**One manual hardware test only, after reading the safety notes:**

```bash
sudo /usr/bin/python3 -m keycue set --keys V,T,F --color white \
  --apply --acknowledge-persistence-risk
```

With stock udev permissions (`root:root`, `0660` on the tested machine), `sudo` is needed. `sudo` is used **only** for a selected manual hardware write; no permanent udev rule is installed. Run from the repository root so `python3 -m keycue` resolves the local package.

Optionally, if you want all keys dark, use `off` with the same two explicit flags **once**, but note that this also submits a full HID effect configuration and may persist. It is **not** a safe fast-off shortcut.

### Example key names

`V`, `T`, `F`, `LSUPER`, `LSHIFT`, `ESC`, `F1`–`F12`, `SPACE`, `ENTER`, `LEFT`, `UP`, `RIGHT`, `DOWN`, `PGUP`, `PGDN`. See `python3 -m keycue keys` for all 84 logical positions. Other physical key mappings are based on the legacy K2 driver and need visual confirmation.

### Transfer diagnostics (safe offline mode)

`python3 -m keycue analyze` prints the 25-step feature-report transaction, the exact number of writes and reads, and the minimum requested pacing time. It **does not access the keyboard**.

A `--trace-timing` flag is available with an explicitly approved single `--apply` operation to show the ioctl and pacing duration of each *existing* operation. It does not change the HID command sequence or add extra transfers, but **it does not remove persistence risk** and is not a reason to repeat hardware experiments. No loops, daemon or automatic updates are enabled.

### Current limitations

- The command uses the **complete 22-write configuration transaction**, not an optimized live-update mode.
- Repeated modifier-driven updates, animations, background services, polling, and auto-start are **intentionally not implemented**.
- `bcdDevice=1.04` was observed, but does not independently establish the installed firmware version.
- Keyboard persistence, full key layout accuracy, and hardware-visible colour-change timing are **not yet verified**.
- `05ac:024f` is shared by other Keychron models; the CLI detects interface 0 but does not assert hardware revision from USB ID alone.
- It doesn't store or reconstruct the keyboard's original on-device lighting settings.

## Repository provenance

The source was informed by [WestSmit/Artemis.Plugins.KeychronK2](https://github.com/WestSmit/Artemis.Plugins.KeychronK2), particularly `KeychronLegacyLighting` and the key-to-LED mapping, and [OpenRGB's KeychronKeyboardController](https://github.com/CalcProgrammer1/OpenRGB/tree/master/Controllers/KeychronKeyboardController). Those projects demonstrate related 64-byte feature-report protocols; the transaction included here was separately physically tested on the user's K2. Protocol adaptation is licensed GPL-2.0-or-later to remain compatible with OpenRGB's code licensing. See [`LICENSE`](LICENSE).

**Host configuration authority:** `iragonforce/ops`. This repository contains application/protocol code and project documents. Any eventual systemd units, udev rules, and host deployment records belong in `ops` and must follow its `AGENTS.md` and `docs/START-HERE.md` policy.
