# Hardware safety and rollback

## Why this is restricted

The verified K2 lighting transaction issues `WRITE_LED_SPECIAL_EFFECT_AREA` (`0x13`) and includes a full page of effect configuration on **every** pattern change. Its persistence behavior is unknown. It **might** modify onboard flash/EEPROM, creating wear if used for every modifier press. A successful visual test does not establish that automated lighting is safe.

### Allowed in v0.1

- All read-only commands (`identify`, `keys`, dry-run `set`/`off`).
- One explicit, human-approved manual HID test using `--apply --acknowledge-persistence-risk`, with physical observation and no automatic retry.

### Prohibited until safety research is complete

- Polling, high-frequency updates, animations, shortcut-event integration, timers, boot auto-start, or systemd services that invoke the current 22-report protocol.
- Speculative `LED_SYNC_*` commands or firmware flashing.
- Modifying global OpenRGB settings, the K2 firmware, udev rules, or USB driver binding merely to run this CLI.

## Preflight

1. Use wired USB and a separate input option if available.
2. Note the keyboard's current built-in RGB mode and brightness. **The existing stored state cannot currently be read or saved.**
3. Ensure `python3 -m keycue identify` shows exactly one compatible interface 0.
4. Run unit tests and the dry-run first. Compare expected colours and buffer positions.
5. Confirm that no other software is actively writing to this K2's lighting interface (OpenRGB has historically had this detector disabled).

## What to do if something goes wrong

- Stop sending HID commands. The CLI does not auto-retry.
- Select a built-in keyboard lighting effect using the physical lighting controls. If needed, disconnect/reconnect USB to recover normal operation.
- Do **not** flash firmware or send undocumented reset commands as a recovery shortcut.
- No permanent host configuration is modified, so there is no software service or udev change to roll back.
- The original *exact* lighting configuration cannot currently be restored automatically. Hardware lighting reset behaviour is unverified.
- Record the symptom, tool output, and firmware identifiers in `docs/EXPERIMENTS.md` before proceeding.

The `off` command also performs a complete effect-write transaction; it is **not** a guaranteed read-only or memory-safe rollback mechanism.
