from logging import config
import os
import numpy as np
# pyrefly: ignore [missing-import]
# Explicit imports - this makes your IDE much happier
from manim import (
    Scene, Circle, Axes, Text, Dot, Arrow, VGroup, Rectangle,
    RoundedRectangle, ManimColor,
    ValueTracker, DecimalNumber, Integer,
    Create, Write, FadeIn, linear,
    config, LEFT, RIGHT, DOWN, UP, ORIGIN, TAU, WHITE,
    interpolate_color
)

# Optional but very useful
# pyrefly: ignore [missing-import]
from manim.utils.color import interpolate_color

config.background_color = "#0B0C10"

# ==================== PARAMETERS FROM FASTAPI ====================
PERIOD = float(os.environ.get("RRL_PERIOD", 0.6))
METALLICITY = float(os.environ.get("RRL_METALLICITY", -1.5))
AMPLITUDE = float(os.environ.get("RRL_AMPLITUDE", 0.8))
MODE = os.environ.get("RRL_MODE", "RRab")
DISTANCE = float(os.environ.get("RRL_DISTANCE", 1000))

# Improved PLZ relation
if MODE == "RRab":
    M_V = 0.84 - 1.35 * np.log10(PERIOD) + 0.20 * METALLICITY
else:
    M_V = 0.65 - 1.35 * np.log10(PERIOD) + 0.20 * METALLICITY

m_V = M_V + 5 * np.log10(DISTANCE) - 5


def lc_func(x):
    phase = x % 1.0
    if MODE == "RRab":
        val = (0.58 * np.sin(2*np.pi*phase - np.pi/2) +
               0.26 * np.sin(4*np.pi*phase - 2.6) +
               0.11 * np.sin(6*np.pi*phase - 3.8))
    else:
        val = 0.48 * np.sin(2*np.pi*phase - np.pi/2)
    return m_V - val * AMPLITUDE


def rv_func(x):
    phase = x % 1.0
    if MODE == "RRab":
        val = (0.52 * np.sin(2*np.pi*phase - 0.3) +
               0.20 * np.sin(4*np.pi*phase - 1.4) +
               0.08 * np.sin(6*np.pi*phase - 2.4))
    else:
        val = 0.47 * np.sin(2*np.pi*phase - 0.3)
    return val * (35 if MODE == "RRab" else 18)


class RRStarPulsation(Scene):
    def construct(self):
        # Title and Info
        title = Text("RR Lyrae Variable Star Pulsation", font_size=28, color="#66FCF1")
        title.to_edge(UP, buff=0.5)

        mode_text = "RRab (Fundamental)" if MODE == "RRab" else "RRc (First Overtone)"
        info = f"Period: {PERIOD:.2f} d    [Fe/H]: {METALLICITY:.2f}    {mode_text}\n" \
               f"Distance: {DISTANCE:.0f} pc    M_V: {M_V:.2f}    m_V: {m_V:.2f}"

        info_label = Text(info, font_size=16, color="#C5C6C7", line_spacing=1.1)
        info_label.next_to(title, DOWN, buff=0.3)

        self.play(Write(title), Write(info_label))
        self.wait(0.8)

        # Layout
        left = LEFT * 3.6
        right = RIGHT * 2.7

        # ===================== LIGHT CURVE =====================
        lc_axes = Axes(
            x_range=[0, 2.0, 0.5],
            y_range=[m_V + AMPLITUDE * 1.15, m_V - AMPLITUDE * 1.15, 0.2],
            x_length=5.3,
            y_length=2.5,
            axis_config={"color": "#45A29E", "stroke_width": 2},
        ).move_to(right + UP * 1.05)

        lc_title = Text("V-band Light Curve", font_size=18, color="#66FCF1").next_to(lc_axes, UP, buff=0.2)
        self.play(Create(lc_axes), Write(lc_title))

        lc_curve = lc_axes.plot(lc_func, x_range=[0, 2], color="#FF007F", stroke_width=4.5)
        self.play(Create(lc_curve))

        # ===================== RADIAL VELOCITY =====================
        rv_axes = Axes(
            x_range=[0, 2.0, 0.5],
            y_range=[-45, 45, 15],
            x_length=5.3,
            y_length=2.4,
            axis_config={"color": "#45A29E", "stroke_width": 2},
        ).move_to(right + DOWN * 1.65)

        rv_title = Text("Radial Velocity (km/s)", font_size=18, color="#66FCF1").next_to(rv_axes, UP, buff=0.2)
        self.play(Create(rv_axes), Write(rv_title))

        rv_curve = rv_axes.plot(rv_func, x_range=[0, 2], color="#00E5FF", stroke_width=4)
        self.play(Create(rv_curve))

        # ===================== STAR + STATE BOX =====================
        star = Circle(radius=1.45, fill_opacity=0.95, stroke_color=WHITE, stroke_width=3)
        star.move_to(left)

        self.play(FadeIn(star, scale=0.6))

        # State Information Box
        state_box = RoundedRectangle(width=3.4, height=2.1, fill_color="#1F2833", fill_opacity=0.75,
                                     stroke_color="#45A29E", stroke_width=2, corner_radius=0.1)
        state_box.next_to(star, DOWN, buff=0.6)

        labels = VGroup(
            Text("Phase:", font_size=14, color="#C5C6C7"),
            Text("Rel. Radius:", font_size=14, color="#C5C6C7"),
            Text("T_eff:", font_size=14, color="#C5C6C7"),
            Text("Velocity:", font_size=14, color="#C5C6C7")
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to(state_box.get_center() + LEFT*0.9)

        # Dynamic values
        val_phase = DecimalNumber(0.000, num_decimal_places=3, font_size=14, color="#66FCF1", mob_class=Text)
        val_radius = DecimalNumber(1.00, num_decimal_places=2, font_size=14, color="#66FCF1", mob_class=Text)
        val_teff = Integer(6000, font_size=14, color="#66FCF1", mob_class=Text)
        val_vel = DecimalNumber(0.0, num_decimal_places=1, include_sign=True, font_size=14, color="#66FCF1", mob_class=Text)

        suffixes = VGroup(
            Text("", font_size=14, color="#C5C6C7"),
            Text(" R☉", font_size=14, color="#C5C6C7"),
            Text(" K", font_size=14, color="#C5C6C7"),
            Text(" km/s", font_size=14, color="#C5C6C7")
        )

        for i, (val, suf) in enumerate(zip([val_phase, val_radius, val_teff, val_vel], suffixes)):
            val.next_to(labels[i], RIGHT, buff=0.6)
            suf.next_to(val, RIGHT, buff=0.1)

        self.play(FadeIn(state_box), Write(labels), Write(VGroup(val_phase, val_radius, val_teff, val_vel, *suffixes)))

        phase_tracker = ValueTracker(0.0)

        # Pre-create arrows
        arrows = VGroup(*[Arrow(ORIGIN, ORIGIN, buff=0, stroke_width=3) for _ in range(8)])
        arrows.move_to(left)
        self.add(arrows)

        # Dots
        lc_dot = Dot(color="#FF1493", radius=0.12)
        rv_dot = Dot(color="#00FFFF", radius=0.12)
        self.add(lc_dot, rv_dot)

        # Updaters
        star.add_updater(lambda s: self.update_star(s, phase_tracker.get_value()))
        arrows.add_updater(lambda a: self.update_arrows(a, phase_tracker.get_value(), star))
        lc_dot.add_updater(lambda d: d.move_to(lc_axes.c2p(phase_tracker.get_value(), lc_func(phase_tracker.get_value()))))
        rv_dot.add_updater(lambda d: d.move_to(rv_axes.c2p(phase_tracker.get_value(), rv_func(phase_tracker.get_value()))))

        # Value updaters
        val_phase.add_updater(lambda m: m.set_value(phase_tracker.get_value() % 1.0))
        val_radius.add_updater(lambda m: m.set_value(star.get_width() / (2 * 1.45)))  # normalized to base radius
        val_teff.add_updater(lambda m: m.set_value(int(5800 + 1800 * ((lc_func(phase_tracker.get_value()) - m_V) / (-AMPLITUDE)))))
        val_vel.add_updater(lambda m: m.set_value(rv_func(phase_tracker.get_value())))

        # ===================== ANIMATION =====================
        self.play(
            phase_tracker.animate.set_value(2.0),
            run_time=10,
            rate_func=linear
        )

        self.wait(1.5)

    # ===================== HELPER UPDATERS =====================
    def update_star(self, star_mob, phase):
        # Radius
        if MODE == "RRab":
            rad_factor = 1.0 + 0.18 * AMPLITUDE * np.cos(2 * np.pi * phase - 2.4)
        else:
            rad_factor = 1.0 + 0.13 * AMPLITUDE * np.cos(2 * np.pi * phase - 2.4)

        star_mob.set_width(2.9 * rad_factor)

        # Color (Temperature)
        brightness = np.clip((lc_func(phase) - m_V) / (-AMPLITUDE), 0, 1)
        color = interpolate_color(ManimColor("#FF8C42"), ManimColor("#A0E8FF"), brightness)
        star_mob.set_fill(color)

    def update_arrows(self, arrows_group, phase, star_mob):
        curr_vel = rv_func(phase)
        rad = star_mob.get_width() / 2
        vel_mag = abs(curr_vel)
        arrow_len = 0.25 + vel_mag * 0.012

        arrows_group.submobjects.clear()

        for i in range(8):
            angle = i * TAU / 8
            direction = np.array([np.cos(angle), np.sin(angle), 0])

            if curr_vel < 0:   # Expanding
                start = LEFT*3.6 + direction * (rad - 0.15)
                end = LEFT*3.6 + direction * (rad + arrow_len)
                color = "#00FFFF"
            else:              # Contracting
                start = LEFT*3.6 + direction * (rad + arrow_len)
                end = LEFT*3.6 + direction * (rad - 0.15)
                color = "#FF4444"

            arrow = Arrow(start, end, color=color, stroke_width=2.5 + vel_mag*0.08, buff=0)
            arrows_group.add(arrow)