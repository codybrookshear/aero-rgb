# aero-rgb

Keyboard backlight control for the **GIGABYTE AERO X16** on Linux. The command and optional hotkey listener use only the Python standard library.

The AERO X16 keyboard (USB `0414:8104`) puts its backlight behind a standard
[HID LampArray](https://learn.microsoft.com/en-us/windows-hardware/design/component-guidelines/dynamic-lighting-devices)
interface. Windows calls this "Dynamic Lighting". The backlight is one RGB zone. `aero-rgb` sends it HID feature reports through `/dev/hidraw`.

Tested on an AERO X16 1VH running Ubuntu 24.04 with GNOME. This project is unofficial and not affiliated with GIGABYTE.

## Usage

```
aero-rgb color ff8800              set the backlight color (name or hex)
aero-rgb color red --brightness 40
aero-rgb off | on                  turn it off, or back to the last setting
aero-rgb toggle                    off if on, on if off
aero-rgb effect breathe --color cyan
aero-rgb effect cycle --speed 0.1  fade through the color wheel
aero-rgb auto                      hand control back to the keyboard firmware
aero-rgb info                      show what the keyboard reports
```

Effects run until you stop them. Running `color`, `effect` or `auto` stops a running effect. `toggle` pauses it and resumes it instead.

The last setting is saved in `~/.local/state/aero-rgb/state.json`.

## Install

Clone the repository and link the script onto your `PATH`:

```bash
git clone https://github.com/codybrookshear/aero-rgb.git ~/src/aero-rgb
ln -s ~/src/aero-rgb/aero-rgb ~/.local/bin/aero-rgb
```

By default, only root can open `/dev/hidraw*`. This udev rule gives the logged-in user the keyboard's lighting interface (USB interface 4) and nothing else. The keyboard's other interfaces carry keystrokes, so they stay root-only.

```bash
sudo cp ~/src/aero-rgb/60-gigabyte-aero-x16-kbd.rules /etc/udev/rules.d/
sudo udevadm control --reload && sudo udevadm trigger --subsystem-match=hidraw
```

## Fn+Space

The firmware handles Fn+Space by itself only while it runs its own lighting. Once `aero-rgb` sets a color, Fn+Space does nothing to the backlight.

The previous setup remapped F20 to `PROG1` (`XF86Launch1`) and bound it to
`aero-rgb toggle`. That shortcut also fires on Fn alone, so it cannot be used
as a Fn+Space binding. If you installed it, disable the shortcut on GNOME:

```bash
P=/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/aero-rgb-toggle/
K="org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$P"
gsettings set "$K" binding ''
```

You can still run `aero-rgb toggle` manually or bind it to another shortcut.

### Working Fn+Space support

Fn alone sends F20 (remapped to `PROG1` by the legacy hwdb entry). Holding Fn
suppresses the normal Space key event. Fn+Space instead sends a vendor report
on USB interface 2: `04 01 LL 00`, where `LL` is the firmware brightness value.
Captures on the AERO X16 1VH include `00`, `18`, `20`, and `32`. `aero-rgb-hotkeys` recognizes the
notification type regardless of brightness and runs one toggle per report;
Fn alone and ordinary Space do nothing to the backlight.

Install the listener and enable it for your account:

```bash
sudo install -m 755 aero-rgb /usr/local/bin/aero-rgb
sudo install -D -m 644 aero-rgb-hotkeys /usr/local/libexec/aero-rgb-hotkeys
sudo install -m 644 aero-rgb-hotkeys@.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now "aero-rgb-hotkeys@$USER.service"
```

Keep the GNOME `XF86Launch1` shortcut disabled. The hwdb remap is not required
by the listener. The existing lighting-interface udev rule is still required.
The listener reads the shared input interface as root, discards ordinary key
reports without logging them, and executes `aero-rgb toggle` as your account.
It uses that account's default `~/.local/state/aero-rgb/state.json`.
The service retries if the keyboard disconnects and starts again after reboot.

If a press is missed, inspect the listener log:

```bash
journalctl -u "aero-rgb-hotkeys@$USER.service" -n 30 --no-pager
```

It records the vendor brightness level and toggle duration, plus unexpected
brightness notifications that were ignored. Ordinary key reports are never
logged. A successful dispatch means the command exited successfully; it does
not verify the physical light changed.

To stop and disable the listener:

```bash
sudo systemctl disable --now "aero-rgb-hotkeys@$USER.service"
```

After `aero-rgb auto`, `toggle` does nothing, so the firmware's own Fn+Space brightness steps work again.

## Limitations

- The LampArray protocol has no "save" command. The keyboard may return to its built-in lighting after a reboot.
- The keyboard reports one lamp, so per-key colors are not possible.
- The firmware's built-in effects are set through a separate, undocumented GIGABYTE interface. `aero-rgb` does not use it.

## License

[MIT](LICENSE)
