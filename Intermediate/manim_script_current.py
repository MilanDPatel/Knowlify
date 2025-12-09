from manim import *
import numpy as np

class DerivativesDeepDive(Scene):
    def construct(self):
        # Section 1: Introduction to Derivatives (55 seconds)
        
        # Moment 1: Visual introduction to derivative concept (20 seconds)
        title1 = Text("Introduction to Derivatives", font_size=48, color=WHITE)
        title1.to_edge(UP)
        self.play(FadeIn(title1), run_time=2)
        self.wait(1)
        self.play(FadeOut(title1), run_time=0.5)
        
        # Create coordinate axes
        axes = Axes(
            x_range=[-5, 5, 1],
            y_range=[0, 25, 5],
            x_length=8,
            y_length=6,
            axis_config={"color": WHITE}
        )
        axes_labels = axes.get_axis_labels(x_label="x", y_label="f(x)")
        
        # Step 1 (3s): Draw blue parabola f(x) = x²
        parabola = axes.plot(lambda x: x**2, color=BLUE, x_range=[-5, 5])
        func_label = MathTex(r"f(x) = x^2", color=WHITE).to_corner(UL)
        
        self.play(Create(axes), Write(axes_labels), run_time=1.5)
        self.play(Create(parabola), Write(func_label), run_time=1.5)
        
        # Step 2 (2s): Show green secant line through (2,4) and (4,16)
        point1 = axes.coords_to_point(2, 4)
        point2 = axes.coords_to_point(4, 16)
        secant_line = Line(
            axes.coords_to_point(1, 1), 
            axes.coords_to_point(5, 25), 
            color=GREEN
        )
        dot1 = Dot(point1, color=RED)
        dot2 = Dot(point2, color=RED)
        
        self.play(Create(secant_line), Create(dot1), Create(dot2), run_time=2)
        
        # Step 3 (5s): Gradually move second point closer to (3,9)
        target_point = axes.coords_to_point(3, 9)
        target_dot = Dot(target_point, color=RED)
        
        # Animate secant line becoming tangent
        for i in range(5):
            x_val = 4 - i * 0.2
            new_point = axes.coords_to_point(x_val, x_val**2)
            new_secant = Line(point1, new_point, color=GREEN)
            if i == 0:
                self.play(Transform(secant_line, new_secant), Transform(dot2, Dot(new_point, color=RED)), run_time=1)
            else:
                self.play(Transform(secant_line, new_secant), Transform(dot2, Dot(new_point, color=RED)), run_time=1)
        
        # Step 4 (3s): Final red tangent line appears at x = 3
        tangent_line = Line(
            axes.coords_to_point(1, -3),
            axes.coords_to_point(5, 21),
            color=RED
        )
        self.play(Transform(secant_line, tangent_line), run_time=2)
        self.play(Transform(dot2, target_dot), run_time=1)
        
        # Step 5 (2s): Label 'slope = 6' appears
        slope_label = Text("slope = 6", color=YELLOW, font_size=24)
        slope_label.next_to(tangent_line, UP)
        self.play(Write(slope_label), run_time=2)
        
        # Fade out everything
        self.play(FadeOut(*self.mobjects), run_time=1)
        self.wait(0.5)
        
        # Moment 2: Formal derivative definition (15 seconds)
        
        # Step 1 (3s): Write limit definition equation
        limit_def = MathTex(
            r"f'(x) = \lim_{h \to 0} \frac{f(x+h) - f(x)}{h}",
            font_size=48,
            color=WHITE
        )
        limit_def.move_to(ORIGIN)
        self.play(Write(limit_def), run_time=3)
        
        # Step 2-3 (7s): Highlight variables and show definitions
        var_f = Text("f(x) = function", color=YELLOW, font_size=24)
        var_h = Text("h = small increment", color=YELLOW, font_size=24)
        var_x = Text("x = point", color=YELLOW, font_size=24)
        
        var_group = VGroup(var_f, var_h, var_x)
        var_group.arrange(DOWN, aligned_edge=LEFT)
        var_group.to_edge(DOWN)
        
        self.play(Write(var_group), run_time=4)
        
        # Step 4-5 (5s): Emphasize limit and connection
        emphasis = Text("as h approaches 0", color=RED, font_size=32)
        emphasis.next_to(limit_def, DOWN, buff=0.5)
        self.play(Write(emphasis), run_time=2)
        
        connection = Text("→ tangent line slope", color=GREEN, font_size=28)
        connection.next_to(emphasis, DOWN)
        self.play(Write(connection), run_time=3)
        
        self.play(FadeOut(*self.mobjects), run_time=1)
        self.wait(0.5)
        
        # Moment 3: Calculate derivative of x² at x = 3 (20 seconds)
        
        # Step 1 (3s): Substitute x = 3 into limit definition
        step1 = MathTex(
            r"f'(3) = \lim_{h \to 0} \frac{(3+h)^2 - 9}{h}",
            font_size=36,
            color=WHITE
        )
        step1.to_edge(UP)
        self.play(Write(step1), run_time=3)
        
        # Step 2 (3s): Expand (3+h)²
        step2 = MathTex(
            r"= \lim_{h \to 0} \frac{9 + 6h + h^2 - 9}{h}",
            font_size=36,
            color=GREEN
        )
        step2.next_to(step1, DOWN, aligned_edge=LEFT)
        self.play(Write(step2), run_time=3)
        
        # Step 3 (3s): Simplify numerator
        step3 = MathTex(
            r"= \lim_{h \to 0} \frac{6h + h^2}{h}",
            font_size=36,
            color=GREEN
        )
        step3.next_to(step2, DOWN, aligned_edge=LEFT)
        self.play(Write(step3), run_time=3)
        
        # Step 4 (3s): Factor out h
        step4 = MathTex(
            r"= \lim_{h \to 0} \frac{h(6 + h)}{h} = \lim_{h \to 0} (6 + h)",
            font_size=36,
            color=GREEN
        )
        step4.next_to(step3, DOWN, aligned_edge=LEFT)
        self.play(Write(step4), run_time=3)
        
        # Step 5-6 (8s): Final answer
        step5 = MathTex(
            r"= 6",
            font_size=48,
            color=BLUE
        )
        step5.next_to(step4, DOWN, aligned_edge=LEFT)
        self.play(Write(step5), run_time=3)
        
        # Highlight final answer
        final_box = SurroundingRectangle(step5, color=BLUE, buff=0.2)
        final_label = Text("f'(3) = 6", color=BLUE, font_size=32)
        final_label.next_to(final_box, DOWN)
        self.play(Create(final_box), Write(final_label), run_time=5)
        
        self.play(FadeOut(*self.mobjects), run_time=1)
        self.wait(0.5)
        
        # Section 2: Rules of Differentiation (55 seconds)
        
        title2 = Text("Rules of Differentiation", font_size=48, color=WHITE)
        title2.to_edge(UP)
        self.play(FadeIn(title2), run_time=2)
        self.wait(1)
        self.play(FadeOut(title2), run_time=0.5)
        
        # Moment 1: Power Rule introduction (20 seconds)
        
        # Step 1 (3s): Display power rule formula
        power_rule = MathTex(
            r"\frac{d}{dx}[x^n] = nx^{n-1}",
            font_size=48,
            color="#FFA500"  # Orange
        )
        power_rule.to_edge(UP)
        self.play(Write(power_rule), run_time=3)
        
        # Step 2 (2s): Show three example functions
        ex1 = MathTex(r"x^3", font_size=36, color=WHITE)
        ex2 = MathTex(r"x^5", font_size=36, color=WHITE)
        ex3 = MathTex(r"x^{-2}", font_size=36, color=WHITE)
        
        examples = VGroup(ex1, ex2, ex3)
        examples.arrange(RIGHT, buff=2)
        examples.move_to(ORIGIN + UP)
        self.play(Write(examples), run_time=2)
        
        # Step 3 (5s): Apply rule to x³
        result1 = MathTex(r"3x^2", font_size=36, color=GREEN)
        result1.next_to(ex1, DOWN, buff=1)
        arrow1 = Arrow(ex1.get_bottom(), result1.get_top(), color=YELLOW)
        self.play(Create(arrow1), Write(result1), run_time=5)
        
        # Step 4 (4s): Apply to x⁵
        result2 = MathTex(r"5x^4", font_size=36, color=GREEN)
        result2.next_to(ex2, DOWN, buff=1)
        arrow2 = Arrow(ex2.get_bottom(), result2.get_top(), color=YELLOW)
        self.play(Create(arrow2), Write(result2), run_time=4)
        
        # Step 5 (4s): Apply to x⁻²
        result3 = MathTex(r"-2x^{-3}", font_size=36, color=GREEN)
        result3.next_to(ex3, DOWN, buff=1)
        arrow3 = Arrow(ex3.get_bottom(), result3.get_top(), color=YELLOW)
        self.play(Create(arrow3), Write(result3), run_time=4)
        
        # Step 6 (2s): Highlight all results
        results_group = VGroup(result1, result2, result3)
        highlight_boxes = VGroup(*[SurroundingRectangle(r, color=GREEN) for r in results_group])
        self.play(Create(highlight_boxes), run_time=2)
        
        self.play(FadeOut(*self.mobjects), run_time=1)
        self.wait(0.5)
        
        # Moment 2: Product Rule formula (15 seconds)
        
        # Step 1 (3s): Write product rule formula
        product_rule = MathTex(
            r"(uv)' = u'v + uv'",
            font_size=48,
            color="#800080"  # Purple
        )
        product_rule.move_to(ORIGIN)
        self.play(Write(product_rule), run_time=3)
        
        # Step 2-3 (6s): Color-code variables
        u_box = Rectangle(width=1, height=0.8, color=BLUE, fill_opacity=0.3)
        v_box = Rectangle(width=1, height=0.8, color=RED, fill_opacity=0.3)
        u_label = Text("u(x)", color=BLUE, font_size=24)
        v_label = Text("v(x)", color=RED, font_size=24)
        
        u_box.next_to(product_rule, LEFT, buff=2)
        v_box.next_to(product_rule, RIGHT, buff=2)
        u_label.move_to(u_box)
        v_label.move_to(v_box)
        
        self.play(Create(u_box), Write(u_label), run_time=3)
        self.play(Create(v_box), Write(v_label), run_time=3)
        
        # Step 4-5 (6s): Show derivatives and terms
        explanation = Text("First term: u'v + Second term: uv'", font_size=28, color=WHITE)
        explanation.next_to(product_rule, DOWN, buff=1)
        self.play(Write(explanation), run_time=6)
        
        self.play(FadeOut(*self.mobjects), run_time=1)
        self.wait(0.5)
        
        # Moment 3: Product rule example (20 seconds)
        
        # Step 1 (3s): Show function
        function = MathTex(r"f(x) = x^2\sin(x)", font_size=40, color=WHITE)
        function.to_edge(UP)
        self.play(Write(function), run_time=3)
        
        # Step 2 (3s): Identify u and v
        u_id = MathTex(r"u = x^2", font_size=32, color=BLUE)
        v_id = MathTex(r"v = \sin(x)", font_size=32, color=RED)
        
        u_id.move_to(LEFT * 3 + UP * 0.5)
        v_id.move_to(RIGHT * 3 + UP * 0.5)
        
        u_box2 = SurroundingRectangle(u_id, color=BLUE)
        v_box2 = SurroundingRectangle(v_id, color=RED)
        
        self.play(Write(u_id), Create(u_box2), run_time=1.5)
        self.play(Write(v_id), Create(v_box2), run_time=1.5)
        
        # Step 3 (3s): Find derivatives
        u_prime = MathTex(r"u' = 2x", font_size=32, color=BLUE)
        v_prime = MathTex(r"v' = \cos(x)", font_size=32, color=RED)
        
        u_prime.next_to(u_id, DOWN, buff=0.5)
        v_prime.next_to(v_id, DOWN, buff=0.5)
        
        self.play(Write(u_prime), Write(v_prime), run_time=3)
        
        # Step 4-5 (8s): Apply formula
        term1 = MathTex(r"u'v = 2x \cdot \sin(x)", font_size=28, color=WHITE)
        term2 = MathTex(r"uv' = x^2 \cdot \cos(x)", font_size=28, color=WHITE)
        
        term1.move_to(DOWN * 1)
        term2.next_to(term1, DOWN, buff=0.3)
        
        self.play(Write(term1), run_time=4)
        self.play(Write(term2), run_time=4)
        
        # Step 6 (3s): Final result
        final_result = MathTex(
            r"f'(x) = 2x\sin(x) + x^2\cos(x)",
            font_size=36,
            color=YELLOW
        )
        final_result.next_to(term2, DOWN, buff=0.5)
        final_box2 = SurroundingRectangle(final_result, color=YELLOW)
        
        self.play(Write(final_result), Create(final_box2), run_time=3)
        
        self.play(FadeOut(*self.mobjects), run_time=1)
        self.wait(0.5)
        
        # Section 3: Applications of Derivatives (55 seconds)
        
        title3 = Text("Applications of Derivatives", font_size=48, color=WHITE)
        title3.to_edge(UP)
        self.play(FadeIn(title3), run_time=2)
        self.wait(1)
        self.play(FadeOut(title3), run_time=0.5)
        
        # Moment 1: Physics application (25 seconds)
        
        # Create three stacked graphs
        axes1 = Axes(x_range=[0, 4, 1], y_range=[0, 10, 2], x_length=6, y_length=2)
        axes2 = Axes(x_range=[0, 4, 1], y_range=[-4, 4, 2], x_length=6, y_length=2)
        axes3 = Axes(x_range=[0, 4, 1], y_range=[0, 4, 1], x_length=6, y_length=2)
        
        axes1.to_edge(UP, buff=1)
        axes2.move_to(ORIGIN)
        axes3.to_edge(DOWN, buff=1)
        
        # Step 1 (4s): Draw position curve
        pos_func = axes1.plot(lambda t: t**2 - 2*t + 5, color=BLUE, x_range=[0, 4])
        pos_eq = MathTex(r"s(t) = t^2 - 2t + 5", font_size=24, color=BLUE)
        pos_eq.next_to(axes1, LEFT)
        
        self.play(Create(axes1), Create(pos_func), Write(pos_eq), run_time=4)
        
        # Step 2 (3s): Label axes
        t_label1 = Text("t", font_size=20).next_to(axes1, DOWN+RIGHT)
        s_label = Text("s(t)", font_size=20).next_to(axes1, LEFT+UP)
        self.play(Write(t_label1), Write(s_label), run_time=3)
        
        # Step 3 (5s): Show velocity
        vel_func = axes2.plot(lambda t: 2*t - 2, color=RED, x_range=[0, 4])
        vel_eq = MathTex(r"v(t) = s'(t) = 2t - 2", font_size=24, color=RED)
        vel_eq.next_to(axes2, LEFT)
        
        self.play(Create(axes2), Create(vel_func), Write(vel_eq), run_time=5)
        
        # Step 4 (3s): Draw velocity graph
        t_label2 = Text("t", font_size=20).next_to(axes2, DOWN+RIGHT)
        v_label = Text("v(t)", font_size=20).next_to(axes2, LEFT+UP)
        self.play(Write(t_label2), Write(v_label), run_time=3)
        
        # Step 5 (5s): Show acceleration
        acc_func = axes3.plot(lambda t: 2, color=GREEN, x_range=[0, 4])
        acc_eq = MathTex(r"a(t) = v'(t) = 2", font_size=24, color=GREEN)
        acc_eq.next_to(axes3, LEFT)
        
        self.play(Create(axes3), Create(acc_func), Write(acc_eq), run_time=5)
        
        # Step 6-7 (5s): Labels and arrows
        t_label3 = Text("t", font_size=20).next_to(axes3, DOWN+RIGHT)
        a_label = Text("a(t)", font_size=20).next_to(axes3, LEFT+UP)
        
        arrow_sv = Arrow(axes1.get_bottom(), axes2.get_top(), color=YELLOW)
        arrow_va = Arrow(axes2.get_bottom(), axes3.get_top(), color=YELLOW)
        
        self.play(Write(t_label3), Write(a_label), run_time=2)
        self.play(Create(arrow_sv), Create(arrow_va), run_time=3)
        
        self.play(FadeOut(*self.mobjects), run_time=1)
        self.wait(0.5)
        
        # Moment 2: Optimization example (30 seconds)
        
        # Create profit function graph
        opt_axes = Axes(
            x_range=[0, 8, 1],
            y_range=[-15, 5, 5],
            x_length=8,
            y_length=6
        )
        opt_axes.move_to(ORIGIN)
        
        # Step 1 (4s): Draw profit parabola
        profit_func = opt_axes.plot(lambda x: -x**2 + 8*x - 12, color=GREEN, x_range=[0, 8])
        profit_eq = MathTex(r"P(x) = -x^2 + 8x - 12", font_size=32, color=WHITE)
        profit_eq.to_edge(UP)
        
        self.play(Create(opt_axes), Create(profit_func), Write(profit_eq), run_time=4)
        
        # Step 2 (3s): Label axes
        x_label = Text("quantity", font_size=24).next_to(opt_axes, DOWN)
        p_label = Text("profit", font_size=24).next_to(opt_axes, LEFT)
        self.play(Write(x_label), Write(p_label), run_time=3)
        
        # Step 3 (4s): Show derivative
        deriv_eq = MathTex(r"P'(x) = -2x + 8", font_size=28, color=WHITE)
        deriv_eq.next_to(profit_eq, DOWN)
        self.play(Write(deriv_eq), run_time=4)
        
        # Step 4 (4s): Explain critical points
        critical_text = Text("Critical points: P'(x) = 0", font_size=24, color=YELLOW)
        critical_text.next_to(deriv_eq, DOWN)
        self.play(Write(critical_text), run_time=4)
        
        # Step 5 (5s): Solve equation
        solve_eq = MathTex(r"P'(x) = 0 \Rightarrow x = 4", font_size=28, color=WHITE)
        solve_eq.next_to(critical_text, DOWN)
        self.play(Write(solve_eq), run_time=5)
        
        # Step 6 (3s): Mark critical point
        critical_point = opt_axes.coords_to_point(4, 4)
        critical_dot = Dot(critical_point, color=RED, radius=0.1)
        self.play(Create(critical_dot), run_time=3)
        
        # Step 7 (4s): Calculate P(4)
        calc_text = MathTex(r"P(4) = -16 + 32 - 12 = 4", font_size=24, color=WHITE)
        calc_text.next_to(solve_eq, DOWN)
        self.play(Write(calc_text), run_time=4)
        
        # Step 8 (3s): Highlight maximum
        max_label = Text("Maximum profit: 4 units at x = 4", font_size=24, color=YELLOW)
        max_box = SurroundingRectangle(max_label, color=YELLOW)
        max_group = VGroup(max_label, max_box)
        max_group.next_to(calc_text, DOWN)
        
        self.play(Write(max_label), Create(max_box), run_time=3)
        
        # Final fadeout
        self.play(FadeOut(*self.mobjects), run_time=2)
        self.wait(1)