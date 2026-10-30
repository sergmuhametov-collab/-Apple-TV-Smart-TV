#!/usr/bin/env python3
"""
Top bar, Apple style: ONE Inputs button (first in the bar, before the day/night switch) that lists every input of
the TV in its glass menu, instead of a separate button per HDMI/AV port, and thin rounded line icons in the style
of SF Symbols for Inputs, Wi-Fi, Settings (and for the rows of the Inputs menu).

Usage:   py apple_bar.py "C:\\path\\to\\cleanyourtv-main\\launcher"

* adds 8 icon files (res/drawable/ic_apple_*.xml)
* MainActivity.java: turns the per-port buttons off (they stay in the code behind PER_INPUT_BUTTONS = false),
  moves the Inputs button to the front, uses the new icons.
Needs daynight_switch.py, daynight_first.py and inputs_bar.py applied first. All or nothing, CRLF kept,
backup in <repo>/.install-backup/MainActivity.java.apple.bak. Running it twice changes nothing.
"""
import math, os, re, shutil, sys
from xml.dom import minidom

if len(sys.argv) != 2:
    sys.exit(__doc__)
launcher = os.path.abspath(sys.argv[1])
main = os.path.join(launcher, "app", "src", "main")
path = os.path.join(main, "java", "com", "gathin", "tvhome", "MainActivity.java")
drawables = os.path.join(main, "res", "drawable")
if not os.path.exists(path):
    sys.exit(f"Not found: {path}")
s = open(path, encoding="utf-8", newline="").read()
crlf = "\r\n" in s
if crlf:
    s = s.replace("\r\n", "\n")
if "applyAppleIcons" in s:
    print("already applied, nothing to do")
    sys.exit(0)
for marker in ("bar.addView(dayNightSwitch, 0, lp);", "updateInputButtons"):
    if marker not in s:
        sys.exit("NOT PATCHED: run daynight_switch.py, daynight_first.py and inputs_bar.py first.")

# ---- icons: 24x24 viewport, 1.8 stroke, round caps and joins, white (the bar tints them) ----
def vector(*paths):
    body = "\n".join(paths)
    return f'''<?xml version="1.0" encoding="utf-8"?>
<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="22dp"
    android:height="22dp"
    android:viewportWidth="24"
    android:viewportHeight="24">
{body}
</vector>
'''

def line(d):
    return (f'    <path android:pathData="{d}" android:fillColor="#00000000" android:strokeColor="#FFFFFFFF" '
            f'android:strokeWidth="1.8" android:strokeLineCap="round" android:strokeLineJoin="round"/>')

def solid(d):
    return f'    <path android:pathData="{d}" android:fillColor="#FFFFFFFF"/>'

SCREEN = "M5.6,4.5 H18.4 A2.6,2.6 0 0 1 21,7.1 V13.9 A2.6,2.6 0 0 1 18.4,16.5 H5.6 A2.6,2.6 0 0 1 3,13.9 V7.1 A2.6,2.6 0 0 1 5.6,4.5 Z"
STAND = "M8,20 H16 M12,16.5 V20"

def arc_pts(r, deg):  # wifi arcs are concentric around (12,19)
    dx = r * math.sin(math.radians(deg))
    y = 19 - r * math.cos(math.radians(deg))
    return dx, y

wifi = []
for r in (5.3, 9.5, 13.7):
    dx, y = arc_pts(r, 40)
    wifi.append(f"M{12 - dx:.2f},{y:.2f} A{r},{r} 0 0 1 {12 + dx:.2f},{y:.2f}")

def gear():
    cx = cy = 12
    ro, ri = 9.6, 7.5
    teeth, step = 6, 60
    def pt(deg, r):
        return cx + r * math.cos(math.radians(deg)), cy + r * math.sin(math.radians(deg))
    d = ""
    for i in range(teeth):
        a = i * step
        p = [pt(a - 14, ri), pt(a - 8, ro), pt(a + 8, ro), pt(a + 14, ri)]
        d += ("M" if i == 0 else "") + f"{p[0][0]:.2f},{p[0][1]:.2f} " if i == 0 else ""
        d += f"L{p[1][0]:.2f},{p[1][1]:.2f} L{p[2][0]:.2f},{p[2][1]:.2f} L{p[3][0]:.2f},{p[3][1]:.2f} "
        nxt = pt(a + step - 14, ri)
        d += f"A{ri},{ri} 0 0 1 {nxt[0]:.2f},{nxt[1]:.2f} "
    return d + "Z"

av = []
for x in (6, 12, 18):
    av.append(f"M{x - 2.1},8 a2.1,2.1 0 1,0 4.2,0 a2.1,2.1 0 1,0 -4.2,0")
    av.append(f"M{x},10.1 V19")

icons = {
    "ic_apple_input": vector(line(SCREEN), line(STAND), line("M8.5,10.5 H15 M12.6,8.1 L15,10.5 L12.6,12.9")),
    "ic_apple_av": vector(*[line(p) for p in av]),
    "ic_apple_livetv": vector(line(SCREEN), line(STAND), line("M10.4,8.6 L14.6,10.5 L10.4,12.4 Z")),
    "ic_apple_wifi": vector(*[line(p) for p in wifi],
                            solid("M12,17.4 a1.6,1.6 0 1,0 0.001,0 Z")),
    "ic_apple_gear": vector(line(gear()), line("M12,9.2 a2.8,2.8 0 1,0 0.001,0 Z")),
}
for name, xml in icons.items():
    minidom.parseString(xml)  # must be well-formed

APPLE_ICONS = '''    /** Apple-style line icons for the top bar buttons: Inputs and Settings (Wi-Fi is set in updateWifiLabel). */
    private void applyAppleIcons() {
        ((TextView) btnInputs).setCompoundDrawablesRelativeWithIntrinsicBounds(R.drawable.ic_apple_input, 0, 0, 0);
        if (!launcherSettingsButton && !topMenu) {
            ((TextView) findViewById(R.id.btnSettings))
                    .setCompoundDrawablesRelativeWithIntrinsicBounds(R.drawable.ic_apple_gear, 0, 0, 0);
        }
    }

'''

edits = [
 ("        if (topMenu || !showInputsMenuRow) return;\n",
  "        if (!PER_INPUT_BUTTONS || topMenu || !showInputsMenuRow) return;\n"),
 ("    private final List<View> inputButtons = new ArrayList<>();\n",
  "    /** One button per TV input in the top bar (false: a single Inputs button lists them all in its menu). */\n"
  "    private static final boolean PER_INPUT_BUTTONS = false;\n"
  "    private final List<View> inputButtons = new ArrayList<>();\n"),
 ("        bar.addView(dayNightSwitch, 0, lp);   // always first: everything else follows it\n",
  "        bar.addView(dayNightSwitch, 0, lp);\n"
  "        // The single Inputs button goes first, before the switch; every other button follows.\n"
  "        if (btnInputs.getParent() == bar) {\n"
  "            bar.removeView(btnInputs);\n"
  "            bar.addView(btnInputs, 0);\n"
  "        }\n"
  "        applyAppleIcons();\n"),
 ("    /** config.xml icon_only_buttons. */\n", APPLE_ICONS + "    /** config.xml icon_only_buttons. */\n"),
]
for old, new in edits:
    if s.count(old) != 1:
        sys.exit(f"NOT PATCHED ({s.count(old)} matches, expected 1) for:\n{old.strip().splitlines()[0]}\nSend me this message.")
for old, new in edits:
    s = s.replace(old, new)
for old_name, new_name in (("ic_input", "ic_apple_input"), ("ic_av", "ic_apple_av"), ("ic_livetv", "ic_apple_livetv"),
                           ("ic_wifi", "ic_apple_wifi"), ("ic_settings", "ic_apple_gear")):
    s = re.sub(rf"R\.drawable\.{old_name}\b", f"R.drawable.{new_name}", s)

os.makedirs(drawables, exist_ok=True)
for name, xml in icons.items():
    with open(os.path.join(drawables, name + ".xml"), "w", encoding="utf-8", newline="") as f:
        f.write(xml.replace("\n", "\r\n") if crlf else xml)

backup = os.path.join(os.path.dirname(launcher), ".install-backup", "MainActivity.java.apple.bak")
os.makedirs(os.path.dirname(backup), exist_ok=True)
if not os.path.exists(backup):
    shutil.copy2(path, backup)
open(path, "w", encoding="utf-8", newline="").write(s.replace("\n", "\r\n") if crlf else s)
print("done: one Inputs button first, Apple-style icons. Rebuild: gradlew.bat assembleDebug")
