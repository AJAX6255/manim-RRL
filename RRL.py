from manim import *
import numpy as np

class RRLyraeLightCurve(Scene):
    def construct(self):
        # Title
        title = Title("RR Lyrae Stars — RRab Type Light Curve")
        self.play(Write(title))
        self.wait(0.5)

        # Physical context
        formula = MathTex(
            r"M_V = \alpha\,[\text{Fe}/\text{H}] + \beta",
            font_size=36
        ).next_to(title, DOWN, buff=0.6)
        subtitle = Text("Period-Luminosity-Metallicity Relation", font_size=28, color=BLUE)
        subtitle.next_to(formula, DOWN, buff=0.3)

        self.play(Write(formula), Write(subtitle))
        self.wait(1)

        # === Axes Setup ===
        axes = Axes(
            x_range=[0, 1.05, 0.2],      # Phase
            y_range=[14.5, 16.5, 0.5],   # Apparent Magnitude (smaller = brighter)
            x_length=9,
            y_length=5.5,
            axis_config={"include_numbers": True, "font_size": 24},
            x_axis_config={"label": "Phase"},
            y_axis_config={"label": "Magnitude"},
        ).shift(DOWN * 0.8)

        # Invert y-axis visually (brighter = higher on screen)
        axes.y_axis.label.rotate(90 * DEGREES).shift(LEFT * 0.5)

        phase_label = axes.get_x_axis_label("Phase \\phi")
        mag_label = axes.get_y_axis_label("Apparent\\ Magnitude", direction=LEFT)

        self.play(Create(axes), Write(phase_label), Write(mag_label))
        self.wait(0.8)

        # === Better RRab Light Curve Model ===
        # Realistic asymmetric sawtooth: fast rise, slow decline
        def rr_ab_light_curve(phi):
            # Combination of Fourier terms for typical RRab shape
            return (
                15.5 
                - 0.65 * np.sin(2 * np.pi * phi) 
                - 0.25 * np.sin(4 * np.pi * phi + 0.3)
                - 0.12 * np.sin(6 * np.pi * phi + 0.6)
                + 0.08 * np.sin(8 * np.pi * phi)  # extra sharpness
            )

        curve = axes.plot(
            rr_ab_light_curve,
            x_range=[0, 1],
            color=YELLOW,
            stroke_width=5
        )

        curve_label = Text("Typical RRab Light Curve", color=YELLOW, font_size=32)
        curve_label.next_to(curve, UP, buff=0.4)

        # Animate the curve drawing
        self.play(
            Create(curve, rate_func=linear),
            Write(curve_label),
            run_time=4
        )
        self.wait(1)

        # === Add a moving point (pulsating star) ===
        dot = Dot(color=RED, radius=0.12)
        dot.move_to(axes.i2gp(0, curve))   # initial position

        self.play(FadeIn(dot))
        self.wait(0.5)

        # Animate one full cycle
        self.play(
            MoveAlongPath(
                dot,
                curve,
                rate_func=linear
            ),
            run_time=6,
            rate_func=linear
        )

        # Add annotations
        rise_arrow = Arrow(
            start=axes.c2p(0.85, 16.1),
            end=axes.c2p(0.05, 14.7),
            color=ORANGE,
            buff=0.1
        )
        rise_text = Text("Rapid rise\n(contraction)", color=ORANGE, font_size=20).next_to(rise_arrow, DOWN)

        decline_arrow = Arrow(
            start=axes.c2p(0.15, 14.8),
            end=axes.c2p(0.85, 16.2),
            color=BLUE,
            buff=0.1
        )
        decline_text = Text("Slow decline\n(expansion)", color=BLUE, font_size=20).next_to(decline_arrow, UP)

        self.play(Create(rise_arrow), Write(rise_text))
        self.play(Create(decline_arrow), Write(decline_text))
        self.wait(2)

        # Final note
        note = Text(
            "RRab stars show asymmetric sawtooth light curves",
            font_size=28,
            color=GREEN
        ).to_edge(DOWN)
        self.play(Write(note))
        self.wait(3)