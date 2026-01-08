import os
import json
from openai import OpenAI
import os
from dotenv import load_dotenv


# ===================================================================
# CONFIG
# ===================================================================

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai_client = OpenAI(api_key=OPENAI_API_KEY)

# ===================================================================
# STEP 1: TEACHER PASS (OpenAI GPT-4o) - ENHANCED VERSION
# ===================================================================

def create_teaching_plan(user_query: str) -> dict:
    """
    Uses OpenAI to create a DEEPLY DETAILED structured teaching plan.
    
    Returns:
        dict: Structured teaching plan with sections, explanations, visuals, and equations
    """
    print("👨‍🏫 Creating teaching plan with OpenAI...")
    
    system_prompt = """You are an EXPERT EDUCATOR and curriculum designer specializing in creating DEEPLY DETAILED visual, animated educational content.

Your task is to create a COMPREHENSIVE, HIGHLY DETAILED TEACHING PLAN for the given topic that will be used to generate an educational animation.

===================================================================
CRITICAL REQUIREMENT: EXTREME DETAIL LEVEL
===================================================================

You must provide FAR MORE detail than typical educational content:

BAD (Too vague):
"Explanation: The model uses attention to focus on relevant parts"
"Key point: Attention is important"

GOOD (Detailed enough):
"Explanation: The attention mechanism computes three matrices: Query (Q), Key (K), and Value (V). For each input token, we calculate attention scores by taking the dot product of Q with all K matrices, then apply softmax to get weights between 0 and 1. These weights determine how much each token should influence the output. For example, in the sentence 'The cat sat on the mat', when processing 'sat', the attention might be: 'cat':0.6, 'mat':0.3, 'The':0.05, 'on':0.05, giving highest weight to the subject."

EXCELLENT (What we need):
"Explanation: The attention mechanism is the core innovation that allows transformers to process sequences without recurrence. Here's the step-by-step process:

Step 1: Linear Projections
- Input embeddings (each token is a 512-dim vector) pass through three learned weight matrices: W_Q (Query), W_K (Key), W_V (Value)
- For the word 'cat' with embedding [0.2, -0.5, 0.8, ...], we compute:
  * Q_cat = [0.2, -0.5, 0.8, ...] × W_Q → produces query vector [0.4, 0.1, -0.2, ...]
  * K_cat = [0.2, -0.5, 0.8, ...] × W_K → produces key vector [0.3, -0.4, 0.6, ...]
  * V_cat = [0.2, -0.5, 0.8, ...] × W_V → produces value vector [0.5, 0.2, -0.1, ...]

Step 2: Attention Score Calculation
- For token 'sat' to attend to 'cat', we calculate: score = Q_sat · K_cat / √d_k
- Example: Q_sat = [0.3, 0.2, -0.1, ...], K_cat = [0.3, -0.4, 0.6, ...]
- Dot product: (0.3)(0.3) + (0.2)(-0.4) + (-0.1)(0.6) + ... = 0.45
- Divide by √64 = 8: 0.45/8 = 0.056
- Repeat this for ALL tokens in the sequence

Step 3: Softmax Normalization
- Raw scores for 'sat' attending to all words: {'The':0.02, 'cat':0.056, 'sat':0.08, 'on':0.015, 'the':0.01, 'mat':0.03}
- Apply softmax: exp(scores) / sum(exp(scores))
- Normalized: {'The':0.05, 'cat':0.35, 'sat':0.40, 'on':0.08, 'the':0.05, 'mat':0.12}
- These sum to 1.0 and represent attention weights

Step 4: Weighted Sum
- Output for 'sat' = 0.05×V_The + 0.35×V_cat + 0.40×V_sat + 0.08×V_on + 0.05×V_the + 0.12×V_mat
- This creates a context-aware representation of 'sat' that incorporates information from all relevant words

Key Insight: The model LEARNS what to attend to. In training, it discovers that verbs should attend strongly to their subjects and objects, adjectives to nouns they modify, etc."

===================================================================
PEDAGOGICAL STRUCTURE & PROGRESSION
===================================================================

**SCAFFOLDING PRINCIPLE:**
Within each section, progress from simple intuition → detailed mechanics → technical depth.
Start with "what" and "why" before diving into "how".

1. SECTION BREAKDOWN
   - 3-6 sections, each focused on ONE major concept
   - Each section needs 5-8 paragraphs of explanation (not 2-3!)
   - **Within each section, follow this progression:**
     * Start with a simple, intuitive explanation (1-2 paragraphs)
     * Build to the core mechanism with concrete examples (2-3 paragraphs)
     * Add technical depth with mathematics and edge cases (2-3 paragraphs)
   - Include worked examples with SPECIFIC numbers
   - Show calculation steps explicitly
   - **Always explain the intuition BEFORE the math**

2. KEY POINTS (Must be substantial)
   - Each key point should be a complete sentence or two
   - Include numerical examples: "With batch size 32, this creates 992 negative pairs"
   - Explain WHY, not just WHAT: "We use softmax (not sigmoid) because we need probabilities that sum to 1"
   - **Order key points from fundamental to advanced**

3. WORKED EXAMPLES (MANDATORY for each section)
   - Show concrete input and output
   - Walk through calculations step-by-step
   - Use realistic numbers
   - Example: "Input: [2.3, -1.5, 0.8] → After ReLU: [2.3, 0, 0.8]"
   - **Start with a simple example, then show a more complex variation**

4. COMMON STUDENT QUESTIONS
   - For each section, anticipate 3-5 questions students ask
   - Provide detailed answers
   - Example: "Q: Why divide by √d_k? A: To prevent dot products from getting too large when dimension is high, which would cause softmax gradients to vanish. With d_k=64, a dot product could reach ±64 in magnitude, making softmax outputs near 0 or 1, but dividing by 8 keeps it in range ±8."

===================================================================
VISUAL SPECIFICATIONS (Must be extremely specific)
===================================================================

GOOD VISUAL DESCRIPTION:
"Type: Matrix visualization
Description: Show 3×4 matrix A on left, 4×2 matrix B on right. Highlight row 1 of A (in blue) and column 1 of B (in red). Animate the element-wise multiplication: A[1,1]×B[1,1] + A[1,2]×B[2,1] + A[1,3]×B[3,1] + A[1,4]×B[4,1], showing each product appearing below, then summing to produce C[1,1]=7.2. Use color coding: positive numbers in green, negative in red. Label dimensions clearly."

BAD VISUAL DESCRIPTION:
"Show matrix multiplication"

ANIMATION CHOREOGRAPHY:
- Specify EXACT sequence: "First fade in A (1s), then B (1s), then highlight row (0.5s), then..."
- Timing: "Show each multiplication for 0.8s before next"
- Camera movement: "Zoom into highlighted region, then zoom out"
- Color scheme: "Use blue for queries, red for keys, green for values"
- **For attention mechanisms specifically:**
  * Use curved arrows or arcs ABOVE/BELOW elements for connections
  * Never specify straight lines that would pass through multiple objects
  * Example: "Draw curved arrows from word to word, arcing above the sentence"

===================================================================
EQUATION REQUIREMENTS
===================================================================

For EACH equation, provide:
1. LaTeX notation
2. Plain English explanation
3. Variable definitions with units/dimensions
4. Numerical example showing calculation
5. When to show vs derive
6. **Intuitive interpretation before formula**

Example:
{
  "intuition": "Attention is like a weighted average - we decide how much to 'pay attention' to each word based on relevance",
  "latex": "\\text{Attention}(Q, K, V) = \\text{softmax}\\left(\\frac{QK^T}{\\sqrt{d_k}}\\right)V",
  "description": "Scaled dot-product attention formula",
  "variable_definitions": {
    "Q": "Query matrix, shape (seq_len, d_k), e.g., (10, 64)",
    "K": "Key matrix, shape (seq_len, d_k), e.g., (10, 64)",
    "V": "Value matrix, shape (seq_len, d_v), e.g., (10, 64)",
    "d_k": "Dimension of key vectors, typically 64"
  },
  "numerical_example": "With seq_len=3, d_k=4: Q·K^T produces 3×3 matrix of attention scores, divide by √4=2, apply softmax row-wise, multiply by V",
  "show_derivation": true,
  "derivation_steps": [
    "Start with Q·K^T to get compatibility scores",
    "Scale by 1/√d_k to prevent large values",
    "Apply softmax to get probabilities",
    "Multiply by V to get weighted sum"
  ]
}

===================================================================
OUTPUT FORMAT
===================================================================

Return ONLY valid JSON:

{
  "title": "Clear, engaging title",
  "total_duration_estimate": "3-4 minutes",
  "sections": [
    {
      "section_number": 1,
      "heading": "Section title",
      "duration_estimate": "45-60 seconds",
      
      "explanation": "5-8 paragraphs with internal progression from simple to detailed. Start with intuition (paragraphs 1-2), build to mechanics (paragraphs 3-5), add technical depth (paragraphs 6-8). Include: what the concept is, why it matters, how it works step-by-step, numerical examples, edge cases, common variations. Minimum 500 words.",
      
      "key_points": [
        "Each point is 2-3 sentences with specific details and numbers",
        "Example: The attention mechanism computes O(n²) pairwise comparisons for sequence length n. With n=512, that's 262,144 comparisons per layer.",
        "Include WHY, not just WHAT"
      ],
      
      "worked_example": {
        "scenario": "Specific scenario description",
        "input": "Concrete input with numbers",
        "step_by_step": [
          "Step 1: Detailed calculation with numbers",
          "Step 2: Show intermediate result",
          "Step 3: Final output"
        ],
        "output": "Final result with interpretation"
      },
      
      "equations": [
        {
          "intuition": "Plain English explanation before the math",
          "latex": "Full LaTeX",
          "description": "What it computes",
          "variable_definitions": {
            "var": "definition with dimensions"
          },
          "numerical_example": "Concrete calculation",
          "show_derivation": true/false,
          "derivation_steps": ["step 1", "step 2"]
        }
      ],
      
      "visuals": [
        {
          "type": "graph|diagram|matrix|animation|3d_plot|timeline",
          "description": "Extremely specific description with positions, colors, labels, dimensions. For attention lines: use arcs or curved arrows, never straight lines through objects.",
          "animation_choreography": "Exact sequence: First X (2s), then Y (1.5s), then...",
          "key_elements": ["element 1 at position (x,y)", "element 2"],
          "color_scheme": {"concept_A": "blue", "concept_B": "red"}
        }
      ],
      
      "misconceptions_to_address": [
        {
          "misconception": "What students incorrectly think",
          "why_its_wrong": "Detailed explanation",
          "correct_understanding": "What they should think instead",
          "visual_clarification": "How to show this visually"
        }
      ],
      
      "common_student_questions": [
        {
          "question": "Specific question students ask",
          "answer": "Detailed answer with examples"
        }
      ],
      
      "transitions": {
        "from_previous": "How this builds on previous section",
        "to_next": "How this leads to next section"
      }
    }
  ],
  "key_takeaways": [
    "Detailed takeaway 1 with specific insight",
    "Detailed takeaway 2 with specific insight"
  ],
  "prerequisites": ["Concept with specificity"],
  "suggested_examples": ["Detailed example scenario"],
  "complexity_notes": "Notes on what makes this topic challenging and how to address it"
}

===================================================================
QUALITY CHECKLIST (Must meet ALL criteria)
===================================================================

□ Each section explanation is 500+ words with clear intuition → mechanics → depth progression
□ Every section has a worked example with numbers
□ Every equation has intuition + variable definitions + numerical example
□ Every visual has specific positions/colors/animation sequence
□ Visual descriptions for attention use arcs/curves, not straight lines through objects
□ Every misconception has a visual clarification strategy
□ At least 3 student questions answered per section
□ No vague language like "show how it works" or "explain the concept"
□ All examples use concrete numbers, not abstractions
□ Timing adds up to 3-4 minutes when paced naturally
□ Content progresses from accessible to technical within each section

Remember: This teaching plan will be converted directly to animation code. More detail = better animations. Start simple, build complexity naturally."""

    user_prompt = f"""Create a COMPREHENSIVE, DEEPLY DETAILED teaching plan for:

TOPIC: {user_query}

Requirements for MAXIMUM DETAIL:

1. EXPLAIN LIKE TEACHING A COURSE
   - Not just bullet points - full explanations
   - Multiple paragraphs per concept
   - **Within each section: Start with intuition, build to mechanics, add technical depth**
   - Step-by-step breakdowns
   - Concrete numerical examples

2. INCLUDE WORKED EXAMPLES
   - For EVERY major concept
   - Use specific numbers (e.g., "input: [2.3, -1.5, 0.8]")
   - Show intermediate calculations
   - Explain what each step does

3. ANTICIPATE STUDENT QUESTIONS
   - "Why do we use X instead of Y?"
   - "What happens if we change parameter Z?"
   - "How does this compare to approach W?"

4. SPECIFY EXACT VISUALS
   - Not "show a graph" but "line graph with x-axis: time (0-100s), y-axis: loss (0-10), showing exponential decay from 8.5 to 0.3, with key point at t=40s marked"
   - **For attention visualizations: Use curved arrows or arcs, never straight lines through multiple objects**

5. PROVIDE MATHEMATICAL DEPTH
   - Give intuition BEFORE formulas
   - Show derivations if relevant
   - Explain why formulas have that form
   - Progress from simple to complex

6. **SCAFFOLDING WITHIN EACH SECTION**
   - Paragraph 1-2: Simple explanation anyone can understand
   - Paragraph 3-5: How it actually works with examples
   - Paragraph 6-8: Technical details and mathematics

Think of this as creating lecture notes for a university course, not a Wikipedia summary.
Each section should take a learner from basic understanding to technical mastery.

Return ONLY the JSON teaching plan. Make it as detailed as possible - minimum 3000 words across all sections."""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=12000,  # Increased for longer responses
            response_format={"type": "json_object"}
        )
        
        # Get response content
        response_text = response.choices[0].message.content
        
        # Try to fix common JSON issues
        try:
            teaching_plan = json.loads(response_text)
        except json.JSONDecodeError as e:
            print(f"⚠️ Initial JSON parse failed: {e}")
            print("   Attempting to fix JSON formatting...")
            
            # Save the raw response for debugging
            with open("debug_raw_response.txt", "w") as f:
                f.write(response_text)
            print("   💾 Raw response saved to: debug_raw_response.txt")
            
            # Try to fix the JSON
            # Remove any markdown code blocks
            if "```" in response_text:
                response_text = response_text.split("```")[1]
                response_text = response_text.replace("json", "").strip()
            
            # Try parsing again
            teaching_plan = json.loads(response_text)
        
        # Validate structure
        if "title" not in teaching_plan or "sections" not in teaching_plan:
            raise ValueError("Invalid teaching plan structure")
        
        # Count total words for quality check
        total_words = 0
        for section in teaching_plan.get('sections', []):
            total_words += len(section.get('explanation', '').split())
        
        print(f"✅ Teaching plan created: {teaching_plan['title']}")
        print(f"   Sections: {len(teaching_plan['sections'])}")
        print(f"   Duration: {teaching_plan.get('total_duration_estimate', 'N/A')}")
        print(f"   Total words: {total_words}")
        
        if total_words < 1000:
            print(f"   ⚠️  Warning: Only {total_words} words - may lack detail\n")
        else:
            print(f"   ✅ Detail level: Good ({total_words} words)\n")
        
        return teaching_plan
        
    except Exception as e:
        print(f"❌ Error creating teaching plan: {e}")
        raise

# ===================================================================
# HELPER: Save Teaching Plan
# ===================================================================

def save_teaching_plan(teaching_plan: dict, filename: str = "teaching_plan.json"):
    """Save the teaching plan to a JSON file for inspection."""
    with open(filename, "w") as f:
        json.dump(teaching_plan, indent=2, fp=f)
    print(f"💾 Teaching plan saved to: {filename}\n")

# ===================================================================
# HELPER: Format Teaching Plan for Claude
# ===================================================================

def format_teaching_plan_for_claude(teaching_plan: dict) -> str:
    """
    Convert the teaching plan into a clear text format that Claude can use
    to generate Manim code.
    """
    formatted = f"""# TEACHING PLAN: {teaching_plan['title']}

Duration: {teaching_plan.get('total_duration_estimate', 'N/A')}

Prerequisites: {', '.join(teaching_plan.get('prerequisites', ['None specified']))}

Complexity Notes: {teaching_plan.get('complexity_notes', 'N/A')}

"""
    
    for section in teaching_plan['sections']:
        formatted += f"""
{'='*70}
SECTION {section['section_number']}: {section['heading']}
{'='*70}
Duration: {section.get('duration_estimate', 'N/A')}

DETAILED EXPLANATION:
{section['explanation']}

KEY POINTS:
"""
        for i, point in enumerate(section.get('key_points', []), 1):
            formatted += f"{i}. {point}\n"
        
        # Worked Example
        if section.get('worked_example'):
            we = section['worked_example']
            formatted += f"""
WORKED EXAMPLE:
Scenario: {we.get('scenario', 'N/A')}
Input: {we.get('input', 'N/A')}

Step-by-Step:
"""
            for i, step in enumerate(we.get('step_by_step', []), 1):
                formatted += f"  {i}. {step}\n"
            formatted += f"\nOutput: {we.get('output', 'N/A')}\n"
        
        # Equations
        if section.get('equations'):
            formatted += "\nEQUATIONS TO SHOW:\n"
            for eq in section['equations']:
                # Show intuition if present
                if eq.get('intuition'):
                    formatted += f"\nIntuition: {eq['intuition']}\n"
                
                formatted += f"Equation: {eq['latex']}\n"
                formatted += f"Description: {eq['description']}\n"
                
                if eq.get('variable_definitions'):
                    formatted += "Variables:\n"
                    for var, defn in eq['variable_definitions'].items():
                        formatted += f"  - {var}: {defn}\n"
                
                if eq.get('numerical_example'):
                    formatted += f"Example: {eq['numerical_example']}\n"
                
                if eq.get('show_derivation'):
                    formatted += "Derivation steps:\n"
                    for i, step in enumerate(eq.get('derivation_steps', []), 1):
                        formatted += f"  {i}. {step}\n"
        
        # Visuals
        if section.get('visuals'):
            formatted += "\nVISUALS REQUIRED:\n"
            for i, vis in enumerate(section['visuals'], 1):
                formatted += f"\nVisual {i}: [{vis['type'].upper()}]\n"
                formatted += f"Description: {vis['description']}\n"
                
                if vis.get('animation_choreography'):
                    formatted += f"Animation: {vis['animation_choreography']}\n"
                
                if vis.get('key_elements'):
                    formatted += "Key elements:\n"
                    for elem in vis['key_elements']:
                        formatted += f"  - {elem}\n"
                
                if vis.get('color_scheme'):
                    formatted += "Colors: " + str(vis['color_scheme']) + "\n"
        
        # Misconceptions
        if section.get('misconceptions_to_address'):
            formatted += "\nMISCONCEPTIONS TO ADDRESS:\n"
            for misc in section['misconceptions_to_address']:
                if isinstance(misc, dict):
                    formatted += f"❌ Misconception: {misc.get('misconception', 'N/A')}\n"
                    formatted += f"   Why wrong: {misc.get('why_its_wrong', 'N/A')}\n"
                    formatted += f"   ✅ Correct: {misc.get('correct_understanding', 'N/A')}\n"
                    formatted += f"   Visual fix: {misc.get('visual_clarification', 'N/A')}\n\n"
                else:
                    formatted += f"- {misc}\n"
        
        # Student Questions
        if section.get('common_student_questions'):
            formatted += "\nCOMMON STUDENT QUESTIONS:\n"
            for qa in section['common_student_questions']:
                formatted += f"Q: {qa.get('question', 'N/A')}\n"
                formatted += f"A: {qa.get('answer', 'N/A')}\n\n"
        
        # Transitions
        if section.get('transitions'):
            trans = section['transitions']
            if trans.get('from_previous'):
                formatted += f"← From previous: {trans['from_previous']}\n"
            if trans.get('to_next'):
                formatted += f"→ To next: {trans['to_next']}\n"
        
        formatted += "\n"
    
    formatted += f"""
{'='*70}
KEY TAKEAWAYS
{'='*70}
"""
    for i, takeaway in enumerate(teaching_plan.get('key_takeaways', []), 1):
        formatted += f"{i}. {takeaway}\n"
    
    if teaching_plan.get('suggested_examples'):
        formatted += "\nSUGGESTED EXAMPLES:\n"
        for example in teaching_plan['suggested_examples']:
            formatted += f"- {example}\n"
    
    return formatted