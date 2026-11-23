# Virtual shortcut layers (hardware-free prototype)

This is a **manual simulation**, not a listener for Hyprland, applications, or the keyboard. It never opens `/dev/hidraw*` or sends RGB commands. Its purpose is to validate shortcut mapping, modifier resolution, and an output frame format while the persistence safety of K2 effect-area writes remains unresolved.

## Usage

```bash
python3 -m keycue preview --modifiers SUPER
python3 -m keycue preview --modifiers SUPER+SHIFT
python3 -m keycue preview --app ghostty --modifiers CTRL+SHIFT
python3 -m keycue preview --app zen --modifiers SUPER --format json
python3 -m keycue preview --profile profiles/demo.toml --modifiers SUPER --format json
```

The bundled `profiles/demo.toml` contains **invented demonstration actions**, not confirmed Hyprland, Ghostty, Zen, tmux, Neovim, or FreeCAD bindings. No real shortcuts have been extracted from `iragonforce/ops`.

## Versioned TOML schema

```toml
version = 1

[[layers]]
scope = "global"
modifiers = ["SUPER"]
[layers.keys]
V = { color = "#FFFFFF", action = "Example action description" }
T = { color = "#00FF00", action = "Another example" }

[[layers]]
scope = "app:ghostty"
modifiers = ["CTRL", "SHIFT"]
[layers.keys]
T = { color = "#FFAA00", action = "Example app action" }
```

- Scope is `global` or `app:<label>`; app context is supplied manually with `--app <label>`.
- Modifiers are `SUPER`, `SHIFT`, `CTRL`, `ALT` (order independent; common aliases supported). Exact modifier combinations match; `SUPER+SHIFT` will **not** inherit `SUPER` keys.
- App-specific exact layers take precedence. If an app lacks an exact layer, a matching global layer is used. Layers are replacements, **not** combined overlays. This rule is provisional until actual Hyprland/app shortcut precedence is modelled.
- Every key must exist in the K2 84-key mapping; aliases normalize to canonical key names. Duplicate keys/layers and invalid colours are rejected.
- Each action has `color` in `#RRGGBB` notation and a textual description. All unspecified keys are black in the *virtual frame*.
- Output JSON contains `requested_scope`, `modifiers`, `matched_scope`, `background`, total/off counts, and key-to-colour/action/physical packet-position mapping. A future UI can consume this output; the existing HID write path is intentionally disconnected.

## Future integration boundaries

1. Populate verified shortcut metadata from the actual host and application configuration, rather than inventing bindings.
2. Wire a separate context provider for held modifiers and active app only after an architecture review; do **not** use the existing persistent-effect HID transaction to drive real-time LEDs.
3. Once a nonpersistent RGB path is established, translate virtual frames into hardware frames through an explicit transport adapter.
4. The secondary-monitor overlay should consume the same virtual frame representation, without stealing keyboard focus.

Use `python3 -m unittest discover -s tests -v` to run all tests offline. No additional Python dependencies are required (Python 3.11+).
