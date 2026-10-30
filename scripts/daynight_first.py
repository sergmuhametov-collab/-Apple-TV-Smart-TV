#!/usr/bin/env python3
"""
Moves the day/night switch to the FRONT of the top bar: it is always first, and every other button (Inputs,
extra apps, Wi-Fi, Settings ...) follows it, whichever of them exist.

Usage:   py daynight_first.py "C:\\path\\to\\cleanyourtv-main\\launcher"

Also fixes the remote's Left/Right at the bar's ends, so the switch can be reached from the next button and Left
on the switch itself does nothing (the focus no longer jumps elsewhere).
Needs daynight_switch.py applied first. All or nothing, CRLF kept, backup in <repo>/.install-backup/.
"""
import os, shutil, sys

if len(sys.argv) != 2:
    sys.exit(__doc__)
launcher = os.path.abspath(sys.argv[1])
path = os.path.join(launcher, "app", "src", "main", "java", "com", "gathin", "tvhome", "MainActivity.java")
if not os.path.exists(path):
    sys.exit(f"Not found: {path}")
s = open(path, encoding="utf-8", newline="").read()
crlf = "\r\n" in s
if crlf:
    s = s.replace("\r\n", "\n")
if "bar.addView(dayNightSwitch, 0, lp);" in s:
    print("already applied, nothing to do")
    sys.exit(0)
if "addDayNightToggle" not in s:
    sys.exit("NOT PATCHED: run daynight_switch.py first (addDayNightToggle not found).")

edits = [
("        bar.addView(dayNightSwitch, bar.indexOfChild(settings), lp);\n",
 "        bar.addView(dayNightSwitch, 0, lp);   // always first: everything else follows it\n"),
("""            return false;
        });
        int height = settings.getLayoutParams().height > 0
""",
"""            // The switch is the first button: Left (Right in a right-to-left bar) has nowhere to go.
            return keyCode == (getResources().getBoolean(R.bool.rtl_menu_bar)
                    ? KeyEvent.KEYCODE_DPAD_RIGHT : KeyEvent.KEYCODE_DPAD_LEFT);
        });
        int height = settings.getLayoutParams().height > 0
"""),
("            int firstButton = btnInputs.getVisibility() == View.VISIBLE ? R.id.btnInputs : firstTopButton().getId();\n",
 """            int firstButton = dayNightSwitch != null ? dayNightSwitch.getId()
                    : btnInputs.getVisibility() == View.VISIBLE ? R.id.btnInputs : firstTopButton().getId();
"""),
]
for old, new in edits:
    if s.count(old) != 1:
        sys.exit(f"NOT PATCHED ({s.count(old)} matches, expected 1) for:\n{old}\nSend me this message.")
for old, new in edits:
    s = s.replace(old, new)

backup = os.path.join(os.path.dirname(launcher), ".install-backup", "MainActivity.java.first.bak")
os.makedirs(os.path.dirname(backup), exist_ok=True)
if not os.path.exists(backup):
    shutil.copy2(path, backup)
open(path, "w", encoding="utf-8", newline="").write(s.replace("\n", "\r\n") if crlf else s)
print("done: the day/night switch is now first. Rebuild: gradlew.bat assembleDebug")
