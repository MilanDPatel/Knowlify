import os
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# ===================================================================
# CONFIG
# ===================================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# ===================================================================
# STORYBOARD GENERATION FROM CODE
# ===================================================================

def generate_storyboard_from_code(manim_code: str) -> dict:
    """Generate a storyboard by analyzing existing Manim code using GPT-4o-mini."""
    
    system_prompt = """You are an expert at analyzing Manim animation code and creating structured storyboards.

Given Manim code, extract the logical structure and create a storyboard that describes what the animation does.

# STORYBOARD STRUCTURE

Each storyboard must have:
- title: Animation title (infer from code or class name)
- sections: Array of animation sections (2-4 sections typical)

Each section contains:
- section_number: Sequential number
- heading: Section title
- key_moments: Array of individual animation moments

Each key moment specifies:
- moment: What this animation shows (clear, actionable description)
- what_appears: Specific visual elements being created
- what_happens: Animation sequence and interactions
- transition: Always "Complete fadeout - clear entire screen"

# ANALYSIS GUIDELINES

1. IDENTIFY LOGICAL MOMENTS
   - Look for self.play() calls, self.add() calls, and self.wait() calls
   - Each FadeOut(*self.mobjects) or clear screen = end of moment
   - Group related animations into single moments

2. BE SPECIFIC
   - Mention exact objects: "Circle", "Square", "MathTex equation"
   - Note colors, positions, transformations
   - Describe animation types: "Create", "Write", "Transform", "FadeIn"

3. EDUCATIONAL FLOW
   - Identify introduction, visualization, demonstration, conclusion
   - Each moment should be one cohesive concept

4. MATCH THE CODE
   - Storyboard should accurately reflect what the code actually does
   - Don't add moments that aren't in the code
   - Don't skip significant animations

OUTPUT: Valid JSON only, no markdown formatting."""

    user_prompt = f"""Analyze this Manim code and create a storyboard describing what it does.

MANIM CODE:
```python
{manim_code}
```

Create a storyboard with 2-4 sections and multiple moments that accurately describes this animation.

Return only valid JSON in this format:
{{
  "title": "Animation Title",
  "sections": [
    {{
      "section_number": 1,
      "heading": "Section Title",
      "key_moments": [
        {{
          "moment": "Specific description of what to show and animate",
          "what_appears": "Exact visual elements: shapes, text, colors, positions",
          "what_happens": "Detailed animation sequence",
          "transition": "Complete fadeout - clear entire screen"
        }}
      ]
    }}
  ]
}}"""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )

        storyboard_text = response.choices[0].message.content
        
        # Clean up markdown if present
        if "```json" in storyboard_text:
            storyboard_text = storyboard_text.split("```json")[1].split("```")[0].strip()
        elif "```" in storyboard_text:
            storyboard_text = storyboard_text.split("```")[1].strip()
        
        storyboard = json.loads(storyboard_text)
        return storyboard
        
    except Exception as e:
        print(f"❌ Error generating storyboard: {e}")
        return None

# ===================================================================
# TRAINING DATA GENERATION
# ===================================================================

def create_training_jsonl(input_folder: str, output_file: str):
    """
    Process all JSON files in input_folder and create training JSONL file.
    
    Args:
        input_folder: Path to folder containing JSON files with 'code' field
        output_file: Path to output JSONL file for training
    """
    
    input_path = Path(input_folder)
    output_path = Path(output_file)
    
    # Get all JSON files
    json_files = list(input_path.glob("*.json"))
    
    print(f"Found {len(json_files)} JSON files in {input_folder}")
    print(f"Processing...\n")
    
    successful = 0
    failed = 0
    
    # Clear output file if it exists
    if output_path.exists():
        output_path.unlink()
    
    for idx, json_file in enumerate(json_files, 1):
        print(f"[{idx}/{len(json_files)}] Processing {json_file.name}...")
        
        try:
            # Read the JSON file
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            manim_code = data.get('code', '')
            
            if not manim_code:
                print(f"  ⚠️  No 'code' field found, skipping\n")
                failed += 1
                continue
            
            # Generate storyboard from code
            storyboard = generate_storyboard_from_code(manim_code)
            
            if not storyboard:
                print(f"  ❌ Failed to generate storyboard, skipping\n")
                failed += 1
                continue
            
            # Create training entry in OpenAI format
            training_entry = {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert at converting animation storyboards into complete, working Manim Python code. Generate code that implements all moments sequentially with proper transitions."
                    },
                    {
                        "role": "user",
                        "content": f"""Convert this storyboard to Manim code.

STORYBOARD:
{json.dumps(storyboard, indent=2)}

Generate complete, working Manim code that:
- Follows the storyboard structure exactly
- Implements one concept per moment
- Uses complete fadeouts between all moments (FadeOut(*self.mobjects))
- Uses proper Manim positioning and layout
- Includes appropriate wait() calls for viewing time
- Has clear comments marking each moment

Output Python code only, no markdown formatting."""
                    },
                    {
                        "role": "assistant",
                        "content": manim_code
                    }
                ]
            }
            
            # Append to JSONL file
            with open(output_path, 'a') as f:
                f.write(json.dumps(training_entry) + '\n')
            
            print(f"  ✅ Success! Storyboard: {storyboard['title']}")
            print(f"     Sections: {len(storyboard.get('sections', []))}, "
                  f"Total moments: {sum(len(s.get('key_moments', [])) for s in storyboard.get('sections', []))}\n")
            
            successful += 1
            
        except Exception as e:
            print(f"  ❌ Error: {e}\n")
            failed += 1
            continue
    
    print("="*60)
    print(f"Processing complete!")
    print(f"  ✅ Successful: {successful}")
    print(f"  ❌ Failed: {failed}")
    print(f"  📁 Output: {output_path}")
    print("="*60)


if __name__ == "__main__":
    # Example usage
    INPUT_FOLDER = "grant_anderson_videos"  # Folder with JSON files
    OUTPUT_FILE = "training_data.jsonl"      # Output JSONL file
    
    create_training_jsonl(INPUT_FOLDER, OUTPUT_FILE)