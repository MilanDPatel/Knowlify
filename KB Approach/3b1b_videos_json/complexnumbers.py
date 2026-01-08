#!/usr/bin/env python

from manim import *
import numpy as np
import itertools as it
from copy import deepcopy
from functools import reduce
import operator as op

DEFAULT_PLANE_CONFIG = {
    "stroke_width": 2
}


# MASTER CLASS - Run all scenes in sequence
class CompleteComplexNumberVideo(Scene):
    def construct(self):
        # Scene 1: Successive multiplications (1+2i) * (1-2i)
        self.show_title("Successive Complex Multiplications")
        self.successive_multiplications(complex(1, 2), complex(1, -2))
        self.clear_scene()
        
        # Scene 2: Another multiplication (-2+i) * (-2-i)
        self.show_title("More Multiplications")
        self.successive_multiplications(complex(-2, 1), complex(-2, -1))
        self.clear_scene()
        
        # Scene 3: Complex power i^2
        self.show_title("Powers of i")
        self.show_complex_power(complex(0, 1), 2)
        self.clear_scene()
        
        # Scene 4: Fifth roots of unity
        self.show_title("Fifth Roots of Unity")
        self.show_complex_power(np.exp(1j * 2 * np.pi / 5), 5)
        self.clear_scene()
        
        # Scene 5: Complex power (1 + sqrt(3)i)^3
        self.show_title("Cube of Complex Number")
        self.show_complex_power(complex(1, np.sqrt(3)), 3)
        self.clear_scene()
        
        # Scene 6: Complex division
        self.show_title("Complex Division")
        self.complex_division(complex(1, 2))
        self.clear_scene()
        
        # Scene 7: Conjugate division
        self.show_title("Division by Conjugate")
        self.conjugate_division(complex(1, 2))
        self.clear_scene()
        
        # Scene 8: Solutions to z^5 = 1
        self.show_title("Fifth Roots of Unity (Geometric)")
        self.draw_solutions_to_power(5, complex(1, 0))
        self.clear_scene()
        
        # Scene 9: Angle and magnitude visualization
        self.show_title("Complex Number Geometry")
        self.draw_angle_and_magnitude(("1+i\\sqrt{3}", complex(1, np.sqrt(3))))
        self.clear_scene()
        
        # Final title
        end_title = Text("Complex Numbers: A Visual Journey", font_size=48)
        self.play(Write(end_title))
        self.wait(3)
    
    def show_title(self, title_text):
        title = Text(title_text, font_size=36)
        self.play(Write(title))
        self.wait(1)
        self.play(FadeOut(title))
    
    def clear_scene(self):
        self.play(*[FadeOut(mob) for mob in self.mobjects], run_time=0.5)
        self.wait(0.5)
    
    def setup_plane(self, **plane_config):
        config = {
            "x_range": [-10, 10, 1],
            "y_range": [-10, 10, 1],
            "background_line_style": {
                "stroke_color": BLUE_D,
                "stroke_width": 2,
                "stroke_opacity": 0.5,
            }
        }
        config.update(plane_config)
        plane = ComplexPlane(**config)
        self.add(plane)
        return plane
    
    def draw_dot(self, label_text, complex_num, plane, show=True):
        point = plane.n2p(complex_num)
        dot = Dot(point, color=YELLOW, radius=0.08)
        label = MathTex(label_text).scale(0.7)
        label.next_to(dot, UR, buff=0.1)
        
        if show:
            self.play(Create(dot), Write(label))
        else:
            self.add(dot, label)
        
        return Group(dot, label)
    
    def successive_multiplications(self, *multipliers):
        norm = abs(reduce(op.mul, multipliers, 1))
        shrink_factor = 7 / max(7, norm)
        
        plane_config = {
            "x_range": [-10*shrink_factor, 10*shrink_factor, 1],
            "y_range": [-10*shrink_factor, 10*shrink_factor, 1],
        }
        
        plane = self.setup_plane(**plane_config)
        
        # Draw the initial point at 1
        one_dot = self.draw_dot("1", 1, plane, True)
        
        # Draw all multiplier dots
        for idx, multiplier in enumerate(multipliers):
            if idx == 0:
                tex = "z"
            elif np.conj(multiplier) == multipliers[0]:
                tex = "\\bar{z}"
            else:
                tex = f"z_{{{idx}}}"
            self.draw_dot(tex, multiplier, plane)
        
        self.wait()
        
        # Apply successive multiplications
        for multiplier in multipliers:
            all_mobs = Group(*[m for m in self.mobjects if m != plane])
            
            self.play(
                all_mobs.animate.apply_complex_function(lambda z: z * multiplier),
                run_time=2
            )
            self.wait(0.5)
    
    def show_complex_power(self, multiplier, num_repeats):
        norm = abs(multiplier ** num_repeats)
        shrink_factor = 7 / max(7, norm)
        
        plane_config = {
            "x_range": [-10*shrink_factor, 10*shrink_factor, 1],
            "y_range": [-10*shrink_factor, 10*shrink_factor, 1],
        }
        
        plane = self.setup_plane(**plane_config)
        
        # Show the exponentiation
        title = MathTex(f"z^{{{num_repeats}}}").to_edge(UP)
        self.play(Write(title))
        
        one_dot = self.draw_dot("1", 1, plane, True)
        z_dot = self.draw_dot("z", multiplier, plane, True)
        
        self.wait()
        
        # Apply the multiplication num_repeats times
        for i in range(num_repeats):
            all_mobs = Group(*[m for m in self.mobjects if m != plane and m != title])
            
            self.play(
                all_mobs.animate.apply_complex_function(lambda z: z * multiplier),
                run_time=1.5
            )
            self.wait(0.3)
        
        self.wait(2)
    
    def complex_division(self, num):
        plane = self.setup_plane()
        
        title = MathTex("\\text{Division by } z").to_edge(UP)
        self.play(Write(title))
        
        self.draw_dot("1", 1, plane, True)
        self.draw_dot("z", num, plane, True)
        
        self.wait()
        
        # Division is multiplication by 1/num
        divisor = 1 / num
        all_mobs = Group(*[m for m in self.mobjects if m != plane and m != title])
        
        self.play(
            all_mobs.animate.apply_complex_function(lambda z: z * divisor),
            run_time=2
        )
        
        self.wait(2)
    
    def conjugate_division(self, num):
        plane = self.setup_plane()
        
        title = MathTex("\\text{Division using conjugate}").to_edge(UP)
        self.play(Write(title))
        
        self.draw_dot("1", 1, plane, True)
        self.draw_dot("\\bar{z}", np.conj(num), plane, True)
        
        self.wait()
        
        # First multiply by conjugate
        all_mobs = Group(*[m for m in self.mobjects if m != plane and m != title])
        
        self.play(
            all_mobs.animate.apply_complex_function(lambda z: z * np.conj(num)),
            run_time=2
        )
        
        self.wait(0.5)
        
        # Then scale by 1/|z|^2
        scale = 1 / (abs(num) ** 2)
        all_mobs = Group(*[m for m in self.mobjects if m != plane and m != title])
        
        self.play(
            all_mobs.animate.scale(scale),
            run_time=2
        )
        
        self.wait(2)
    
    def draw_solutions_to_power(self, n, w):
        w = complex(w)
        
        plane = ComplexPlane(
            x_range=[-3, 3, 1],
            y_range=[-3, 3, 1],
        )
        self.add(plane)
        
        # Calculate solutions
        theta = np.angle(w)
        radius = abs(w) ** (1 / n)
        
        solutions = [
            radius * np.exp(1j * (2 * np.pi * k + theta) / n)
            for k in range(n)
        ]
        
        # Draw circle
        circle = Circle(radius=radius, color=BLUE, stroke_width=2)
        self.play(Create(circle))
        
        # Draw solution points
        dots = []
        for sol in solutions:
            point = plane.n2p(sol)
            dot = Dot(point, color=YELLOW, radius=0.08)
            dots.append(dot)
            self.play(Create(dot), run_time=0.3)
        
        # Draw connecting lines
        points = [plane.n2p(sol) for sol in solutions]
        lines = [Line(points[i], points[(i+1) % n], color=GREEN) for i in range(n)]
        
        for line in lines:
            self.play(Create(line), run_time=0.3)
        
        # Add title
        title = MathTex(f"z^{{{n}}} = {w:.2f}").to_edge(UP)
        self.play(Write(title))
        
        self.wait(2)
    
    def draw_angle_and_magnitude(self, rep_and_num):
        plane = ComplexPlane(
            x_range=[-5, 5, 1],
            y_range=[-5, 5, 1],
        )
        self.add(plane)
        
        rep, num = rep_and_num
        point = plane.n2p(num)
        
        # Draw dot
        dot = Dot(point, color=YELLOW, radius=0.08)
        label = MathTex(rep).scale(0.7)
        label.next_to(dot, UR if point[0] > 0 else UL, buff=0.1)
        
        self.play(Create(dot), Write(label))
        
        # Draw lines from origin
        x_line = Line(ORIGIN, point[0] * RIGHT, color=BLUE)
        y_line = Line(point[0] * RIGHT, point, color=GOLD)
        num_line = Line(ORIGIN, point, color=WHITE, stroke_width=3)
        
        self.play(Create(x_line), Create(y_line), Create(num_line))
        
        # Draw angle arc
        angle = np.angle(num)
        if angle != 0:
            arc = Arc(radius=0.5, angle=angle, color=RED)
            self.play(Create(arc))
        
        # Add magnitude label
        magnitude = abs(num)
        mag_label = MathTex(f"|z| = {magnitude:.2f}").scale(0.6)
        mag_label.next_to(num_line.get_center(), 
                        UP if point[1] > 0 else DOWN, buff=0.2)
        self.play(Write(mag_label))
        
        self.wait(2)