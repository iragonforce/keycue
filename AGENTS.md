# Agent instructions for keycue

1. Read `docs/PLAN.md`, `docs/SAFETY.md` and `docs/EXPERIMENTS.md` before planning HID changes.
2. Treat `iragonforce/ops` as the source of truth for host deployment/infrastructure; check its `AGENTS.md` and `docs/START-HERE.md` before modifying `tensor` configuration.
3. Separate physical observations from protocol inference. The single confirmed physical pattern is V/T/F white, others off, using the historical 22-report script on 2026-11-22.
4. DO NOT implement or enable repeated, event-driven, or scheduled HID effect writes until nonvolatile storage behavior is verified. The current effect-area write (`0x13`) might persist to flash.
5. No firmware flashing, undocumented raw USB experiments, permanent permission changes, or uncontrolled hardware loops without a risk assessment, rollback method and explicit human approval.
6. Tests must run without any USB access. Default CLI actions must not touch hardware.
7. Stop on device ambiguity, failed HID calls, or incorrect visual mapping; do not retry hardware writes automatically.
8. Document measured results and hardware testing in `docs/EXPERIMENTS.md` with dates, commands, outcomes, and uncertainties.
9. Prefer a minimal native user-session controller when safe streaming is established; do not create redundant background frameworks or databases.
