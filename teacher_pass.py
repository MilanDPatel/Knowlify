import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# ===================================================================
# CONFIG
# ===================================================================

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# ===================================================================
# STEP 1: TEACHER PASS (OpenAI GPT-4o)
# ===================================================================

def create_teaching_plan(user_query: str) -> dict:
    """
    Uses OpenAI to create a structured teaching plan.
    
    Returns:
        dict: Structured teaching plan with sections, explanations, visuals, and equations
    """
    print("👨‍🏫 Creating teaching plan with OpenAI...")
    
    system_prompt = """You are an expert educator and curriculum designer specializing in creating visual, animated educational content.

Your task is to create a STRUCTURED TEACHING PLAN for the given topic that will be used to generate an educational animation.

CRITICAL REQUIREMENTS:

1. PEDAGOGICAL STRUCTURE
   - Break the topic into logical sections (3-6 sections ideal)
   - Each section should build on previous ones
   - Start with motivation/problem, then explain solution
   - Address common misconceptions explicitly
   - End with synthesis or application

2. VISUAL SPECIFICATIONS
   - For EACH section, specify exact visuals needed
   - Be specific: "Graph of accuracy vs epoch" not just "graph"
   - Include animation suggestions: "fade in", "morph", "highlight"
   - Specify what should appear sequentially vs simultaneously

3. EQUATION REQUIREMENTS
   - List ALL equations that should appear
   - Use LaTeX notation (will be rendered as r"..." in Python)
   - Specify when equations should be shown vs derived step-by-step
   - Include variable definitions

4. MISCONCEPTION AWARENESS
   - Identify common student confusions
   - Suggest visual clarifications
   - Note what NOT to do

5. TIMING GUIDANCE
   - Suggest approximate duration for each section
   - Mark which parts need more explanation vs quick transitions
   - Identify key moments that need pauses for comprehension

OUTPUT FORMAT:
You MUST return ONLY valid JSON in this exact structure:

{
  "title": "Clear, engaging title",
  "total_duration_estimate": "2-3 minutes",
  "sections": [
    {
      "section_number": 1,
      "heading": "Section title",
      "duration_estimate": "30-45 seconds",
      "explanation": "Clear explanation of concept (2-3 sentences)",
      "key_points": [
        "Bullet point 1",
        "Bullet point 2"
      ],
      "equations": [
        {
          "latex": "E = mc^2",
          "description": "Energy-mass equivalence",
          "show_derivation": false
        }
      ],
      "visuals": [
        {
          "type": "graph|diagram|matrix|timeline|comparison|animation",
          "description": "Specific description of what to show",
          "animation_notes": "How to animate this (fade in, morph, etc.)"
        }
      ],
      "misconceptions_to_address": [
        "Common misunderstanding and how to clarify"
      ],
      "transitions": {
        "from_previous": "How this connects to previous section",
        "to_next": "How this leads to next section"
      }
    }
  ],
  "key_takeaways": [
    "Main lesson 1",
    "Main lesson 2"
  ],
  "prerequisites": [
    "Concept student should know"
  ],
  "suggested_examples": [
    "Concrete example to illustrate concept"
  ]
}

EXAMPLES OF GOOD VISUAL SPECIFICATIONS:
✓ "3D plot showing loss surface with gradient descent path animated"
✓ "Side-by-side comparison: RNN (left) vs Transformer (right) processing sequence"
✓ "Matrix multiplication visualization with Q, K, V highlighted in different colors"
✓ "Timeline from 1990-2020 showing evolution of architectures"

EXAMPLES OF BAD VISUAL SPECIFICATIONS:
✗ "Show how it works"
✗ "Graph"
✗ "Animation of the concept"

Remember: The goal is to create a plan so detailed that a code generator can produce the exact animation without making pedagogical decisions."""

    user_prompt = f"""Create a comprehensive teaching plan for the following topic:

TOPIC: {user_query}

Consider:
- What is the core problem or motivation?
- What are the key concepts that must be explained?
- What is the logical order of presentation?
- What visuals will make abstract concepts concrete?
- What equations are essential?
- What do students typically misunderstand about this?

Return ONLY the JSON teaching plan. No markdown, no extra text."""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            response_format={"type": "json_object"}
        )
        
        teaching_plan = json.loads(response.choices[0].message.content)
        
        # Validate structure
        if "title" not in teaching_plan or "sections" not in teaching_plan:
            raise ValueError("Invalid teaching plan structure")
        
        print(f"✅ Teaching plan created: {teaching_plan['title']}")
        print(f"   Sections: {len(teaching_plan['sections'])}")
        print(f"   Duration: {teaching_plan.get('total_duration_estimate', 'N/A')}\n")
        
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

"""
    
    for section in teaching_plan['sections']:
        formatted += f"""
## SECTION {section['section_number']}: {section['heading']}
Duration: {section.get('duration_estimate', 'N/A')}

Explanation:
{section['explanation']}

Key Points:
"""
        for point in section.get('key_points', []):
            formatted += f"- {point}\n"
        
        if section.get('equations'):
            formatted += "\nEquations to Show:\n"
            for eq in section['equations']:
                formatted += f"- {eq['latex']} — {eq['description']}"
                if eq.get('show_derivation'):
                    formatted += " (show derivation step-by-step)"
                formatted += "\n"
        
        if section.get('visuals'):
            formatted += "\nVisuals Required:\n"
            for vis in section['visuals']:
                formatted += f"- [{vis['type'].upper()}] {vis['description']}\n"
                if vis.get('animation_notes'):
                    formatted += f"  Animation: {vis['animation_notes']}\n"
        
        if section.get('misconceptions_to_address'):
            formatted += "\nMisconceptions to Address:\n"
            for misc in section['misconceptions_to_address']:
                formatted += f"- {misc}\n"
        
        if section.get('transitions'):
            trans = section['transitions']
            if trans.get('from_previous'):
                formatted += f"\nTransition from previous: {trans['from_previous']}\n"
            if trans.get('to_next'):
                formatted += f"Transition to next: {trans['to_next']}\n"
        
        formatted += "\n" + "-"*60 + "\n"
    
    formatted += f"""
## KEY TAKEAWAYS
"""
    for takeaway in teaching_plan.get('key_takeaways', []):
        formatted += f"- {takeaway}\n"
    
    if teaching_plan.get('suggested_examples'):
        formatted += "\n## SUGGESTED EXAMPLES\n"
        for example in teaching_plan['suggested_examples']:
            formatted += f"- {example}\n"
    
    return formatted

# ===================================================================
# TEST
# ===================================================================

if __name__ == "__main__":
    test_query = "Explain transformers in deep learning"
    
    # Create teaching plan
    plan = create_teaching_plan(test_query)
    
    # Save for inspection
    save_teaching_plan(plan)
    
    # Format for Claude
    formatted = format_teaching_plan_for_claude(plan)
    with open("teaching_plan_formatted.txt", "w") as f:
        f.write(formatted)
    
    print("💾 Formatted teaching plan saved to: teaching_plan_formatted.txt")
    print("\n" + "="*60)
    print("TEACHING PLAN PREVIEW:")
    print("="*60)
    print(formatted[:500] + "...\n")