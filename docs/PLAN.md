# Implementation plan — keycue

## Objective

Make keyboard LEDs serve as a **contextual shortcut guide**. Example: holding Super in Hyprland illuminates only `V`, `T`, and `F` in white; adding Shift changes the illuminated keys. Future versions also convey the currently focused application's available actions. The keyboard remains a normal input device.

## Constraints

- Host: `tensor` (Arch Linux, Hyprland, wired Keychron K2 RGB V2).
- Preserve stock firmware and the existing OpenRGB setup for other devices.
- Avoid redundant services, invasive remapping, or changing existing shortcut bindings.
- Treat `iragonforce/ops` as the host deployment source of truth.
- All automatic repeated writes **blocked** while nonvolatile persistence is unknown.

## Milestones

| Stage | Deliverable | Acceptance | State |
|---|---|---|---|
| P1.0 | Identify K2 HID, confirm V/T/F | Only V/T/F white, all other keys off | **Physically verified** 2026-11-22 |
| P1.1 | Reproducible CLI + mapping + tests | Dry-run by default; 22 writes generated; no dependencies | **Implemented; offline tests passed** |
| P1.2 | Test packaged CLI on K2 | Exactly correct pattern; input still works; document latency | **Pending** |
| P1.3 | Nonvolatile persistence analysis | Evidence-based determination of write endurance / memory effects | **Research in progress; still unverified and blocking loops** |
| P1.4 | Low-latency safe update transport | Nonpersistent update, repeatably <50 ms end-to-end if hardware permits | **Pending research** |
| P2.0 | Hyprland layer resolver | Super/Super+Shift map without altering existing binds | **Pending P1.4** |
| P2.1 | Focused app layers | Zen Browser, FreeCAD, Ghostty, Neovim, tmux | **Pending P2.0** |
| P3.0 | Secondary display overlay | Show current key labels and actions on secondary monitor | **Pending P2.0** |

### Immediate next action

Review and merge the P1.3 offline diagnostics branch, pull to `tensor`, and run `python3 -m unittest discover -s tests -v` followed by `python3 -m keycue analyze`. Both operations are software-only; they must not send USB HID commands. Continue firmware persistence research before scheduling or looping writes. A physical `--apply` test is not needed for this validation.

### P1.3 evidence plan (read-only first)

1. Find the exact K2 V2 board/controller and relevant firmware/reverse engineering references.
2. Establish what `WRITE_LED_SPECIAL_EFFECT_AREA` (`0x13`) does (RAM, flash, or EEPROM). The OpenRGB `AUTOMATIC_SAVE` flag is suggestive but not conclusive.
3. Investigate the documented-but-unverified `LED_SYNC_INITIAL`/`START`/`STOP` commands from published drivers/firmware, without sending speculative commands to live hardware.
4. Only after evidence supports a safe transient protocol: add a separate transport, mock tests and an opt-in manual A/B timing benchmark. Keep the old transaction as an explicitly risky fallback.

### Phase 2 interface proposal (not implemented)

`modifier_state + active_window + application_state -> ShortcutMap -> LED key-colour frame`.
Use event changes, not polling or permanent remaps; preserve a normal base layer. Initially expose a static Hyprland map, then app-specific adapters. Use a low-priority, user-session service only if a safe, nonpersistent update path has been proven.

### Phase 3 interface proposal (not implemented)

An optional Wayland overlay anchored to the secondary monitor, showing a key diagram with action descriptions corresponding to the current modifier/application layer. It must not intercept keyboard focus or appear on the primary gaming/work display.

## Operational risks and rollback

See `SAFETY.md`. No firmware flash is in scope. Since original onboard RGB state is not backed up, a true bit-for-bit lighting-state rollback is unavailable; user-selected built-in effects are the immediate visual fallback. No persistent host config is changed by v0.1.
