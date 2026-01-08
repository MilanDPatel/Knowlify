# The videos are meant to be in horizontal format (1920*1080, landscape orientation).
# Using Manim's default configuration for standard 16:9 aspect ratio.

from manim import *
from manim_voiceover import VoiceoverScene
from kokoro_mv import KokoroService

class ContextRotScene(VoiceoverScene):
    def construct(self):
        # Initialize Kokoro TTS
        self.set_speech_service(KokoroService(voice="af_sarah", lang="en-us"))
        
        # Concept Caption Setup
        self.caption_bg = Rectangle(width=14.22, height=1.0, fill_color=BLACK, fill_opacity=0.8, stroke_width=0)
        self.caption_bg.to_edge(DOWN, buff=0)
        self.caption_text = Text("", font_size=24, color=WHITE).move_to(self.caption_bg)
        # We'll add them to the scene but keep the text empty initially
        self.add(self.caption_bg, self.caption_text)

        # Helper to update caption
        def update_caption(new_text_str):
            new_text = Text(new_text_str, font_size=24, color=WHITE).move_to(self.caption_bg)
            self.play(Transform(self.caption_text, new_text), run_time=0.5)

        # Scene 0: Opening
        with self.voiceover(text="Welcome to part 1 of our series on Recursive Language Models. Despite valid context windows extending to millions of tokens, frontier models like GPT-5 suffer from 'context rot,' where reasoning capabilities degrade as input length increases. This topic explores why simply increasing context size is insufficient for complex tasks and introduces the motivation behind inference-time scaling.") as tracker:
            header = Text("Part 1/5: Recursive Language Models", font_size=24, color=BLUE).to_edge(UP)
            title = Text("The Problem of Context Rot", font_size=48).center()
            subtitle = Text("Why Bigger Context Isn't Enough", font_size=32, color=GRAY).next_to(title, DOWN)
            
            update_caption("Understanding The Problem of Context Rot in Long-Context LLMs")
            self.play(Write(header), FadeIn(title), FadeIn(subtitle))
            self.wait(tracker.duration - 2)

        self.play(FadeOut(title), FadeOut(subtitle))

        # Scene 1: The Digital Brain & Stream
        with self.voiceover(text="In the world of artificial intelligence, we are witnessing an explosion of memory. Modern language models can now technically ingest entire libraries—millions of words—in a single prompt. It sounds like the ultimate super-power: perfect recall at an infinite scale.") as tracker:
            update_caption("Modern LLMs have massive context windows (1M+ tokens)")
            
            # Brain visualization
            brain_circle = Circle(radius=1.5, color=BLUE, fill_opacity=0.2).shift(RIGHT * 2)
            brain_network = VGroup(*[
                Line(brain_circle.point_from_proportion(i/10), brain_circle.point_from_proportion(((i+4)%10)/10), color=BLUE_A, stroke_width=2)
                for i in range(10)
            ])
            brain_label = Text("LLM", font_size=24).next_to(brain_circle, UP)
            brain = VGroup(brain_circle, brain_network, brain_label)
            
            self.play(Create(brain))
            
            # Document stream
            docs = VGroup(*[
                Rectangle(width=0.4, height=0.6, fill_color=WHITE, fill_opacity=0.8, stroke_width=1).shift(LEFT * 6 + RIGHT * i * 0.5)
                for i in range(15)
            ])
            
            # Token Counter
            counter_val = Integer(0)
            counter_label = Text("Tokens:", font_size=24).next_to(brain, UP, buff=1).shift(LEFT)
            counter_val.next_to(counter_label, RIGHT)
            counter_group = VGroup(counter_label, counter_val)
            
            self.play(FadeIn(docs), Write(counter_group))
            
            # Animate stream and counter
            self.play(
                docs.animate.move_to(brain.get_center()),
                counter_val.animate.set_value(1000000),
                run_time=4,
                rate_func=linear
            )
            self.play(FadeOut(docs))

        # Scene 2: Inside the Brain (Context Rot)
        with self.voiceover(text="But there is a catch. Just because a model can swallow a million words, doesn't mean it can digest them. As the input grows, a phenomenon called 'Context Rot' sets in. The model's attention gets diluted, drowning in the noise of its own memory.") as tracker:
            update_caption("Context Rot: Attention degrades as input size grows")
            
            # Zoom effect (scale up brain)
            self.play(
                brain.animate.scale(2.5).move_to(ORIGIN),
                FadeOut(header), FadeOut(counter_group)
            )
            
            # Chaos animation
            chaos_lines = VGroup(*[
                Line(
                    brain_circle.point_from_proportion((i%20)/20), 
                    brain_circle.point_from_proportion((i*3 % 20)/20), 
                    color=GREY, stroke_width=1, stroke_opacity=0.5
                )
                for i in range(40)
            ]).scale(2.5) # Match scale
            
            rot_label = Text("CONTEXT ROT", color=RED, font_size=60).move_to(ORIGIN)
            warning_box = SurroundingRectangle(rot_label, color=RED, buff=0.2)
            
            self.play(Transform(brain_network, chaos_lines))
            self.play(
                brain_circle.animate.set_color(GREY),
                FadeIn(rot_label), Create(warning_box)
            )
            self.wait(1)

        self.play(FadeOut(brain), FadeOut(rot_label), FadeOut(warning_box), FadeOut(brain_network))

        # Scene 3: Simple vs Dense Tasks
        with self.voiceover(text="It's not that the models simply forget. They can easily find a specific password hidden in a book—that's the 'needle in a haystack' problem. But ask them to track a complex plot or connect an idea from page one to page five hundred? That's where they crumble.") as tracker:
            update_caption("Simple Retrieval vs. Dense Reasoning")
            
            # Left side: Simple
            left_panel = VGroup()
            haystack_simple = VGroup(*[Line(ORIGIN, UP*0.5, color=YELLOW).rotate(i) for i in range(0, 360, 10)])
            needle = Line(ORIGIN, UP*0.5, color=RED, stroke_width=4)
            haystack_simple.add(needle)
            haystack_simple.move_to(LEFT * 3.5)
            
            label_simple = Text("Needle in Haystack", font_size=24).next_to(haystack_simple, UP)
            checkmark = Text("✔", color=GREEN, font_size=48).next_to(haystack_simple, DOWN)
            
            left_panel.add(haystack_simple, label_simple)
            
            # Right side: Dense
            right_panel = VGroup()
            haystack_dense = VGroup(*[Line(ORIGIN, UP*0.5, color=YELLOW).rotate(i) for i in range(0, 360, 5)])
            threads = VGroup(*[Line(ORIGIN, UP*0.5, color=RED, stroke_width=2).rotate(i) for i in range(0, 360, 15)])
            haystack_dense.add(threads)
            haystack_dense.move_to(RIGHT * 3.5)
            
            label_dense = Text("Dense Reasoning", font_size=24).next_to(haystack_dense, UP)
            x_mark = Text("✘", color=RED, font_size=48).next_to(haystack_dense, DOWN)
            
            right_panel.add(haystack_dense, label_dense)
            
            self.play(Create(left_panel), Create(right_panel))
            self.play(FadeIn(checkmark))
            self.wait(1)
            self.play(FadeIn(x_mark))

        self.play(FadeOut(left_panel), FadeOut(right_panel), FadeOut(checkmark), FadeOut(x_mark))

        # Scene 4: The Graph
        with self.voiceover(text="This degradation isn't subtle. On tasks that require reasoning across the whole text, performance doesn't just dip—it dives off a cliff. The model's physical context window is huge, but its effective reasoning window is surprisingly small.") as tracker:
            update_caption("Performance crashes on dense tasks despite large context")
            
            ax = Axes(
                x_range=[0, 10, 1],
                y_range=[0, 100, 20],
                x_length=8,
                y_length=5,
                axis_config={"include_numbers": False},
                tips=True
            ).center()
            
            x_label = Text("Tokens (Log Scale)", font_size=20).next_to(ax.x_axis, DOWN)
            y_label = Text("Accuracy", font_size=20).next_to(ax.y_axis, LEFT).rotate(90 * DEGREES)
            
            # Labels for log scale
            x_ticks = VGroup(
                Text("8k", font_size=16).next_to(ax.coords_to_point(1,0), DOWN),
                Text("128k", font_size=16).next_to(ax.coords_to_point(5,0), DOWN),
                Text("1M", font_size=16).next_to(ax.coords_to_point(9,0), DOWN)
            )
            
            retrieval_line = ax.plot_line_graph(
                x_values=[0, 2, 5, 9], y_values=[98, 97, 96, 95], line_color=GREEN, add_vertex_dots=False
            )["line_graph"]
            
            reasoning_line = ax.plot_line_graph(
                x_values=[0, 2, 4, 6, 9], y_values=[95, 90, 60, 10, 5], line_color=RED, add_vertex_dots=False
            )["line_graph"]
            
            label_ret = Text("Retrieval", color=GREEN, font_size=20).next_to(retrieval_line, UP, buff=0).shift(RIGHT*2)
            label_rea = Text("Deep Reasoning", color=RED, font_size=20).next_to(reasoning_line, DOWN, buff=0).shift(LEFT*1)
            
            self.play(Create(ax), Write(x_label), Write(y_label), Write(x_ticks))
            self.play(Create(retrieval_line), Write(label_ret))
            self.play(Create(reasoning_line), Write(label_rea))

        # Keep the axes for later scene 8, but fade out lines for now or just fade all out
        # Storyboard implies transition to hardware analogy, then back to graph later.
        # I'll fade everything out to clean slate.
        graph_group = VGroup(ax, x_label, y_label, x_ticks, retrieval_line, reasoning_line, label_ret, label_rea)
        self.play(FadeOut(graph_group))

        # Scene 5: Hardware Analogy (RAM vs HDD)
        with self.voiceover(text="Think of it like a computer. Trying to stuff a million-token prompt into the model's active attention is like trying to load a terabyte database entirely into your RAM. It's inefficient, expensive, and frankly, overwhelming.") as tracker:
            update_caption("Analogy: Loading a massive DB into small RAM")
            
            ram_chip = Square(side_length=2, color=BLUE, fill_opacity=0.2).shift(LEFT * 3)
            ram_text = Text("RAM\n(Context)", font_size=20).move_to(ram_chip)
            
            hdd_stack = VGroup(*[
                Rectangle(width=2, height=0.5, color=GREY, fill_opacity=0.5).shift(UP * i * 0.1)
                for i in range(10)
            ]).shift(RIGHT * 3)
            hdd_text = Text("Hard Drive\n(Prompt)", font_size=20).next_to(hdd_stack, UP)
            
            self.play(Create(ram_chip), Write(ram_text), Create(hdd_stack), Write(hdd_text))
            
            # Animation: Move HDD to RAM
            self.play(hdd_stack.animate.move_to(ram_chip), run_time=2)
            
            # Overload effect
            self.play(
                ram_chip.animate.set_color(RED),
                Wiggle(ram_chip),
                Flash(ram_chip, color=RED, line_length=0.5)
            )

        self.play(FadeOut(ram_chip), FadeOut(ram_text), FadeOut(hdd_stack), FadeOut(hdd_text))

        # Scene 6: Out of Core
        with self.voiceover(text="Computer science solved this decades ago with 'out-of-core' algorithms. If a dataset is too big for memory, you don't crash. You leave the data on the disk, and you fetch only the chunks you need, when you need them.") as tracker:
            update_caption("Solution: Out-of-Core Processing (Chunking)")
            
            # Reset visual positions
            ram_chip = Square(side_length=2, color=BLUE, fill_opacity=0.2).shift(LEFT * 3)
            ram_text = Text("RAM", font_size=20).move_to(ram_chip)
            
            hdd_stack = VGroup(*[
                Rectangle(width=2, height=0.5, color=GREY, fill_opacity=0.5).shift(RIGHT * 3 + UP * (i-2) * 0.6)
                for i in range(5)
            ])
            hdd_text = Text("Disk", font_size=20).next_to(hdd_stack, UP)
            
            title_ooc = Text("Out-of-Core Algorithm", color=YELLOW, font_size=36).to_edge(UP)
            
            self.play(Create(ram_chip), Write(ram_text), Create(hdd_stack), Write(hdd_text), Write(title_ooc))
            
            # Packet animation
            for i in range(3):
                packet = hdd_stack[i].copy().set_color(YELLOW)
                self.play(packet.animate.move_to(ram_chip), run_time=0.8)
                self.play(FadeOut(packet), run_time=0.2) # "Processed"

        self.play(FadeOut(ram_chip), FadeOut(ram_text), FadeOut(hdd_stack), FadeOut(hdd_text), FadeOut(title_ooc))

        # Scene 7: Inference Time Scaling (Robot Hand)
        with self.voiceover(text="This is the core idea behind 'Inference-Time Scaling.' Instead of feeding the prompt into the neural network, we treat the prompt as an external environment. The model uses code to browse the text, read specific snippets, and reason iteratively.") as tracker:
            update_caption("Inference-Time Scaling: Prompt as External Environment")
            
            # Scroll/Environment
            scroll = Rectangle(width=4, height=6, color=WHITE, fill_opacity=0.1).shift(LEFT * 3)
            lines = VGroup(*[Line(LEFT*1.5, RIGHT*1.5, color=GREY).shift(UP*2.5 - DOWN*i*0.2) for i in range(20)]).move_to(scroll)
            env_label = Text("Environment\n(The Prompt)", font_size=24).next_to(scroll, UP)
            
            # Code/Interpreter
            code_window = Code(
                code_string="data = env.read(0, 1000)\nsummary = model.summarize(data)\nnext_chunk = env.read(5000, 6000)",
                language="python",
                background="window"
            ).shift(RIGHT * 3)
            
            agent_label = Text("Agent / Interpreter", font_size=24).next_to(code_window, UP)
            
            arrow = Arrow(start=code_window.get_left(), end=scroll.get_right(), color=YELLOW)
            
            self.play(Create(scroll), Create(lines), Write(env_label))
            self.play(Write(code_window), Write(agent_label))
            self.play(GrowArrow(arrow))

        self.play(FadeOut(scroll), FadeOut(lines), FadeOut(env_label), FadeOut(code_window), FadeOut(agent_label), FadeOut(arrow))

        # Scene 8: Solution Graph (Recursive Model)
        with self.voiceover(text="The result? We stop the rot. By processing information in manageable pieces, we can extend the reasoning capabilities of models by orders of magnitude. It turns out the secret to reading a long book isn't a bigger brain—it's learning how to turn the pages.") as tracker:
            update_caption("RLMs maintain accuracy regardless of length")
            
            # Recreate graph basics
            ax = Axes(
                x_range=[0, 10, 1],
                y_range=[0, 100, 20],
                x_length=8,
                y_length=5,
                axis_config={"include_numbers": False},
                tips=True
            ).center()
            
            x_label = Text("Tokens (Log Scale)", font_size=20).next_to(ax.x_axis, DOWN)
            y_label = Text("Accuracy", font_size=20).next_to(ax.y_axis, LEFT).rotate(90 * DEGREES)
            x_ticks = VGroup(
                Text("8k", font_size=16).next_to(ax.coords_to_point(1,0), DOWN),
                Text("128k", font_size=16).next_to(ax.coords_to_point(5,0), DOWN),
                Text("1M", font_size=16).next_to(ax.coords_to_point(9,0), DOWN)
            )

            # Red line again
            reasoning_line = ax.plot_line_graph(
                x_values=[0, 2, 4, 6, 9], y_values=[95, 90, 60, 10, 5], line_color=RED, add_vertex_dots=False
            )["line_graph"]
            
            # Blue line (Recursive)
            recursive_line = ax.plot_line_graph(
                x_values=[0, 2, 4, 6, 9], y_values=[96, 95, 94, 95, 93], line_color=BLUE, add_vertex_dots=False
            )["line_graph"]
            
            label_base = Text("Base Model", color=RED, font_size=20).next_to(reasoning_line, DOWN, buff=0).shift(LEFT*1)
            label_rlm = Text("Recursive Model", color=BLUE, font_size=20).next_to(recursive_line, UP, buff=0).shift(RIGHT*2)
            
            self.play(Create(ax), Write(x_label), Write(y_label), Write(x_ticks))
            self.play(Create(reasoning_line), Write(label_base))
            self.play(Create(recursive_line), Write(label_rlm))
            
            # Sparkles/Emphasis
            self.play(Indicate(recursive_line, color=YELLOW, scale_factor=1.1))

        self.play(FadeOut(ax), FadeOut(x_label), FadeOut(y_label), FadeOut(x_ticks), FadeOut(reasoning_line), FadeOut(recursive_line), FadeOut(label_base), FadeOut(label_rlm))

        # Final Scene: Closing
        with self.voiceover(text="To recap: Physical context capacity does not equal effective reasoning capacity; models suffer from 'context rot' as inputs grow. The proposed solution shifts focus from architectural changes to inference-time compute scaling. Next time, we will explore Recursive Language Models (RLMs): The Core Architecture.") as tracker:
            update_caption("Coming Next: The RLM Architecture")
            
            takeaway_title = Text("Key Takeaways", font_size=36, color=BLUE).to_edge(UP)
            takeaways = BulletedList(
                "Physical context != Effective reasoning",
                "Context Rot degrades dense tasks",
                "Solution: Inference-time scaling",
                "Treat prompt as external environment",
                font_size=24
            ).center()
            
            next_teaser = Text("Next: Part 2 - The Core Architecture", color=YELLOW, font_size=32).next_to(takeaways, DOWN, buff=1)
            
            self.play(Write(takeaway_title), Write(takeaways))
            self.play(FadeIn(next_teaser))
            self.wait(tracker.duration - 5)

        self.play(FadeOut(takeaway_title), FadeOut(takeaways), FadeOut(next_teaser), FadeOut(self.caption_bg), FadeOut(self.caption_text))

