# aero-rgb

Keyboard backlight control for the **GIGABYTE AERO X16** on Linux. It's a single Python file that uses only the standard library.

The AERO X16 keyboard (USB `0414:8104`) puts its backlight behind a standard
[HID LampArray](https://learn.microsoft.com/en-us/windows-hardware/design/component-guidelines/dynamic-lighting-devices)
interface. Windows calls this "Dynamic Lighting". The backlight is one RGB zone. `aero-rgb` sends it HID feature reports through `/dev/hidraw`.

Tested on an AERO X16 1VH running Ubuntu 24.04 with GNOME. This project is unofficial and not affiliated with GIGABYTE.

## Usage

```
aero-rgb color ff8800              set the backlight color (name or hex)
aero-rgb color red --brightness 40
aero-rgb off | on                  turn it off, or back to the last setting
aero-rgb toggle                    off if on, on if off (bind this to Fn+Space)
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

Fn+Space also sends F20, which the desktop keymap treats as microphone mute.
This hwdb entry changes that key to `PROG1` (`XF86Launch1`) on this keyboard only:

```bash
sudo cp ~/src/aero-rgb/61-gigabyte-aero-x16-fn-space.hwdb /etc/udev/hwdb.d/
sudo systemd-hwdb update && sudo udevadm trigger --subsystem-match=input --action=change
```

Then bind `XF86Launch1` to `aero-rgb toggle`. On GNOME:

```bash
P=/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings/aero-rgb-toggle/
K="org.gnome.settings-daemon.plugins.media-keys.custom-keybinding:$P"
gsettings set org.gnome.settings-daemon.plugins.media-keys custom-keybindings "['$P']"
gsettings set "$K" name 'Keyboard backlight toggle'
gsettings set "$K" command "$HOME/.local/bin/aero-rgb toggle"
gsettings set "$K" binding 'XF86Launch1'
```

The first `gsettings` line replaces your list of custom shortcuts. If you already have some, add this path to the list instead.

After `aero-rgb auto`, `toggle` does nothing, so the firmware's own Fn+Space brightness steps work again.

## Limitations

- The LampArray protocol has no "save" command. The keyboard may return to its built-in lighting after a reboot.
- The keyboard reports one lamp, so per-key colors are not possible.
- The firmware's built-in effects are set through a separate, undocumented GIGABYTE interface. `aero-rgb` does not use it.

## License

[MIT](LICENSE)
