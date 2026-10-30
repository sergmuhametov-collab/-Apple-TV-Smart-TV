#!/usr/bin/env python3
"""
Apple-style on/off switch in the top bar that flips the backdrop between NIGHT (off, the usual dark background)
and DAY (on, a blue sky gradient). The text stays white on both; the choice is remembered.

Usage:   py daynight_switch.py "C:\\path\\to\\cleanyourtv-main\\launcher"

Adds DayNightSwitch.java and edits MainActivity.java (all or nothing, CRLF kept, backup in <repo>/.install-backup/).
The switch sits just before the Settings button and is reachable with Left/Right like the other buttons.
Run topbar_glass.py first if you want the switch inside the glass capsule (it works without it too).
Running it twice changes nothing. Undo: copy MainActivity.java.daynight.bak back and delete DayNightSwitch.java.
Note: a wallpaper set by a theme is drawn over this backdrop and hides it.
"""
import os, shutil, sys

if len(sys.argv) != 2:
    sys.exit(__doc__)
launcher = os.path.abspath(sys.argv[1])
java = os.path.join(launcher, "app", "src", "main", "java", "com", "gathin", "tvhome")
path = os.path.join(java, "MainActivity.java")
if not os.path.exists(path):
    sys.exit(f"Not found: {path}")

SWITCH_JAVA = r'''package com.gathin.tvhome;

import android.animation.ValueAnimator;
import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.RectF;
import android.view.View;

/**
 * An Apple-style on/off switch for the day (on) and night (off) backdrop: a rounded track and a white knob that
 * slides across it, with a moon on the knob at night and a sun by day.
 */
public class DayNightSwitch extends View {
    private static final int TRACK_NIGHT = 0x40FFFFFF;
    private static final int TRACK_DAY = 0xFFFFC857;
    private static final int INK = 0xFF30404A;

    private final float density;
    private final boolean animate;
    private final Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
    private final RectF rect = new RectF();
    private final Path moon = new Path();
    private final Path bite = new Path();
    private boolean day;
    /** 0 is night, 1 is day. */
    private float progress;
    private ValueAnimator animator;

    public DayNightSwitch(Context context, boolean animate) {
        super(context);
        this.density = getResources().getDisplayMetrics().density;
        this.animate = animate;
        setFocusable(true);
        setClickable(true);
    }

    boolean isDay() {
        return day;
    }

    void setDay(boolean day, boolean animated) {
        this.day = day;
        if (animator != null) animator.cancel();
        float target = day ? 1f : 0f;
        if (!animated || !animate) {
            progress = target;
            invalidate();
            return;
        }
        animator = ValueAnimator.ofFloat(progress, target);
        animator.setDuration(200);
        animator.addUpdateListener(a -> {
            progress = (Float) a.getAnimatedValue();
            invalidate();
        });
        animator.start();
    }

    @Override
    protected void onDetachedFromWindow() {
        if (animator != null) animator.cancel();
        super.onDetachedFromWindow();
    }

    private static int blend(int from, int to, float t) {
        int a = Math.round(Color.alpha(from) + (Color.alpha(to) - Color.alpha(from)) * t);
        int r = Math.round(Color.red(from) + (Color.red(to) - Color.red(from)) * t);
        int g = Math.round(Color.green(from) + (Color.green(to) - Color.green(from)) * t);
        int b = Math.round(Color.blue(from) + (Color.blue(to) - Color.blue(from)) * t);
        return Color.argb(a, r, g, b);
    }

    @Override
    protected void onDraw(Canvas canvas) {
        float d = density;
        float w = 52 * d;
        float h = 30 * d;
        float left = (getWidth() - w) / 2f;
        float top = (getHeight() - h) / 2f;
        rect.set(left, top, left + w, top + h);

        paint.setStyle(Paint.Style.FILL);
        paint.setColor(blend(TRACK_NIGHT, TRACK_DAY, progress));
        canvas.drawRoundRect(rect, h / 2f, h / 2f, paint);
        paint.setStyle(Paint.Style.STROKE);
        paint.setStrokeWidth(Math.max(1f, d));
        paint.setColor(0x33FFFFFF);
        canvas.drawRoundRect(rect, h / 2f, h / 2f, paint);

        float knob = 26 * d;
        float pad = 2 * d;
        float cx = left + pad + knob / 2f + (w - 2 * pad - knob) * progress;
        float cy = top + h / 2f;
        paint.setStyle(Paint.Style.FILL);
        paint.setColor(0x30000000);
        canvas.drawCircle(cx, cy + d, knob / 2f, paint);
        paint.setColor(Color.WHITE);
        canvas.drawCircle(cx, cy, knob / 2f, paint);

        // The moon fades out as the knob moves to day.
        int moonAlpha = Math.round(255 * (1f - progress));
        if (moonAlpha > 0) {
            moon.reset();
            moon.addCircle(cx, cy, 6 * d, Path.Direction.CW);
            bite.reset();
            bite.addCircle(cx + 3.5f * d, cy - 2.5f * d, 5 * d, Path.Direction.CW);
            moon.op(bite, Path.Op.DIFFERENCE);
            paint.setStyle(Paint.Style.FILL);
            paint.setColor(INK);
            paint.setAlpha(moonAlpha);
            canvas.drawPath(moon, paint);
        }
        // The sun fades in.
        int sunAlpha = Math.round(255 * progress);
        if (sunAlpha > 0) {
            paint.setColor(INK);
            paint.setAlpha(sunAlpha);
            paint.setStyle(Paint.Style.FILL);
            canvas.drawCircle(cx, cy, 4 * d, paint);
            paint.setStyle(Paint.Style.STROKE);
            paint.setStrokeWidth(1.5f * d);
            paint.setStrokeCap(Paint.Cap.ROUND);
            for (int i = 0; i < 8; i++) {
                double angle = Math.PI / 4 * i;
                float cos = (float) Math.cos(angle);
                float sin = (float) Math.sin(angle);
                canvas.drawLine(cx + cos * 6.5f * d, cy + sin * 6.5f * d,
                        cx + cos * 9f * d, cy + sin * 9f * d, paint);
            }
            paint.setStrokeCap(Paint.Cap.BUTT);
        }
    }
}
'''

METHODS = r'''    /** Day/night backdrop: night is the configured background, day a blue sky; the text stays white on both. */
    private static final String UI_PREFS = "tvhome_ui";
    private int nightBackground;
    private boolean dayMode;
    private DayNightSwitch dayNightSwitch;

    /** The Apple-style day/night switch in the top bar, just before Settings; the choice is remembered. */
    private void addDayNightToggle() {
        LinearLayout bar = findViewById(R.id.topButtons);
        View settings = findViewById(R.id.btnSettings);
        dayMode = getSharedPreferences(UI_PREFS, MODE_PRIVATE).getBoolean("day_mode", false);
        dayNightSwitch = new DayNightSwitch(this, animations && !reducedMotion);
        dayNightSwitch.setId(View.generateViewId());
        dayNightSwitch.setDay(dayMode, false);
        dayNightSwitch.setContentDescription("Day / night");
        dayNightSwitch.setOnClickListener(v -> {
            dayMode = !dayMode;
            dayNightSwitch.setDay(dayMode, true);
            getSharedPreferences(UI_PREFS, MODE_PRIVATE).edit().putBoolean("day_mode", dayMode).apply();
            applyDayNight(true);
        });
        // The same edge handling as the other pills: Up stays in the bar, Down returns to the tiles.
        dayNightSwitch.setOnKeyListener((v, keyCode, event) -> {
            if (event.getAction() != KeyEvent.ACTION_DOWN) return false;
            if (keyCode == KeyEvent.KEYCODE_DPAD_UP) return true;
            if (keyCode == KeyEvent.KEYCODE_DPAD_DOWN) {
                focusTile(singleRow ? lastFocused : lastFocused % COLUMNS);
                return true;
            }
            return false;
        });
        int height = settings.getLayoutParams().height > 0
                ? settings.getLayoutParams().height : Math.round(42 * density);
        LinearLayout.LayoutParams lp = new LinearLayout.LayoutParams(Math.round(64 * density), height);
        lp.gravity = Gravity.CENTER_VERTICAL;
        bar.addView(dayNightSwitch, bar.indexOfChild(settings), lp);
        applyDayNight(false);
    }

    /** Puts the day or the night backdrop on the root, with a short cross-fade when the switch is flipped. */
    private void applyDayNight(boolean animate) {
        int[] sky = {0xFF3A86BC, 0xFF1B5A87};
        Drawable day = new GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM, sky);
        Drawable night = new ColorDrawable(nightBackground);
        Drawable to = dayMode ? day : night;
        Drawable from = dayMode ? night : day;
        if (animate && animations && !reducedMotion) {
            android.graphics.drawable.TransitionDrawable fade =
                    new android.graphics.drawable.TransitionDrawable(new Drawable[]{from, to});
            root.setBackground(fade);
            fade.startTransition(350);
        } else {
            root.setBackground(to);
        }
    }

'''

s = open(path, encoding="utf-8", newline="").read()
crlf = "\r\n" in s
if crlf:
    s = s.replace("\r\n", "\n")
if "addDayNightToggle" in s:
    print("already applied, nothing to do")
    sys.exit(0)

bg_anchor = "        root.setBackgroundColor(cfg.backgroundColor);\n"
glass_call = "        applyGlassTopBar();\n"
festive_call = "        if (festive) applyFestiveSkin((TextView) btnInputs, (TextView) btnSettings);\n"
method_anchor = "    /** config.xml icon_only_buttons. */\n"
call_anchor = glass_call if s.count(glass_call) == 1 else festive_call

for a in (bg_anchor, call_anchor, method_anchor):
    if s.count(a) != 1:
        sys.exit(f"NOT PATCHED ({s.count(a)} matches, expected 1) for:\n{a}\nSend me this message.")

s = s.replace(bg_anchor, bg_anchor + "        nightBackground = cfg.backgroundColor;\n")
s = s.replace(call_anchor, "        addDayNightToggle();\n" + call_anchor)
s = s.replace(method_anchor, METHODS + method_anchor)

backup = os.path.join(os.path.dirname(launcher), ".install-backup", "MainActivity.java.daynight.bak")
os.makedirs(os.path.dirname(backup), exist_ok=True)
if not os.path.exists(backup):
    shutil.copy2(path, backup)
sw = os.path.join(java, "DayNightSwitch.java")
if not os.path.exists(sw):
    open(sw, "w", encoding="utf-8", newline="").write(SWITCH_JAVA.replace("\n", "\r\n") if crlf else SWITCH_JAVA)
open(path, "w", encoding="utf-8", newline="").write(s.replace("\n", "\r\n") if crlf else s)
print("done: day/night switch added. Rebuild: gradlew.bat assembleDebug")
