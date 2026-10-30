#!/usr/bin/env python3
"""
The TV's own inputs as glass buttons at the START of the top bar (before the day/night switch).

The launcher asks the TV which inputs it has (HDMI ports, AV) and adds one button per input, in the same glass
style: an input icon, and for HDMI the port number. A button looks dimmer while nothing is plugged into that
port. OK on a button switches the TV to that input (an HDMI-CEC device on the port is woken up). The number of
buttons follows the TV: two HDMI ports give two buttons, and they appear or disappear when the TV reports a change.
Inputs the TV hides in its own settings, and ports left out with input_sources ("HW8=-"), are not shown.

Usage:   py inputs_bar.py "C:\\path\\to\\cleanyourtv-main\\launcher"

Needs daynight_switch.py and daynight_first.py applied first. All or nothing, CRLF kept,
backup in <repo>/.install-backup/MainActivity.java.inputs.bak. Running it twice changes nothing.
USB is not a TV input on Android TV, so it is not detected here (see the note in my message).
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
if "updateInputButtons" in s:
    print("already applied, nothing to do")
    sys.exit(0)
if "bar.addView(dayNightSwitch, 0, lp);" not in s:
    sys.exit("NOT PATCHED: run daynight_switch.py and then daynight_first.py first.")

METHODS = r'''    /** The TV's own inputs (HDMI ports, AV) as buttons at the start of the top bar, one per input the TV reports. */
    private final List<View> inputButtons = new ArrayList<>();
    private String inputButtonsKey = "";

    /** Up stays in the bar, Down returns to the tiles, and the first button has nothing on its start side. */
    private final View.OnKeyListener barKeys = (v, keyCode, event) -> {
        if (event.getAction() != KeyEvent.ACTION_DOWN) return false;
        if (keyCode == KeyEvent.KEYCODE_DPAD_UP) return true;
        if (keyCode == KeyEvent.KEYCODE_DPAD_DOWN) {
            focusTile(singleRow ? lastFocused : lastFocused % COLUMNS);
            return true;
        }
        int startKey = getResources().getBoolean(R.bool.rtl_menu_bar)
                ? KeyEvent.KEYCODE_DPAD_RIGHT : KeyEvent.KEYCODE_DPAD_LEFT;
        return keyCode == startKey && v == firstBarButton();
    };

    /** The first shown, focusable button of the top bar, or null. */
    private View firstBarButton() {
        LinearLayout bar = findViewById(R.id.topButtons);
        for (int i = 0; i < bar.getChildCount(); i++) {
            View child = bar.getChildAt(i);
            if (child.getVisibility() == View.VISIBLE && child.isFocusable()) return child;
        }
        return null;
    }

    /** Glass look for a top-bar button: clear until focused, then a lighter capsule with white ink. */
    private void styleGlassButton(TextView button, ColorStateList ink) {
        float round = 100 * density;
        GradientDrawable lit = new GradientDrawable();
        lit.setColor(0x4DFFFFFF);
        lit.setCornerRadius(round);
        GradientDrawable clear = new GradientDrawable();
        clear.setColor(Color.TRANSPARENT);
        clear.setCornerRadius(round);
        android.graphics.drawable.StateListDrawable background = new android.graphics.drawable.StateListDrawable();
        background.addState(new int[]{android.R.attr.state_focused}, lit);
        background.addState(new int[]{android.R.attr.state_activated}, lit);
        background.addState(new int[0], clear);
        button.setBackground(background);
        button.setTextColor(ink);
        button.setCompoundDrawableTintList(ink);
    }

    /** Rebuilds the input buttons when the TV inputs, or whether something is plugged into one, change. */
    private void updateInputButtons() {
        if (topMenu || !showInputsMenuRow) return;
        LinearLayout bar = findViewById(R.id.topButtons);
        TvInputManager tim = (TvInputManager) getSystemService(TV_INPUT_SERVICE);
        if (bar == null || tim == null) return;
        for (View old : inputButtons) {
            if (old.hasFocus()) return;   // not while one is focused: the focus would be lost
        }
        List<TvInputInfo> all = tim.getTvInputList();
        Set<String> ids = new HashSet<>();
        for (TvInputInfo info : all) ids.add(info.getId());
        // An HDMI-CEC device answers on a port: that port opens the device, which also wakes it.
        Map<String, String> deviceOnPort = new HashMap<>();
        for (TvInputInfo info : all) {
            String parent = info.getParentId();
            if (parent != null && ids.contains(parent) && info.isPassthroughInput() && !info.isHidden(this)) {
                deviceOnPort.put(parent, info.getId());
            }
        }
        List<TvInputInfo> ports = new ArrayList<>();
        for (TvInputInfo info : all) {
            if (!info.isPassthroughInput() || info.isHidden(this)) continue;
            if (Integer.valueOf(-1).equals(mappedSource(info.getId()))) continue;
            if (info.getParentId() != null && ids.contains(info.getParentId())) continue;
            ports.add(info);
        }
        Collections.sort(ports, (a, b) -> {
            boolean ha = a.getType() == TvInputInfo.TYPE_HDMI;
            boolean hb = b.getType() == TvInputInfo.TYPE_HDMI;
            if (ha != hb) return ha ? -1 : 1;
            return String.valueOf(a.loadLabel(this)).compareToIgnoreCase(String.valueOf(b.loadLabel(this)));
        });
        StringBuilder key = new StringBuilder();
        for (TvInputInfo port : ports) {
            key.append(port.getId()).append(':').append(tim.getInputState(port.getId())).append(';');
        }
        if (key.toString().equals(inputButtonsKey)) return;
        inputButtonsKey = key.toString();

        for (View old : inputButtons) bar.removeView(old);
        inputButtons.clear();
        View settings = findViewById(R.id.btnSettings);
        int height = settings.getLayoutParams().height > 0
                ? settings.getLayoutParams().height : Math.round(42 * density);
        int half = Math.round(1 * density);
        int index = 0;
        for (TvInputInfo port : ports) {
            boolean hdmi = port.getType() == TvInputInfo.TYPE_HDMI;
            CharSequence label = port.loadLabel(this);
            String name = label == null ? port.getId() : label.toString();
            java.util.regex.Matcher digits = java.util.regex.Pattern.compile("(\\d+)").matcher(name);
            String number = hdmi && digits.find() ? digits.group(1) : "";
            boolean unplugged = tim.getInputState(port.getId()) == TvInputManager.INPUT_STATE_DISCONNECTED;
            final String target = deviceOnPort.containsKey(port.getId())
                    ? deviceOnPort.get(port.getId()) : port.getId();

            TextView button = (TextView) getLayoutInflater().inflate(R.layout.top_app_button, bar, false);
            button.setId(View.generateViewId());
            Drawable icon = getDrawable(hdmi ? R.drawable.ic_input : R.drawable.ic_av).mutate();
            int size = Math.round(22 * density);
            icon.setBounds(0, 0, size, size);
            button.setCompoundDrawablesRelative(icon, null, null, null);
            button.setCompoundDrawablePadding(number.isEmpty() ? 0 : Math.round(4 * density));
            button.setText(number);
            button.setGravity(Gravity.CENTER);
            button.setMinWidth(Math.round(42 * density));
            int side = Math.round(10 * density);
            button.setPaddingRelative(side, 0, side, 0);
            button.setContentDescription(name);
            ColorStateList ink = new ColorStateList(
                    new int[][]{new int[]{android.R.attr.state_focused}, new int[0]},
                    new int[]{0xFFFFFFFF, unplugged ? 0x66FFFFFF : 0xCCFFFFFF});
            styleGlassButton(button, ink);
            button.setOnKeyListener(barKeys);
            button.setOnClickListener(v -> openInput(target));
            LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(ViewGroup.LayoutParams.WRAP_CONTENT, height);
            lp.gravity = Gravity.CENTER_VERTICAL;
            lp.setMargins(half, 0, half, 0);
            bar.addView(button, index++, lp);
            inputButtons.add(button);
        }
    }

'''

old_toggle_keys = """        dayNightSwitch.setOnKeyListener((v, keyCode, event) -> {
            if (event.getAction() != KeyEvent.ACTION_DOWN) return false;
            if (keyCode == KeyEvent.KEYCODE_DPAD_UP) return true;
            if (keyCode == KeyEvent.KEYCODE_DPAD_DOWN) {
                focusTile(singleRow ? lastFocused : lastFocused % COLUMNS);
                return true;
            }
            // The switch is the first button: Left (Right in a right-to-left bar) has nowhere to go.
            return keyCode == (getResources().getBoolean(R.bool.rtl_menu_bar)
                    ? KeyEvent.KEYCODE_DPAD_RIGHT : KeyEvent.KEYCODE_DPAD_LEFT);
        });
"""
edits = [
 (old_toggle_keys, "        dayNightSwitch.setOnKeyListener(barKeys);\n"),
 ("""            int firstButton = dayNightSwitch != null ? dayNightSwitch.getId()
                    : btnInputs.getVisibility() == View.VISIBLE ? R.id.btnInputs : firstTopButton().getId();
""",
  """            View firstShown = firstBarButton();
            int firstButton = firstShown != null ? firstShown.getId()
                    : btnInputs.getVisibility() == View.VISIBLE ? R.id.btnInputs : firstTopButton().getId();
"""),
 ("    private void updateInputsButton() {\n",
  "    private void updateInputsButton() {\n        updateInputButtons();\n"),
 ("""        public void onInputRemoved(String inputId) {
            updateInputsButton();
        }
""",
  """        public void onInputRemoved(String inputId) {
            updateInputsButton();
        }

        @Override
        public void onInputStateChanged(String inputId, int state) {
            updateInputButtons();
        }
"""),
 ("    /** config.xml icon_only_buttons. */\n", METHODS + "    /** config.xml icon_only_buttons. */\n"),
]
for old, new in edits:
    if s.count(old) != 1:
        sys.exit(f"NOT PATCHED ({s.count(old)} matches, expected 1) for:\n{old.strip().splitlines()[0]}\nSend me this message.")
for old, new in edits:
    s = s.replace(old, new)

backup = os.path.join(os.path.dirname(launcher), ".install-backup", "MainActivity.java.inputs.bak")
os.makedirs(os.path.dirname(backup), exist_ok=True)
if not os.path.exists(backup):
    shutil.copy2(path, backup)
open(path, "w", encoding="utf-8", newline="").write(s.replace("\n", "\r\n") if crlf else s)
print("done: TV input buttons at the start of the top bar. Rebuild: gradlew.bat assembleDebug")
