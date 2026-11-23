# Evidence ledger

## 2026-11-21 / 2026-11-22 — legacy Keychron K2, tensor

**User-supplied read-only evidence**

- Wired USB: manufacturer `Keychron`, product `Keychron K2`, VID:PID `05ac:024f`, `bcdDevice=1.04`.
- Linux HID: `0003:05AC:024F.0005` (USB interface 0, `/dev/hidraw1` at observation); `.0006` (interface 1, `/dev/hidraw9`).
- Interface 0 advertised 64-byte HID Feature report; input/output reports also present.
- `/dev/hidraw1` and `/dev/hidraw9` had `root:root` and mode `0660`.
- OpenRGB 1.1 was running and its `Keychron Gaming Keyboard 1` detector was disabled. Other RGB controllers were detected.

**User-supplied active hardware proof**

- Ran single Python HID transaction by direct ioctl on `/dev/hidraw1` as root.
- Sent **22 HID writes** plus three reads in **174.5 ms** reported wall time.
- Specified LED positions: `V=70`, `T=39`, `F=54`, all white; other RGB triplets zero.
- User **visually confirmed**: only `V`, `T`, `F` illuminated white, every other key fully dark.
- The command ended without a reported error. Normal typing after the test was **not independently confirmed**.
- The 174.5 ms measurement was USB operation wall time, **not an instrumented LED-visible response time**.
- No systematic endurance tests, reboot-state comparison, or alternate colour verification performed.

**What remains unknown**

- Whether `0x13` effect-area commands write persistent nonvolatile storage.
- Whether the firmware supports a low-latency transient streaming protocol.
- Whether all 84 logical keys match the K2 hardware layout on this particular unit.
- Actual firmware version; `bcdDevice=1.04` is only a USB device revision.

## 2026-11-23 — repository implementation

- Added a pure-Python port of the verified 22-write feature-report sequence, packaged as a manual CLI.
- Tests compare report counts, command order, V/T/F indices, all-black background, and default dry-run safety.
- **Software-only verification**; the repository implementation has **not been executed on the physical K2**.

## 2026-11-23 — tensor repository validation (user-reported)

- User ran the packaged code on `tensor`, branch `main`: 14/14 unit tests passed, `identify` selected `/dev/hidraw1` with read and write access, and the V/T/F CLI dry-run showed positions `70,39,54`, 22 writes, 3 reads.
- No physical `keycue --apply` test was reported; earlier V/T/F visual verification remains specific to the historical one-shot script.
- User published `iragonforce/keycue` on GitHub; visibility changed to public.

## 2026-11-23 — P1.3 source review + offline instrumentation (development environment)

- Inspected the actual `keycue` baseline at GitHub `main` commit `d0b24d1` and reviewed the K2-specific Artemis and OpenRGB controllers.
- Found no authoritative evidence that the legacy `0x13` configuration writes are nonpersistent, and no verified K2 V2 RAM-only streaming transfer sequence. See `PROTOCOL.md` for sources and remaining gaps.
- Implemented an **offline** `analyze` command and optional per-transfer timing instrumentation for an explicitly approved one-shot hardware write; the transaction, pacing and number of HID calls are unchanged.
- In an isolated Linux environment with fake/mock HID calls, 19/19 unit tests passed. The user has not run this updated implementation on `tensor` yet. No keyboard access occurred in this stage.
