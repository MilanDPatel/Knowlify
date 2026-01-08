from manim import *
class FullEncryptionVideo(Scene):
	def construct(self):
		rectangle = RoundedRectangle(stroke_width = 8, stroke_color = WHITE, 
		fill_color = BLUE_B, width = 3.8, height = 1.5).shift(UP*2+LEFT*4)
		rectangle2 = RoundedRectangle(stroke_width = 8, stroke_color = WHITE, 
		fill_color = BLUE_B, width = 3.8, height = 2).shift(DOWN*2)

		message = MathTex("\\text{Hello, Amy!}").set_color_by_gradient(GREEN, PINK).set_height(0.5)
		message.move_to(rectangle.get_center())

		ciphertext = MathTex(
			r"& \text{A345DFE510}\\",
			r"& \text{C6DB34F8E7}\\"
		).set_color_by_gradient(GREEN, PINK)
		ciphertext.move_to(rectangle2.get_center())
		
		rect1 = Rectangle(height = 1.15, width = 4).shift(LEFT*4)
		rect2 = Rectangle(height = 1.15, width = 1.8).shift(RIGHT*4)
		christina = MathTex("\\text{Christina}").set_color(GREEN).set_height(0.6).shift(LEFT*4)
		amy = MathTex("\\text{Amy}").set_color(PINK).set_height(0.6).shift(RIGHT*4)
		christina.move_to(rect1.get_center())
		amy.move_to(rect2.get_center())

		self.play(Create(rect1), Write(christina), Create(rect2), Write(amy))
		self.wait(1)
		self.play(FadeIn(rectangle), Write(message))
		#self.play(Write(message))
		self.wait(1)
		self.play(rectangle.animate.shift(RIGHT*8), message.animate.shift(RIGHT*8), run_time = 2)
		self.wait(5)
		self.play(FadeOut(rect1), FadeOut(christina), FadeOut(rect2), FadeOut(amy))
		self.play(rectangle.animate.shift(LEFT*4), message.animate.shift(LEFT*4), run_time = 1)
		self.wait(2)
		down_arrow = Arrow(start=UP, end=DOWN)
		down_arrow.set_stroke(width=5)
		self.play(FadeIn(down_arrow))
		self.play(FadeIn(rectangle2), Write(ciphertext))
		self.wait(4)
		up_arrow = Arrow(start = DOWN, end = UP)
		up_arrow.set_stroke(width=5)
		self.play(FadeOut(down_arrow))
		self.play(FadeIn(up_arrow))
		self.wait(5)
		self.play(FadeOut(rectangle), FadeOut(message), FadeOut(rectangle2), FadeOut(ciphertext), FadeOut(up_arrow))	
		mathtext1 = MathTex("\\text{Public-key Encryption}").shift(UP*3)
		msg = MathTex("\\text{Message}").shift(LEFT*5, DOWN * 0.25)
		encrmsg = MathTex("\\text{Ciphertext}").shift(RIGHT*4.5, DOWN * 0.25)
		silvermsg = MathTex("\\text{Alice's public key}").shift(DOWN * 2)
		goldmsg = MathTex("\\text{Alice's private key}").shift(DOWN * 2)
		bob = MathTex("\\text{Bob}").set_color(BLUE).shift(UP*2.5)
		alice = MathTex("\\text{Alice}").set_color(RED).shift(UP*2.5)
		msg.scale(1.25)
		encrmsg.scale(1.25)
		silvermsg.scale(1.3)
		goldmsg.scale(1.3)
		bob.scale(2)
		alice.scale(2)
		mathtextlistkeys = MathTex(
			r"& \text{1. Public key}\\",
			r"& \boxed{\text{Hello}}\ \Longrightarrow \ \boxed{\text{A7CEF687D5}}\\",
			r"& \\",
			r"& \text{2. Private key}\\",
			r"& \boxed{\text{A7CEF687D5}} \ \Longrightarrow \ \boxed{\text{Hello}}"
		)
		# mathtextlistkeys.shift(DOWN*1)
		# Create the key shape using VMobject
		private_key = VMobject()
		public_key = VMobject()
		private_key.set_points_as_corners([
			[-1.5, 0, 0], [2.5, 0, 0], [2.5, -0.5, 0], [2, -0.5, 0], [2, -1, 0],
			[1.5, -1, 0], [1.5, -0.5, 0], [1, -0.5, 0], [1, -1, 0], [0.5, -1, 0],
			[0.5, -0.5, 0], [-1.5, -0.5, 0], [-1.5, 0, 0]
		])
		public_key.set_points_as_corners([
			[-1.5, 0, 0], [2.5, 0, 0], [2.5, -0.5, 0], [2, -0.5, 0], [2, -1, 0],
			[1.5, -1, 0], [1.5, -0.5, 0], [1, -0.5, 0], [1, -1, 0], [0.5, -1, 0],
			[0.5, -0.5, 0], [-1.5, -0.5, 0], [-1.5, 0, 0]
		])
		#	[-1, 0, 0], [3, 0, 0], [3, -0.5, 0], [2.5, -0.5, 0], [2.5, -1, 0],
		#	[2, -1, 0], [2, -0.5, 0], [1.5, -0.5, 0], [1.5, -1, 0], [1, -1, 0],
		#	[1, -0.5, 0], [-1, -0.5, 0], [-1, 0, 0]
		#])
		# Create golden color gradient - private key
		golden_color = ["#FFD700", "#FFC700", "#FFB700", "#FFA700", "#FF9700"]

		# Create silver color gradient - public key
		silver_color = ["#C0C0C0", "#B0B0B0", "#A0A0A0", "#909090", "#808080"]

		private_key.set_color_by_gradient(*golden_color)
		private_key.set_fill(opacity=1)
		private_key.set_stroke(width=4, color=YELLOW)

		public_key.set_color_by_gradient(*silver_color)
		public_key.set_fill(opacity=1)
		public_key.set_stroke(width=4, color=BLUE)

		# Create the private key ring
		private_ring = Annulus(inner_radius=0.7, outer_radius=1.0, color=YELLOW, stroke_width=8)
		private_ring.set_color_by_gradient(*golden_color)
		private_ring.set_fill(opacity=1)
		private_ring.set_stroke(width=8, color=YELLOW)

		# Put the ring in the correct relative position
		private_ring.shift(LEFT * 2.25 + DOWN * 0.25)

		# Create the public key ring
		public_ring = Annulus(inner_radius=0.7, outer_radius=1.0, color=YELLOW, stroke_width=8)
		public_ring.set_color_by_gradient(*silver_color)
		public_ring.set_fill(opacity=1)
		public_ring.set_stroke(width=8, color=BLUE)

		# Put the ring in the correct relative position
		#public_ring.shift(LEFT * 1.75 + DOWN * 0.25)
		public_ring.shift(LEFT * 2.25 + DOWN * 0.25)
		
		# Intro to Public-key encryption	

		self.play(Write(mathtext1))
		self.wait(3)
		self.play(Write(mathtextlistkeys[0]))
		self.wait(1)
		self.play(Write(mathtextlistkeys[3]))
		self.wait(3)
		self.play(Write(mathtextlistkeys[1]))
		self.wait(2)
		self.play(Write(mathtextlistkeys[2]))
		self.wait(1)
		self.play(Write(mathtextlistkeys[4]))
		self.wait(3)
		#self.clear()
		self.play(FadeOut(mathtext1), FadeOut(mathtextlistkeys)) # Fade out all objects

		# Bob and Alice Example
		silvermsg.set_color_by_gradient(*silver_color)
		goldmsg.set_color_by_gradient(*golden_color)

		# Show the public key
		self.play(Write(bob), Write(msg), Write(public_key), Write(public_ring), Write(encrmsg), Write(silvermsg))
		self.wait(4)
		
		self.play(FadeOut(public_key), FadeOut(public_ring), FadeOut(bob), FadeOut(msg), FadeOut(encrmsg), FadeOut(silvermsg))
		self.wait(1)

		# Show the private key
		msg = MathTex("\\text{Message}").shift(RIGHT*4.5, DOWN * 0.25)
		encrmsg = MathTex("\\text{Ciphertext}").shift(LEFT*5, DOWN * 0.25)
		msg.scale(1.25)
		encrmsg.scale(1.25)
		self.play(Write(alice), Write(encrmsg), Write(private_key), Write(private_ring), Write(msg), Write(goldmsg))
		self.wait(4)

		self.play(FadeOut(alice), FadeOut(encrmsg), FadeOut(private_key), FadeOut(private_ring), FadeOut(msg), FadeOut(goldmsg))
		self.wait(1)

		self.wait(2)
		# Display title
		title = MathTex("\\text{The RSA Algorithm}").shift(UP*3)
		self.play(Write(title))
		self.wait(3)
		basic_info = MathTex(
			r"& \text{Find very large positive integers }e,d,n\text{ s.t.}\\",
			r"& (m^e)^d \equiv m \pmod{n}, \ \text{where }0 \leq m < n"
		).shift(UP*1)
		description = MathTex(
			r"& \text{Public key: }(e,n)\\",
			r"& \text{Private key: }d\\",
			r"& \text{Message: }m"
		).shift(DOWN*1.5)
		description2 = MathTex(
			r"& \text{Encryption: } m^e \bmod{n} = c\\",
			r"&\\",
			r"& \text{Decryption: } c^d \bmod{n} = (m^e)^d \bmod{n} = m"
		).shift(DOWN*1.5)

		# Display public key, private key, message
		self.play(Write(basic_info), run_time = 4)
		self.wait(12)
		self.play(Write(description[0]))
		self.wait(1)
		self.play(Write(description[1]))
		self.wait(1)
		self.play(Write(description[2]))
		self.wait(2)
		self.play(FadeOut(description))
		self.wait(1)

		# Display encryption, description
		self.play(Write(description2[0]), Write(description2[1]))
		self.wait(3)
		self.play(Write(description2[2]))
		self.wait(3)
		self.play(FadeOut(basic_info), FadeOut(description2), FadeOut(title))
		#self.play(FadeOut(title))

		# Explain key generation
		section = MathTex("\\text{Key generation}").shift(UP*3)
		steps = MathTex(
			r"& \text{1. Choose 2 large prime numbers }p \text{ and } q\\",
			r"& \quad \quad n=pq\\",
			r"& \text{2. Compute }\lambda(n)=\text{lcm}(p-1,q-1)\\",
			r"& \text{3. Choose }e\text{ s.t. }1<e<\lambda(n),\ \gcd(e,\lambda(n))=1\\",
			r"& \text{4. Find }d\text{ by solving }de\equiv 1 \pmod{\lambda(n)}"
		)
		self.play(Write(section))
		self.wait(1)
		self.play(Write(steps[0]))
		self.play(Write(steps[1]))
		self.wait(2)
		self.play(Write(steps[2]))
		self.wait(8)
		self.play(Write(steps[3]))
		self.wait(5)
		self.play(Write(steps[4]))
		self.wait(8)
		self.play(FadeOut(steps), FadeOut(section))
		self.wait(1)
		start_proof = MathTex("\\text{Proof of Correctness}").scale(1.5)
		self.play(Write(start_proof))
		self.wait(2)
		self.play(FadeOut(start_proof))

		# Show proof of correctness
		theorem = MathTex("(m^e)^d \equiv m \pmod{pq}").shift(UP*3)
		arrow = MathTex("\Longleftrightarrow").shift(UP*3)
		equiv = MathTex(
			r"& (m^e)^d \equiv m \pmod{p}\\",
			r"& (m^e)^d \equiv m \pmod{q}"
		).shift(UP*3, RIGHT*3)
		self.play(Write(theorem))
		self.wait(4)
		self.play(theorem.animate.shift(LEFT * 3))
		self.play(Write(arrow), Write(equiv))
		self.wait(5)
		proof1 = MathTex(
			r"& \text{1. }ed\equiv 1 \pmod{\text{lcm}(p-1,q-1)}\\",
			r"& \Longrightarrow ed - 1 = k_1(p-1)=k_2(q-1)\text{ for some }k_1,k_2\in\mathbb{Z}\\",
			r"& \text{2. }m\equiv 0 \pmod{p} \Longrightarrow (m^e)^d \equiv (0^e)^d \equiv 0 \pmod{p}\\",
			r"& \\",
			r"& \quad m\not\equiv 0 \pmod{p} \Longrightarrow \gcd(m,p)=1\\",
			r"& \quad \text{Use Fermat's Little Theorem: }m^{p-1} \equiv 1 \pmod{p}"
		).shift(DOWN*0.5)
		self.play(Write(proof1[0]), run_time = 3)
		self.play(Write(proof1[1]), run_time = 3)
		self.wait(4)
		self.play(Write(proof1[2]), run_time = 4)
		self.play(Write(proof1[3]))
		self.play(Write(proof1[4]), run_time = 2.5)
		self.play(Write(proof1[5]), run_time = 2.5)
		self.wait(2)
		self.play(FadeOut(proof1))
		#last_line = MathTex("\quad (m^{e})^d \equiv m^{ed} \equiv m^{ed-1}m").shift(UP*1.5, LEFT * 1)
		last_bunch = MathTex(
			r"(m^{e})^d \equiv m^{ed} & \equiv m^{ed-1}m\\",
			r"& \equiv m^{k_1(p-1)}m\\",
			r"& \equiv (m^{p-1})^{k_1}m\\",
			r"& \equiv 1^{k_1}m\\",
			r"& \equiv m \pmod{p}"
		).shift(DOWN * 0.5)
		proof2 = MathTex(
			r"& \text{3. }m\equiv 0 \pmod{q} \Longrightarrow (m^e)^d \equiv (0^e)^d \equiv 0 \pmod{q}\\",
			r"& \\",
			r"& \quad m\not\equiv 0 \pmod{q} \Longrightarrow \gcd(m,q)=1\\",
			r"& \quad \text{Use Fermat's Little Theorem: }m^{q-1} \equiv 1 \pmod{q}\\",
		).shift(DOWN*0.5)
		last_bunch2 = MathTex(
			r"(m^{e})^d \equiv m^{ed} &\equiv m^{ed-1}m\\",
			r"& \equiv m^{k_2(q-1)}m\\",
			r"& \equiv (m^{q-1})^{k_2}m\\",
			r"& \equiv 1^{k_2}m\\",
			r"& \equiv m \pmod{q}"
		).shift(DOWN*0.5)
		#self.play(Write(last_line))	
		#self.wait(1)
		self.play(Write(last_bunch[0]))
		self.play(Write(last_bunch[1]))
		self.play(Write(last_bunch[2]))
		self.play(Write(last_bunch[3]))
		self.play(Write(last_bunch[4]))
		self.wait(2)
		self.play(FadeOut(last_bunch))
		self.play(Write(proof2[0]))
		self.play(Write(proof2[1]))
		self.play(Write(proof2[2]))
		self.play(Write(proof2[3]))
		self.wait(3)
		self.play(FadeOut(proof2))
		self.play(Write(last_bunch2[0]))
		self.play(Write(last_bunch2[1]))
		self.play(Write(last_bunch2[2]))
		self.play(Write(last_bunch2[3]))
		self.play(Write(last_bunch2[4]))
		self.wait(3)
		self.play(FadeOut(last_bunch2), FadeOut(theorem), FadeOut(arrow), FadeOut(equiv))
		self.wait(1)
		# Summarize video
		list = MathTex(
			r"& \text{1. Public-key encryption}\\",
			r"& \quad\quad -\text{public key for encryption}\\",
			r"& \quad\quad -\text{private key for decryption}\\",
			r"&\\",
			r"& \text{2. The RSA Algorithm}\\",
			r"& \quad \quad -\text{a public-key cryptosystem}"
		).shift(UP*1)
		self.play(Write(list[0]))
		self.play(Write(list[4]))
		self.wait(1)
		self.play(Write(list[1]))
		self.play(Write(list[2]), Write(list[3]))
		self.wait(2)
		self.play(Write(list[5]))
		self.wait(1)
		self.play(FadeOut(list))		

		# Replay part of the intro animation
		# rectangle = RoundedRectangle(stroke_width = 8, stroke_color = WHITE, 
		# fill_color = BLUE_B, width = 3.8, height = 1.5).shift(UP*2+LEFT*4)

		#message = MathTex("\\text{Hello, Amy!}").set_color_by_gradient(GREEN, PINK).set_height(0.5)
		#message.move_to(rectangle.get_center())
		
		#rect1 = Rectangle(height = 1.15, width = 4).shift(LEFT*4)
		#rect2 = Rectangle(height = 1.15, width = 1.8).shift(RIGHT*4)
		#christina = MathTex("\\text{Christina}").set_color(GREEN).set_height(0.6).shift(LEFT*4)
		#amy = MathTex("\\text{Amy}").set_color(PINK).set_height(0.6).shift(RIGHT*4)
		#christina.move_to(rect1.get_center())
		#amy.move_to(rect2.get_center())
		
		rectangle.shift(LEFT*4)
		message.move_to(rectangle.get_center())
		self.play(Create(rect1), Write(christina), Create(rect2), Write(amy))
		self.wait(1)
		self.play(FadeIn(rectangle), Write(message))
		self.wait(1)
		self.play(rectangle.animate.shift(RIGHT*8), message.animate.shift(RIGHT*8), run_time = 2)
		self.wait(3)
		self.play(FadeOut(rectangle), FadeOut(message), FadeOut(christina), FadeOut(amy), FadeOut(rect1), FadeOut(rect2))
		self.wait(1)