import os
from dotenv import load_dotenv
import os
import json
import subprocess
import boto3
import requests
import ast
import re
from pathlib import Path
from teacher_pass_v2 import create_teaching_plan, format_teaching_plan_for_claude
from error_handler import (
    validate_python_syntax, quick_fix_syntax, get_error_context,
    fix_code_with_claude, execute_manim_script
)

# ===================================================================
# CONFIG
# ===================================================================

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION")
KB_ID = os.getenv("KB_ID")
CLAUDE_SONNET_MODEL_ID = os.getenv("CLAUDE_SONNET_MODEL_ID")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")

INTERMEDIATE_DIR = Path("Intermediate")
INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)

# Configure Boto3 with increased timeout for long-running requests
from botocore.config import Config

bedrock_config = Config(
    read_timeout=180,
    connect_timeout=10,
    retries={'max_attempts': 3}
)

bedrock_runtime = boto3.client("bedrock-runtime", region_name=AWS_REGION, config=bedrock_config)
bedrock_agent_runtime = boto3.client("bedrock-agent-runtime", region_name=AWS_REGION)

# ===================================================================
# KEYWORD EXTRACTION
# ===================================================================

def extract_keywords_with_ollama(query: str) -> list:
    """Extract keywords using Ollama, with rule-based fallback."""
    print(f"🤖 Extracting keywords from query using Ollama ({OLLAMA_MODEL})...")
    
    prompt = f"""Extract main mathematical concepts from this query.
Return ONLY a comma-separated list with proper capitalization.

Query: "{query}"

Examples: "Pythagorean theorem", "Right triangle", "Geometry"
Extract now:"""

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False, "temperature": 0.1},
            timeout=90
        )
        
        if response.status_code == 200:
            result = response.json().get("response", "").strip()
            result = re.sub(r'[\[\]{}"\']', '', result)
            result = re.sub(r'^(Answer:|Keywords:|Concepts:)\s*', '', result, flags=re.IGNORECASE)
            
            keywords = [p.strip() for p in re.split(r'[,\n;]', result) if p.strip() and len(p.strip()) > 2]
            
            if not keywords:
                return extract_keywords_rule_based(query)
            
            # Add case variants
            keywords_with_variants = []
            for kw in keywords[:5]:
                keywords_with_variants.extend([kw, kw.lower()])
                if ' ' not in kw:
                    keywords_with_variants.append(kw.capitalize())
            
            # Remove duplicates
            final = []
            seen = set()
            for kw in keywords_with_variants:
                if kw not in seen:
                    seen.add(kw)
                    final.append(kw)
            
            print(f"✅ Extracted keywords: {final}\n")
            return final
            
    except requests.exceptions.ConnectionError:
        print(f"⚠️ Could not connect to Ollama, using rule-based extraction\n")
    except Exception as e:
        print(f"⚠️ Ollama error: {e}\n")
    
    return extract_keywords_rule_based(query)


def extract_keywords_rule_based(query: str) -> list:
    """Fallback rule-based keyword extraction."""
    print(f"🔧 Using rule-based keyword extraction")
    
    math_concepts = {
        'pythagorean': 'Pythagorean theorem', 'theorem': 'Pythagorean theorem',
        'triangle': 'Triangle', 'right triangle': 'Right triangle',
        'geometry': 'Geometry', 'trigonometry': 'Trigonometry',
        'algebra': 'Algebra', 'calculus': 'Calculus'
    }
    
    query_lower = query.lower()
    keywords = []
    
    for term, concept in math_concepts.items():
        if term in query_lower and concept not in keywords:
            keywords.append(concept)
    
    if not keywords:
        stop_words = {'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'and', 'or', 'is', 'are'}
        keywords = [w.capitalize() for w in query.split() if w.lower() not in stop_words and len(w) > 3][:5]
    
    # Add case variants
    variants = []
    for kw in keywords[:5]:
        variants.extend([kw, kw.lower()])
    
    return list(dict.fromkeys(variants))  # Remove duplicates

# ===================================================================
# KNOWLEDGE BASE RETRIEVAL
# ===================================================================

def try_filter_string_contains(query: str, keyword: str, max_results: int) -> list:
    """Try filtering by keyword. Returns a list of raw retrieval results."""
    try:
        response = bedrock_agent_runtime.retrieve(
            knowledgeBaseId=KB_ID,
            retrievalQuery={"text": query},
            retrievalConfiguration={
                "vectorSearchConfiguration": {
                    "numberOfResults": max_results,
                    "filter": {"stringContains": {"key": "topic", "value": keyword}}
                }
            }
        )
        return response.get("retrievalResults", [])
    except Exception as e:
        return []


def retrieve_from_kb(query: str, keywords: list = None, max_results: int = 15) -> str:
    """Smart retrieval with keyword filtering, aggregation, and fallback."""
    print(f"🔍 Retrieving KB examples for: {query}")
    
    if not keywords:
        return retrieve_from_kb_no_filter(query, max_results)
    
    print(f"   Keywords: {keywords}")
    
    all_results = []
    seen_texts = set()
    
    for keyword in keywords[:6]:
        new_results = try_filter_string_contains(query, keyword, max_results)
        
        if new_results:
            newly_added = 0
            for result in new_results:
                text = result["content"]["text"]
                if text not in seen_texts:
                    seen_texts.add(text)
                    all_results.append(result)
                    newly_added += 1
            
            if newly_added > 0:
                print(f"   ✓ '{keyword}' added {newly_added} unique chunk(s)")

        if ' ' in keyword:
            for word in keyword.split():
                if len(word) > 4:
                    new_results = try_filter_string_contains(query, word, max_results)
                    newly_added = 0
                    for result in new_results:
                        text = result["content"]["text"]
                        if text not in seen_texts:
                            seen_texts.add(text)
                            all_results.append(result)
                            newly_added += 1
                    
                    if newly_added > 0:
                        print(f"   ✓ '{word}' (split) added {newly_added} unique chunk(s)")

    if all_results:
        chunks = []
        for i, result in enumerate(all_results[:max_results], 1): 
            text = result["content"]["text"]
            topic = result.get("metadata", {}).get("topic", "unknown")
            chunks.append(f"--- Result {i} (topic: {topic}) ---\n{text}\n")
        
        print(f"📚 Retrieved {len(chunks)} unique chunks using keyword filters\n")
        return "\n".join(chunks)
    
    print(f"   ⚠️ No filtered results, retrieving without filter")
    return retrieve_from_kb_no_filter(query, max_results)


def retrieve_from_kb_no_filter(query: str, max_results: int = 15) -> str:
    """Retrieve without filter."""
    try:
        response = bedrock_agent_runtime.retrieve(
            knowledgeBaseId=KB_ID,
            retrievalQuery={"text": query},
            retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": max_results}}
        )
        
        chunks = []
        for i, result in enumerate(response["retrievalResults"], 1):
            text = result["content"]["text"]
            topic = result.get("metadata", {}).get("topic", "unknown")
            chunks.append(f"--- Result {i} (topic: {topic}) ---\n{text}\n")
        
        print(f"📚 Retrieved {len(chunks)} chunks (no filter)\n")
        return "\n".join(chunks)
    except Exception as e:
        print(f"⚠️ KB retrieval error: {e}")
        return ""

# ===================================================================
# TWO-STAGE GENERATION
# ===================================================================

def generate_animation_storyboard(user_query: str, teaching_plan: dict, retrieved_chunks: str) -> dict:
    """
    STAGE 1: Generate a DETAILED storyboard that preserves the richness of the teaching plan.
    """
    print("📋 STAGE 1: Generating animation storyboard...")
    
    formatted_plan = format_teaching_plan_for_claude(teaching_plan)
    
    system_prompt = """You are an animation storyboard designer for educational content.

Your task: Create a DETAILED, SPECIFIC STORYBOARD for a Manim animation based on a teaching plan.

===================================================================
CRITICAL REQUIREMENTS
===================================================================

1. TIMING SPECIFICATIONS
   - The final animation MUST be 2-3 minutes long (120-180 seconds)
   - Each section should be 30-45 seconds
   - Specify duration for each major segment
   - Include brief 1-2 second pauses for comprehension

2. DETAILED VISUAL SPECIFICATIONS
   - For EACH visual, specify:
     * Exact content (numbers, text, shapes)
     * Approximate positions (left/center/right, top/middle/bottom)
     * Colors for different concepts
     * Size hierarchy (what's primary vs secondary)
   - **NEVER reference actual images, photos, or pictures** - Manim cannot load external images
   - Use geometric shapes (rectangles, circles) with COLOR CODING and LABELS to represent concepts
   - Example: Instead of "cat image", use "orange rectangle labeled 'Cat'" or "cat icon using circles and triangles"
   - Include ALL worked examples from teaching plan
   - Show calculations step-by-step with intermediate results
   - Use specific numbers, not placeholders

3. ANIMATION CHOREOGRAPHY
   - Specify the SEQUENCE of animations
   - Timing for each sub-animation (keep individual steps 1-3 seconds)
   - Transitions between elements
   - What appears simultaneously vs sequentially
   - Camera movements (zoom in/out, pan)

4. EQUATION INTEGRATION
   - Show which equations when
   - If derivation needed, break into 2-3 steps maximum
   - Display variable definitions
   - Show numerical examples alongside equations

5. PRESERVE TEACHING MOMENTS
   - Include misconception clarifications from teaching plan
   - Visualize answers to student questions
   - Show comparisons and contrasts
   - Highlight key insights

OUTPUT FORMAT (JSON):
{
  "title": "Animation title",
  "total_duration_seconds": 150,
  "sections": [
    {
      "section_number": 1,
      "heading": "Section title from teaching plan",
      "duration_seconds": 40,
      "teaching_goal": "What student should understand after this section",
      "key_moments": [
        {
          "moment": "Specific teaching moment",
          "duration_seconds": 12,
          "description": "Detailed description with specific numbers",
          "visuals": [
            "Detailed visual 1 with exact values",
            "Detailed visual 2 with colors and positions"
          ],
          "equations": [
            {
              "latex": "formula here",
              "when_to_show": "timing",
              "show_variables": true
            }
          ],
          "animation_sequence": [
            "Step 1 (2s): specific action",
            "Step 2 (3s): specific action"
          ],
          "transition": "how to transition to next moment"
        }
      ],
      "misconception_addressed": "What misconception is clarified",
      "student_question_answered": "What question is answered"
    }
  ],
  "overall_flow": "Narrative arc",
  "key_teaching_moments": ["insight 1", "insight 2"],
  "verification": {
    "all_sections_covered": true,
    "duration_meets_target": true,
    "worked_examples_included": true,
    "equations_all_shown": true
  }
}

Remember: 2-3 minutes means CONCISE. Focus on core concepts, not every detail."""

    user_prompt = f"""DETAILED TEACHING PLAN TO STORYBOARD:
{formatted_plan[:12000]}

USER'S ORIGINAL QUERY: {user_query}

KB EXAMPLES (Manim techniques):
{retrieved_chunks[:3000]}

Create a DETAILED storyboard for a 2-3 minute animation (120-180 seconds).

CRITICAL: 
- Target 120-180 seconds total
- 3-4 sections maximum
- 2-3 key moments per section
- Keep individual animations 1-3 seconds each
- No external images - use colored shapes with labels

Return ONLY valid JSON."""

    response = bedrock_runtime.converse(
        modelId=CLAUDE_SONNET_MODEL_ID,
        messages=[{"role": "user", "content": [{"text": user_prompt}]}],
        system=[{"text": system_prompt}],
        inferenceConfig={"maxTokens": 50000, "temperature": 0.5}
    )

    storyboard_text = response["output"]["message"]["content"][0]["text"]
    
    if "```" in storyboard_text:
        storyboard_text = storyboard_text.split("```")[1].replace("json", "").strip()
    
    try:
        storyboard = json.loads(storyboard_text)
        
        total_moments = sum(len(s.get('key_moments', [])) for s in storyboard.get('sections', []))
        
        print(f"✅ Storyboard created: {storyboard.get('total_duration_seconds', 0)} seconds")
        print(f"   Sections: {len(storyboard.get('sections', []))}")
        print(f"   Total moments: {total_moments}")
        print()
        
        return storyboard
        
    except json.JSONDecodeError as e:
        print(f"⚠️ Storyboard JSON parse error: {e}")
        print("Using fallback storyboard")
        return {
            "title": "Animation",
            "total_duration_seconds": 120,
            "sections": [],
            "overall_flow": "Fallback due to parsing error"
        }


def generate_manim_from_storyboard(user_query: str, teaching_plan: dict, storyboard: dict, retrieved_chunks: str) -> str:
    """
    STAGE 2: Convert the detailed storyboard into Manim code.
    """
    print("🎬 STAGE 2: Converting storyboard to Manim code...")
    
    formatted_plan = format_teaching_plan_for_claude(teaching_plan)
    storyboard_text = json.dumps(storyboard, indent=2)
    
    system_prompt = r"""You are an expert Manim Community Edition code generator.

Your task: Convert a detailed storyboard into working Manim code.

CRITICAL REQUIREMENTS:

1. FOLLOW THE STORYBOARD EXACTLY
   - Implement every animation step specified
   - Use exact timings from the storyboard
   - Create all objects as described
   - Maintain the sequence order

2. DURATION ENFORCEMENT
   - The animation MUST match the storyboard duration (2-3 minutes = 120-180 seconds)
   - Use run_time parameters for precise timing
   - Add wait() calls as specified in storyboard
   - Never skip sections to save time

3. MANIM TECHNICAL REQUIREMENTS
   - Use ONLY Manim Community Edition v0.19.x API
   - All LaTeX in raw strings: MathTex(r"...")
   - ONE Scene class with construct() method
   - **CRITICAL: NEVER use ImageMobject or reference external image files**
   - Use colored rectangles, circles, or simple geometric shapes instead
   - Color-code shapes to represent different concepts
   - Add text labels to clarify what shapes represent

4. **AGGRESSIVE FADEOUT POLICY - EXTREMELY IMPORTANT**
   
   RULE: FadeOut objects IMMEDIATELY after you're done showing them.
   
   PATTERN TO FOLLOW RELIGIOUSLY:
```python
   # Create and show object
   obj = Text("Something")
   self.play(FadeIn(obj), run_time=1)
   self.wait(1)
   
   # IMMEDIATELY fade it out when done
   self.play(FadeOut(obj), run_time=0.5)
   
   # Now create next object
   obj2 = Text("Something else")
   self.play(FadeIn(obj2), run_time=1)
   self.wait(1)
   self.play(FadeOut(obj2), run_time=0.5)
```
   
   APPLY THIS TO:
   - Every text element
   - Every shape/diagram
   - Every equation
   - Every arrow
   - Every group of objects
   
   ONLY EXCEPTION: If the storyboard explicitly says "keep X on screen while showing Y"
   
   **SECTION TRANSITIONS:**
   At the end of EVERY section, add:
```python
   # Clear ALL remaining objects
   self.play(FadeOut(*self.mobjects), run_time=1)
   self.wait(0.5)
```
   
   **NEVER** let more than 2-3 objects remain on screen simultaneously unless explicitly required.

5. VISUAL LAYOUT (3-ZONE SYSTEM)
   - Title Zone: y > 2.5 (section headings)
   - Content Zone: -3 < y < 2 (main visuals, equations)
   - Caption Zone: y < -3 (explanations, notes)

6. CODE QUALITY
   - No syntax errors (check parentheses, brackets, quotes)
   - No undefined variables
   - Use descriptive variable names from storyboard
   - Add comments for each section
   - For custom colors, use hex codes like "#8B4513" instead of undefined color names

7. FADEOUT EXAMPLES - FOLLOW THESE PATTERNS:

   Example 1 - Sequential text:
```python
   text1 = Text("First point")
   self.play(FadeIn(text1))
   self.wait(2)
   self.play(FadeOut(text1))  # Remove before next
   
   text2 = Text("Second point")
   self.play(FadeIn(text2))
   self.wait(2)
   self.play(FadeOut(text2))  # Remove before next
```
   
   Example 2 - Diagram with explanation:
```python
   diagram = Circle()
   label = Text("Circle")
   group = VGroup(diagram, label)
   
   self.play(FadeIn(group))
   self.wait(2)
   self.play(FadeOut(group))  # Remove entire group
```
   
   Example 3 - Before section transition:
```python
   # ... end of section animations ...
   
   # MANDATORY: Clear everything
   self.play(FadeOut(*self.mobjects), run_time=1)
   self.wait(0.5)
   
   # Now start next section with clean slate
   next_title = Text("Next Section")
```

8. COMPLETENESS VERIFICATION
   Before finishing, verify you've implemented:
   - ALL sections from the storyboard
   - ALL animation steps in each section
   - ALL objects specified
   - Proper timing (matches storyboard duration)
   - **FadeOut after EVERY major element**
   - **FadeOut(*self.mobjects) between EVERY section**

OUTPUT: Complete Python Manim script only. No markdown, no explanations.

Remember: When in doubt, FadeOut. It's better to fade out too much than to have overlapping elements."""

    user_prompt = f"""DETAILED STORYBOARD TO IMPLEMENT:
{storyboard_text[:15000]}

TEACHING PLAN (for context):
{formatted_plan[:5000]}

USER'S ORIGINAL QUERY: {user_query}

KB EXAMPLES (Manim techniques):
{retrieved_chunks[:2000]}

Convert this storyboard into a complete, working Manim script.
Implement EVERY step. Match the timing exactly. Make it {storyboard.get('total_duration_seconds', 150)} seconds long.

CRITICAL REMINDERS:
- NO ImageMobject - use colored rectangles with labels
- Use hex codes for custom colors (e.g., "#8B4513" for brown)
- Total duration: {storyboard.get('total_duration_seconds', 150)} seconds

Output Python code only."""

    response = bedrock_runtime.converse(
        modelId=CLAUDE_SONNET_MODEL_ID,
        messages=[{"role": "user", "content": [{"text": user_prompt}]}],
        system=[{"text": system_prompt}],
        inferenceConfig={"maxTokens": 50000, "temperature": 0.4}
    )

    code = response["output"]["message"]["content"][0]["text"]
    
    if "```" in code:
        code = code.split("```")[1].replace("python", "").strip()

    print("✅ Manim code generated from storyboard!\n")
    return code

# ===================================================================
# MAIN PIPELINE
# ===================================================================

def generate_manim_animation(query: str, use_two_stage: bool = True):
    """
    Main pipeline with enhanced detail and error handling.
    """
    print("\n" + "="*60)
    print(" 🎬 ENHANCED MANIM GENERATION PIPELINE ")
    print("="*60 + "\n")

    # STEP 0: Create Teaching Plan
    print("👨‍🏫 STEP 0: Creating Teaching Plan...")
    try:
        teaching_plan = create_teaching_plan(query)
        plan_file = INTERMEDIATE_DIR / "teaching_plan.json"
        with open(plan_file, "w") as f:
            json.dump(teaching_plan, f, indent=2)
        print(f"💾 Saved: {plan_file}")
        print(f"   Title: {teaching_plan.get('title', 'N/A')}")
        print(f"   Sections: {len(teaching_plan.get('sections', []))}\n")
    except Exception as e:
        print(f"⚠️ Teaching plan failed: {e}")
        print("   Cannot proceed without teaching plan.\n")
        return None, None, None, None, None

    # STEP 1: Extract Keywords
    print("🔑 STEP 1: Extracting Keywords...")
    keywords = extract_keywords_with_ollama(query)
    
    keywords_file = INTERMEDIATE_DIR / "extracted_keywords.json"
    with open(keywords_file, "w") as f:
        json.dump({"query": query, "keywords": keywords}, f, indent=2)
    print(f"💾 Saved: {keywords_file}\n")

    # STEP 2: KB Retrieval
    print("📚 STEP 2: Retrieving from Knowledge Base...")
    kb_chunks = retrieve_from_kb(query, keywords=keywords, max_results=15)
    
    chunks_file = INTERMEDIATE_DIR / "kb_retrieved_chunks.txt"
    with open(chunks_file, "w") as f:
        f.write(kb_chunks)
    print(f"💾 Saved: {chunks_file}\n")

    # STEP 3: Two-Stage Generation
    storyboard = None
    if use_two_stage:
        print("📋 STEP 3A: Generating Animation Storyboard...")
        storyboard = generate_animation_storyboard(query, teaching_plan, kb_chunks)
        
        storyboard_file = INTERMEDIATE_DIR / "animation_storyboard.json"
        with open(storyboard_file, "w") as f:
            json.dump(storyboard, f, indent=2)
        print(f"💾 Saved: {storyboard_file}\n")
        
        print("🎬 STEP 3B: Generating Manim Code from Storyboard...")
        script = generate_manim_from_storyboard(query, teaching_plan, storyboard, kb_chunks)
    else:
        print("🎬 STEP 3: Generating Manim Code (single-stage)...")
        from qa_agent_v2 import generate_manim_code
        script = generate_manim_code(query, teaching_plan, kb_chunks)
    
    initial_script_file = INTERMEDIATE_DIR / "manim_script_v1.py"
    with open(initial_script_file, "w") as f:
        f.write(script)
    print(f"💾 Saved: {initial_script_file}\n")

    # STEP 4: Syntax Validation & Fixing
    print("🔍 STEP 4: Validating Syntax...")
    max_syntax_fixes = 3
    syntax_fix_count = 0
    
    is_valid, syntax_error = validate_python_syntax(script)
    
    while not is_valid and syntax_fix_count < max_syntax_fixes:
        syntax_fix_count += 1
        print(f"❌ Syntax Error (Attempt {syntax_fix_count}/{max_syntax_fixes}):")
        print(f"   {syntax_error}\n")
        
        script, was_fixed = quick_fix_syntax(script, syntax_error)
        
        if was_fixed:
            print("   ✅ Fixed with rule-based logic")
        else:
            line_match = re.search(r'line (\d+)', syntax_error)
            error_context = get_error_context(script, int(line_match.group(1))) if line_match else "N/A"
            
            full_error = f"{syntax_error}\n\nContext:\n{error_context}"
            script = fix_code_with_claude(bedrock_runtime, CLAUDE_SONNET_MODEL_ID, query, script, full_error, 
                                         "syntax", kb_chunks, teaching_plan, storyboard)
        
        fixed_file = INTERMEDIATE_DIR / f"manim_script_v1_syntax_fix_{syntax_fix_count}.py"
        with open(fixed_file, "w") as f:
            f.write(script)
        print(f"💾 Saved: {fixed_file}\n")
        
        is_valid, syntax_error = validate_python_syntax(script)
        
        if is_valid:
            print(f"✅ Syntax valid after {syntax_fix_count} fix(es)!\n")
            break
    
    if not is_valid:
        print(f"⚠️ Max syntax fixes reached. Error: {syntax_error}\n")

    # STEP 5: Execute Manim
    print("🎬 STEP 5: Executing Manim Script...")
    script_path = INTERMEDIATE_DIR / "manim_script_current.py"
    with open(script_path, "w") as f:
        f.write(script)
    
    execution_result = execute_manim_script(str(script_path))
    
    exec_log_file = INTERMEDIATE_DIR / "execution_log.json"
    with open(exec_log_file, "w") as f:
        json.dump(execution_result, f, indent=2)
    print(f"💾 Saved: {exec_log_file}\n")

    # STEP 6: Runtime Error Fixing
    max_runtime_fixes = 2
    runtime_fix_count = 0
    
    while not execution_result["success"] and runtime_fix_count < max_runtime_fixes:
        runtime_fix_count += 1
        print(f"🔧 STEP 6 (Attempt {runtime_fix_count}/{max_runtime_fixes}): Fixing Runtime Errors...")
        
        error_msg = execution_result['error_message']
        print(f"Error Preview:\n{error_msg[:500]}...\n")
        
        error_info = f"""STDOUT:
{execution_result['stdout'][-2000:]}

STDERR:
{execution_result['stderr'][-2000:]}

MAIN ERROR:
{error_msg}"""
        
        script = fix_code_with_claude(bedrock_runtime, CLAUDE_SONNET_MODEL_ID, query, script, error_info, 
                                     "runtime", kb_chunks, teaching_plan, storyboard)
        
        fixed_file = INTERMEDIATE_DIR / f"manim_script_v{runtime_fix_count + 1}_runtime_fixed.py"
        with open(fixed_file, "w") as f:
            f.write(script)
        print(f"💾 Saved: {fixed_file}\n")
        
        print("🔍 Validating fixed code syntax...")
        is_valid, syntax_error = validate_python_syntax(script)
        
        if not is_valid:
            print(f"⚠️ Fixed code has syntax error: {syntax_error}")
            print("   Attempting rule-based fix...")
            
            script, was_fixed = quick_fix_syntax(script, syntax_error)
            is_valid, syntax_error = validate_python_syntax(script)
            
            if not is_valid:
                print(f"❌ Still has syntax error: {syntax_error}")
                print("   Asking Claude to fix syntax...")
                
                line_match = re.search(r'line (\d+)', syntax_error)
                error_context = get_error_context(script, int(line_match.group(1))) if line_match else "N/A"
                full_error = f"{syntax_error}\n\nContext:\n{error_context}"
                
                script = fix_code_with_claude(bedrock_runtime, CLAUDE_SONNET_MODEL_ID, query, script, full_error,
                                            "syntax", kb_chunks, teaching_plan, storyboard)
                
                is_valid, syntax_error = validate_python_syntax(script)
                if not is_valid:
                    print(f"❌ Could not fix syntax: {syntax_error}")
                    print("   Skipping this attempt\n")
                    continue
        
        print("✅ Syntax valid")
        print(f"🎬 Re-executing fixed script (Attempt {runtime_fix_count})...\n")
        
        script_path = INTERMEDIATE_DIR / f"manim_script_v{runtime_fix_count + 1}_runtime_fixed.py"
        with open(script_path, "w") as f:
            f.write(script)
        
        execution_result = execute_manim_script(str(script_path))
        
        exec_log_file = INTERMEDIATE_DIR / f"execution_log_attempt_{runtime_fix_count}.json"
        with open(exec_log_file, "w") as f:
            json.dump(execution_result, f, indent=2)
        print(f"💾 Saved: {exec_log_file}\n")
        
        if execution_result["success"]:
            print(f"🎉 SUCCESS after {runtime_fix_count} fix attempt(s)!\n")
            break

    # FINAL: Save the final script
    final_script_file = INTERMEDIATE_DIR / "final_scene.py"
    with open(final_script_file, "w") as f:
        f.write(script)
    print(f"💾 Saved: {final_script_file}")

    print("\n" + "="*60)
    print(" 🎬 PIPELINE COMPLETE ")
    print("="*60 + "\n")

    if execution_result["success"]:
        print("✅ Animation rendered successfully!")
        print(f"   Check the 'media' folder for output video")
    else:
        print("⚠️ Final script has errors:")
        print(f"   {execution_result.get('error_message', 'Unknown error')[:200]}")
        print("⚠️ Review Intermediate folder for debugging")
    
    return script, teaching_plan, storyboard, kb_chunks, execution_result

if __name__ == "__main__":
    query = "Explain to me how derivatives work?."
    generate_manim_animation(query, use_two_stage=True)