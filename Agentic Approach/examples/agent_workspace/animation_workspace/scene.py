# The videos are meant to be in horizontal format (1920*1080, landscape orientation).
# Using Manim's default configuration for standard 16:9 aspect ratio.

from manim import *
import math
import random

class ContextRotScene(Scene):
    def construct(self):
        # --- Common Assets & Helpers ---
        self.caption_bar = Rectangle(
            width=14.22, height=1.2, 
            fill_color=BLACK, fill_opacity=0.8,
            stroke_width=0
        ).to_edge(DOWN, buff=0)
        
        self.caption_text = Text("", font_size=24, color=WHITE).move_to(self.caption_bar.get_center())
        
        def set_caption(text_str):
            new_text = Text(text_str, font_size=24, color=WHITE).move_to(self.caption_bar.get_center())
            if self.caption_text.text == "":
                self.play(FadeIn(self.caption_bar), Write(new_text), run_time=1)
                self.caption_text = new_text
            else:
                self.play(Transform(self.caption_text, new_text), run_time=0.5)
            self.wait(0.5)

        # --- Scene 0: Opening ---
        series_header = Text("Part 1/5: Recursive Language Models", font_size=20, color=BLUE_B).to_edge(UP)
        hook_text = Text("The Problem of Context Rot in Long-Context LLMs", font_size=40, gradient=(BLUE, PURPLE))
        
        self.play(Write(series_header))
        self.play(FadeIn(hook_text, shift=UP))
        self.wait(2)
        
        # Start Caption
        set_caption("Understanding The Problem of Context Rot in Long-Context LLMs")
        
        self.play(FadeOut(hook_text))
        
        # --- Scene 1: The Infinite Scroll ---
        
        brain_group = VGroup()
        brain_circle = Circle(radius=1.5, color=BLUE, fill_opacity=0.1, stroke_width=4)
        brain_nodes = VGroup(*[
            Dot(point=brain_circle.get_center() + np.array([
                math.cos(angle) * r, math.sin(angle) * r, 0
            ]), color=BLUE_A, radius=0.08)
            for r in [0.5, 1.0] for angle in np.linspace(0, 2*PI, 6 if r==0.5 else 10, endpoint=False)
        ])
        
        brain_lines = VGroup()
        random.seed(42)
        node_list = list(brain_nodes)
        for _ in range(15):
            p1 = random.choice(node_list)
            p2 = random.choice(node_list)
            if p1 != p2:
                brain_lines.add(Line(p1.get_center(), p2.get_center(), stroke_width=1, stroke_opacity=0.5, color=BLUE_B))
        
        brain_group.add(brain_circle, brain_lines, brain_nodes).move_to(ORIGIN)
        
        token_counter_val = ValueTracker(10000)
        token_label = DecimalNumber(10000, num_decimal_places=0, include_sign=False, group_with_commas=True, font_size=36)
        token_label.add_updater(lambda d: d.set_value(token_counter_val.get_value()))
        token_label.next_to(brain_group, UP)
        token_text = Text("Tokens", font_size=24).next_to(token_label, RIGHT, buff=0.1).shift(DOWN * 0.05)
        
        self.play(
            FadeIn(brain_group), 
            FadeIn(token_label), 
            FadeIn(token_text),
            FadeIn(series_header)
        )
        
        # Documents entering
        docs = VGroup()
        for i in range(5):
            doc = VGroup(
                Rectangle(width=0.6, height=0.8, fill_color=WHITE, fill_opacity=0.8, stroke_width=1),
                Line(start=LEFT*0.2, end=RIGHT*0.2, stroke_width=1).shift(UP*0.2),
                Line(start=LEFT*0.2, end=RIGHT*0.2, stroke_width=1),
                Line(start=LEFT*0.2, end=RIGHT*0.2, stroke_width=1).shift(DOWN*0.2),
            )
            doc.move_to(RIGHT * (7 + i*1.5))
            docs.add(doc)
            
        set_caption("Modern LLMs have massive context windows (1M+ tokens)")
        
        self.play(
            LaggedStart(*[
                doc.animate.move_to(brain_group.get_center()).scale(0).set_opacity(0)
                for doc in docs
            ], lag_ratio=0.2, run_time=3),
            token_counter_val.animate.set_value(1000000),
            brain_circle.animate.set_color(BLUE_E).set_stroke(width=6),
            run_time=4
        )
        self.wait(1)

        # --- Scene 2: The Fog of Data ---
        set_caption("But massive context leads to 'Context Rot' - attention degrades")
        
        self.play(
            brain_group.animate.scale(2),
            token_label.animate.shift(UP*1.5),
            token_text.animate.shift(UP*1.5),
            series_header.animate.set_opacity(0),
            run_time=1.5
        )
        
        new_lines = VGroup()
        for _ in range(50):
             p1 = random.choice(node_list)
             p2 = random.choice(node_list)
             new_lines.add(Line(p1.get_center(), p2.get_center(), stroke_width=1, stroke_opacity=0.3, color=GREY))
        
        rot_text = Text("CONTEXT ROT", color=RED, font_size=60).move_to(brain_group.get_center())
        
        self.play(
            Transform(brain_lines, new_lines),
            brain_circle.animate.set_color(GREY),
            brain_nodes.animate.set_color(GREY_B),
            FadeIn(rot_text, scale=0.5),
            run_time=2
        )
        self.wait(2)
        
        self.play(
            FadeOut(brain_group), 
            FadeOut(brain_lines),
            FadeOut(rot_text),
            FadeOut(token_label),
            FadeOut(token_text)
        )

        # --- Scene 3: Needles vs Haystacks ---
        set_caption("Simple retrieval works, but dense reasoning fails")
        
        left_group = VGroup()
        right_group = VGroup()
        
        l_title = Text("Simple Task", font_size=30).move_to(LEFT * 3.5 + UP * 2.5)
        haystack_l = VGroup(*[
            Line(ORIGIN, RIGHT*0.5, color=YELLOW_E, stroke_width=2).rotate(random.random()*TAU).shift(
                LEFT*3.5 + np.array([random.uniform(-1,1), random.uniform(-1,1), 0])
            ) for _ in range(40)
        ])
        needle = Line(ORIGIN, RIGHT*0.5, color=RED, stroke_width=4).rotate(PI/4).move_to(LEFT*3.5)
        
        check = Text("✔", color=GREEN, font_size=60).next_to(haystack_l, UP)
        left_group.add(l_title, haystack_l, needle)
        
        r_title = Text("Dense Task", font_size=30).move_to(RIGHT * 3.5 + UP * 2.5)
        haystack_r = VGroup(*[
             Line(ORIGIN, RIGHT*0.6, color=RED_E, stroke_width=2).rotate(random.random()*TAU).shift(
                RIGHT*3.5 + np.array([random.uniform(-1,1), random.uniform(-1,1), 0])
            ) for _ in range(60)
        ])
        connections = VGroup(*[
             Line(haystack_r[i].get_center(), haystack_r[j].get_center(), stroke_width=0.5, color=RED_A, stroke_opacity=0.5)
             for i in range(0, 60, 2) for j in range(1, 60, 5) if abs(i-j) < 10
        ])
        
        cross = Text("✘", color=RED, font_size=60).next_to(haystack_r, UP)
        right_group.add(r_title, haystack_r, connections)
        
        self.play(FadeIn(left_group), FadeIn(right_group))
        self.wait(0.5)
        
        spotlight_l = Circle(radius=0.3, color=WHITE, stroke_opacity=0.8).move_to(LEFT*3.5 + UP*1)
        self.play(spotlight_l.animate.move_to(needle.get_center()), run_time=1)
        self.play(Indicate(needle, color=RED), FadeIn(check))
        
        spotlight_r = Circle(radius=0.3, color=WHITE, stroke_opacity=0.8).move_to(RIGHT*3.5 + UP*1)
        self.play(
            spotlight_r.animate.move_to(RIGHT*3.5).scale(3),
            run_time=1.5
        )
        self.play(spotlight_r.animate.set_opacity(0), FadeIn(cross))
        self.wait(1)
        
        self.play(FadeOut(left_group), FadeOut(right_group), FadeOut(check), FadeOut(cross), FadeOut(spotlight_l), FadeOut(spotlight_r))

        # --- Scene 4: The Performance Cliff ---
        set_caption("Performance dives off a cliff as context length increases")
        
        ax = Axes(
            x_range=[0, 3.5, 1],
            y_range=[0, 100, 20],
            x_length=9,
            y_length=5,
            axis_config={"include_tip": True},
            x_axis_config={"numbers_to_include": []},
            y_axis_config={"numbers_to_include": [0, 50, 100]}
        ).shift(UP * 0.5)
        
        x_labels = VGroup(
            Text("8k", font_size=20).next_to(ax.c2p(0,0), DOWN),
            Text("32k", font_size=20).next_to(ax.c2p(1,0), DOWN),
            Text("128k", font_size=20).next_to(ax.c2p(2,0), DOWN),
            Text("1M", font_size=20).next_to(ax.c2p(3,0), DOWN),
        )
        
        y_label = Text("Accuracy %", font_size=24).next_to(ax.y_axis, UP)
        x_label_title = Text("Context Length (Tokens)", font_size=24).next_to(ax.x_axis, RIGHT)
        
        retrieval_curve = ax.plot(lambda x: 95 + math.sin(x)*2, x_range=[0, 3.2], color=GREEN)
        retrieval_label = Text("Retrieval", color=GREEN, font_size=20).next_to(retrieval_curve.get_end(), RIGHT)
        
        def reasoning_func(x):
            if x < 1.5:
                return 90
            else:
                return 90 - 80 / (1 + math.exp(-5 * (x - 2.2)))
                
        reasoning_curve = ax.plot(reasoning_func, x_range=[0, 3.2], color=RED)
        reasoning_label = Text("Reasoning", color=RED, font_size=20).next_to(reasoning_curve.get_point_from_function(2.5), UP).shift(RIGHT*0.5)

        self.play(Create(ax), Write(x_labels), Write(y_label), Write(x_label_title))
        self.play(Create(retrieval_curve), FadeIn(retrieval_label))
        self.play(Create(reasoning_curve), FadeIn(reasoning_label), run_time=2)
        self.wait(2)
        
        graph_group = VGroup(ax, x_labels, y_label, x_label_title, retrieval_curve, retrieval_label, reasoning_curve, reasoning_label)
        self.play(FadeOut(graph_group))

        # --- Scene 5: The Memory Bottleneck ---
        set_caption("Trying to fit all context into memory is the bottleneck")
        
        ram_chip = VGroup(
            Square(side_length=2, fill_color=DARK_GREY, fill_opacity=1, stroke_color=WHITE),
            Text("RAM", font_size=30).shift(UP*0.5),
            Text("Context", font_size=20, color=GREY_A).shift(DOWN*0.5)
        ).move_to(LEFT * 3)
        
        hdd_stack = VGroup(*[
            Rectangle(width=2.5, height=0.5, fill_color=BLUE_E, fill_opacity=1, stroke_color=WHITE).shift(UP * i * 0.1)
            for i in range(10)
        ]).move_to(RIGHT * 3)
        hdd_label = Text("Prompt (10M+)", font_size=24).next_to(hdd_stack, UP)
        
        self.play(FadeIn(ram_chip), FadeIn(hdd_stack), FadeIn(hdd_label))
        
        self.play(
            hdd_stack.animate.move_to(ram_chip.get_center()),
            run_time=2
        )
        
        self.play(
            ram_chip[0].animate.set_fill(RED_E),
            Wiggle(ram_chip),
            hdd_stack.animate.set_opacity(0.5),
        )
        
        smoke = VGroup(*[
             Circle(radius=r, fill_color=GREY, fill_opacity=0.5, stroke_width=0).shift(ram_chip.get_center() + np.array([random.uniform(-1,1), random.uniform(0,2), 0]))
             for r in [0.2, 0.3, 0.4]
        ])
        self.play(FadeIn(smoke, shift=UP), run_time=1)
        self.wait(1)
        
        self.play(FadeOut(ram_chip), FadeOut(hdd_stack), FadeOut(hdd_label), FadeOut(smoke))

        # --- Scene 6: Out-of-Core Inspiration ---
        set_caption("The Solution: 'Out-of-Core' Algorithms - Fetch only what you need")
        
        ram_chip = Square(side_length=2, fill_color=GREEN_E, fill_opacity=1, stroke_color=WHITE).move_to(ORIGIN)
        ram_text = Text("Processing", font_size=24).move_to(ram_chip)
        
        hdd_stack = VGroup(*[
            Rectangle(width=1, height=1, fill_color=BLUE, fill_opacity=0.8, stroke_color=WHITE).move_to(LEFT * 5 + RIGHT * i * 0.1 + UP * i * 0.05)
            for i in range(5)
        ])
        hdd_label = Text("Disk", font_size=24).next_to(hdd_stack, UP)
        
        self.play(FadeIn(ram_chip), FadeIn(ram_text), FadeIn(hdd_stack), FadeIn(hdd_label))
        
        for i in range(3):
            chunk = hdd_stack[4-i].copy()
            self.play(chunk.animate.move_to(ram_chip.get_center()), run_time=0.8)
            self.play(chunk.animate.set_color(YELLOW), run_time=0.3)
            self.play(FadeOut(chunk, shift=RIGHT), run_time=0.5)
            
        ooc_text = Text("Out-of-Core Algorithm", font_size=36, color=YELLOW).to_edge(UP, buff=2)
        self.play(Write(ooc_text))
        self.wait(1)
        
        self.play(FadeOut(ram_chip), FadeOut(ram_text), FadeOut(hdd_stack), FadeOut(hdd_label), FadeOut(ooc_text))

        # --- Scene 7: Inference-Time Scaling ---
        set_caption("Inference-Time Scaling: The model reads the prompt like a book")
        
        scroll = Rectangle(width=10, height=2, fill_color=GREY_E, stroke_color=WHITE).shift(DOWN * 1)
        scroll_lines = VGroup(*[
            Line(start=scroll.get_left() + RIGHT*0.5 + UP * (0.8 - i*0.2), 
                 end=scroll.get_right() + LEFT*0.5 + UP * (0.8 - i*0.2), 
                 color=GREY_A, stroke_width=2)
            for i in range(8)
        ])
        env_label = Text("Environment (The Prompt)", font_size=24).next_to(scroll, DOWN)
        
        interpreter = RoundedRectangle(corner_radius=0.2, width=3, height=2, fill_color=BLACK, stroke_color=GREEN).shift(UP * 1.5)
        int_label = Text("Python REPL", font_size=24, color=GREEN).next_to(interpreter, UP)
        code_line = Text("read(chapter_1)", font="Monospace", font_size=24, color=GREEN).move_to(interpreter)
        
        self.play(FadeIn(scroll), FadeIn(scroll_lines), FadeIn(env_label))
        self.play(Create(interpreter), FadeIn(int_label))
        
        self.play(Write(code_line))
        
        highlight = SurroundingRectangle(scroll_lines[0:2], color=YELLOW, fill_opacity=0.3, stroke_width=0)
        self.play(FadeIn(highlight))
        
        self.play(highlight.animate.move_to(interpreter.get_center()).scale(0.5).set_opacity(0), run_time=1)
        
        new_code = Text("read(chapter_5)", font="Monospace", font_size=24, color=GREEN).move_to(interpreter)
        self.play(Transform(code_line, new_code))
        
        highlight2 = SurroundingRectangle(scroll_lines[6:8], color=YELLOW, fill_opacity=0.3, stroke_width=0)
        self.play(FadeIn(highlight2))
        self.play(highlight2.animate.move_to(interpreter.get_center()).scale(0.5).set_opacity(0), run_time=1)
        
        self.wait(1)
        
        self.play(
            FadeOut(scroll), FadeOut(scroll_lines), FadeOut(env_label), 
            FadeOut(interpreter), FadeOut(int_label), FadeOut(code_line)
        )

        # --- Scene 8: The Flat Line of Success ---
        set_caption("Recursive Models maintain accuracy regardless of length")
        
        self.play(FadeIn(graph_group))
        
        recursive_curve = ax.plot(lambda x: 95, x_range=[0, 3.2], color=BLUE)
        recursive_label = Text("Recursive Model", color=BLUE, font_size=20).next_to(recursive_curve.get_end(), UP)
        
        self.play(Create(recursive_curve), FadeIn(recursive_label), run_time=2)
        
        sparkles = VGroup(*[
            Dot(point=ax.c2p(x, 95), color=YELLOW, radius=0.05)
            for x in np.linspace(1.5, 3.2, 10)
        ])
        self.play(LaggedStart(*[FadeIn(s, scale=2) for s in sparkles], lag_ratio=0.1), run_time=1)
        self.play(FadeOut(sparkles))
        
        self.wait(2)
        
        self.play(FadeOut(graph_group), FadeOut(recursive_curve), FadeOut(recursive_label))
        set_caption("")
        self.play(FadeOut(self.caption_bar), FadeOut(self.caption_text))
        
        # --- Final Scene ---
        title = Text("Key Takeaways", font_size=40, color=BLUE).to_edge(UP)
        points = BulletedList(
            "Physical context != Effective reasoning capacity",
            "'Context Rot' degrades performance on dense tasks",
            "Solution: Inference-time compute scaling",
            "Mimics 'Out-of-Core' algorithms (chunking)",
            font_size=28
        ).next_to(title, DOWN)
        
        self.play(Write(title), Write(points))
        self.wait(3)
        
        next_box = RoundedRectangle(width=10, height=2, fill_color=GREY_E, fill_opacity=1).to_edge(DOWN, buff=1)
        next_text = VGroup(
            Text("Coming Next:", font_size=24, color=YELLOW),
            Text("Recursive Language Models (RLMs): The Core Architecture", font_size=32)
        ).arrange(DOWN).move_to(next_box)
        
        self.play(FadeIn(next_box), FadeIn(next_text))
        self.wait(3)
        
        self.play(FadeOut(title), FadeOut(points), FadeOut(next_box), FadeOut(next_text))
