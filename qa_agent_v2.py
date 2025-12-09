import os
import json
import subprocess
import boto3
import requests
from openai import OpenAI
from timeline_layout_analyzer import extract_timeline_layout, detect_collisions
from teacher_pass import create_teaching_plan, save_teaching_plan, format_teaching_plan_for_claude

# ===================================================================
# CONFIG
# ===================================================================


bedrock_runtime = boto3.client("bedrock-runtime", region_name=AWS_REGION)
bedrock_agent_runtime = boto3.client("bedrock-agent-runtime", region_name=AWS_REGION)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# ===================================================================
# OLLAMA KEYWORD EXTRACTION
# ===================================================================

def extract_keywords_with_ollama(query: str) -> list:
    """
    Use Ollama to extract 1-5 key technical keywords from the user's query.
    
    Args:
        query: User's question or request
        
    Returns:
        List of 1-5 keywords (strings)
    """
    print(f"🤖 Extracting keywords from query using Ollama ({OLLAMA_MODEL})...")
    
    # More explicit prompt with better examples
    prompt = f"""You are a keyword extractor. Extract 1-5 key technical terms from this query.

Query: "{query}"

Return ONLY a JSON array of keywords, like this example:
["graph theory", "spanning tree", "Prim's algorithm"]

Requirements:
- Return ONLY the JSON array, no other text
- Use simple, searchable terms
- Focus on technical concepts, algorithms, or topics
- Maximum 5 keywords
- Each keyword should be 1-4 words

Your JSON array:"""

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.3  # Lower temperature for more consistent output
            },
            timeout=90
        )
        
        if response.status_code == 200:
            result = response.json()
            response_text = result.get("response", "").strip()
            
            print(f"📝 Raw Ollama response: {response_text[:200]}")
            
            # Try multiple parsing strategies
            keywords = None
            
            # Strategy 1: Direct JSON parse
            try:
                parsed = json.loads(response_text)
                if isinstance(parsed, list):
                    keywords = parsed[:5]
                elif isinstance(parsed, dict):
                    # If it's a dict, extract the keys or values
                    keywords = list(parsed.keys())[:5]
                    print(f"   Converted dict keys to keywords")
            except json.JSONDecodeError:
                pass
            
            # Strategy 2: Extract array from text
            if keywords is None:
                import re
                array_match = re.search(r'\[(.*?)\]', response_text, re.DOTALL)
                if array_match:
                    try:
                        array_str = '[' + array_match.group(1) + ']'
                        keywords = json.loads(array_str)
                        print(f"   Extracted array from text")
                    except:
                        pass
            
            # Strategy 3: Split by common delimiters
            if keywords is None:
                # Remove brackets and quotes
                cleaned = response_text.replace('[', '').replace(']', '').replace('"', '').replace("'", '')
                # Split by comma, newline, or semicolon
                parts = re.split(r'[,\n;]', cleaned)
                keywords = [p.strip() for p in parts if p.strip() and len(p.strip()) > 2][:5]
                print(f"   Parsed using delimiter split")
            
            # Strategy 4: Use original query as fallback
            if not keywords or len(keywords) == 0:
                print(f"⚠️ Could not extract keywords, using query-based fallback")
                # Extract nouns and technical terms from the query
                words = query.lower().split()
                # Filter for likely technical terms (longer words, or algorithm-related)
                keywords = [w for w in words if len(w) > 4 or w in ['tree', 'graph', 'sort', 'search']][:5]
                if not keywords:
                    keywords = [query[:50]]  # Use first 50 chars of query as single keyword
            
            # Clean up keywords
            keywords = [str(k).strip().lower() for k in keywords if k][:5]
            
            if keywords:
                print(f"✅ Extracted keywords: {keywords}\n")
                return keywords
            else:
                print(f"⚠️ No keywords could be extracted\n")
                return []
        else:
            print(f"⚠️ Ollama API error: {response.status_code}")
            return []
            
    except requests.exceptions.ConnectionError:
        print(f"⚠️ Could not connect to Ollama at {OLLAMA_BASE_URL}")
        print("   Make sure Ollama is running: ollama serve")
        print("   Continuing without keyword filtering...\n")
        return []
    except Exception as e:
        print(f"⚠️ Error calling Ollama: {e}")
        print("   Continuing without keyword filtering...\n")
        return []

# ===================================================================
# KNOWLEDGE BASE RETRIEVAL WITH METADATA FILTERING
# ===================================================================

def retrieve_from_kb(query: str, keywords: list = None, max_results: int = 10) -> str:
    """
    Retrieve from knowledge base with optional metadata filtering by topic.
    
    Args:
        query: Search query text
        keywords: List of keywords to filter by (using 'topic' metadata field)
        max_results: Maximum number of results to return
        
    Returns:
        Concatenated text chunks from KB
    """
    print(f"🔍 Retrieving KB examples for: {query}")
    if keywords:
        print(f"   Filtering by topics: {keywords}")

    # Build retrieval configuration
    retrieval_config = {
        "vectorSearchConfiguration": {
            "numberOfResults": max_results
        }
    }
    
    # Add metadata filter if keywords provided
    if keywords and len(keywords) > 0:
        # Build filter for "topic in [keyword1, keyword2, ...]"
        retrieval_config["vectorSearchConfiguration"]["filter"] = {
            "in": {
                "key": "topic",
                "value": keywords
            }
        }

    try:
        response = bedrock_agent_runtime.retrieve(
            knowledgeBaseId=KB_ID,
            retrievalQuery={"text": query},
            retrievalConfiguration=retrieval_config
        )

        chunks = []
        for i, result in enumerate(response["retrievalResults"], 1):
            text = result["content"]["text"]
            # Optionally include metadata for debugging
            metadata = result.get("metadata", {})
            topic = metadata.get("topic", "unknown")
            chunks.append(f"--- Result {i} (topic: {topic}) ---\n{text}\n")

        print(f"📚 Retrieved {len(chunks)} chunks\n")
        return "\n".join(chunks)
        
    except Exception as e:
        print(f"⚠️ KB retrieval error: {e}")
        print("   Falling back to retrieval without filters\n")
        
        # Fallback: retrieve without filter
        response = bedrock_agent_runtime.retrieve(
            knowledgeBaseId=KB_ID,
            retrievalQuery={"text": query},
            retrievalConfiguration={
                "vectorSearchConfiguration": {
                    "numberOfResults": max_results
                }
            }
        )
        
        chunks = []
        for i, result in enumerate(response["retrievalResults"], 1):
            text = result["content"]["text"]
            chunks.append(f"--- Result {i} ---\n{text}\n")
        
        print(f"📚 Retrieved {len(chunks)} chunks (no filter)\n")
        return "\n".join(chunks)

# ===================================================================
# CODE GENERATION (CLAUDE)
# ===================================================================

def generate_manim_code(user_query: str, teaching_plan: dict, retrieved_chunks: str) -> str:
    print("🎨 Generating Manim code from teaching plan...")

    formatted_plan = format_teaching_plan_for_claude(teaching_plan)

    system_prompt = r"""You are an expert Manim animation generator that converts TEACHING PLANS into code.

YOUR ROLE:
- You are a TRANSLATOR, not a teacher
- The teaching plan specifies WHAT to teach and in what order
- Your job is to translate that plan into working Manim code
- DO NOT add, remove, or reorder content from the teaching plan
- DO NOT make pedagogical decisions — follow the plan exactly

• Knowledge Base Usage
– Use the provided knowledge base for ANIMATION TECHNIQUES only
– Use retrieved examples for Manim syntax, patterns, and visual styles
– Never hallucinate Manim APIs — only use confirmed syntax
– Use only current official Manim API methods

• Output Requirements
- Before starting ANY new conceptual section or writing ANY new section title, you MUST insert: self.play(FadeOut(*self.mobjects))
    This clears all mobjects from the previous section.
    Always insert this before a new section heading (Section 1, Section 2, etc).
– You must output ONLY a complete, fully runnable Manim Python script
– Do NOT include narration, narration comments, timestamps, or explanations
– No markdown code blocks, just raw Python code

• Scene Rules
– You must produce exactly one Scene class
– All animations must occur inside this single Scene
– Follow the teaching plan's section order exactly

• Manim Code Rules
– Allowed imports: from manim import *
– Script must run on Manim Community Edition
– Use standard constructs: Scene, Axes, VGroup, MathTex, Text, Dot, Arrow, self.play(), self.wait(), self.add(), etc.
– Animations must be smooth, simple, and pedagogical

• LaTeX Rules (CRITICAL)
– Always use raw strings: MathTex(r"...")
– Single backslashes in raw strings: r"\alpha", r"\int_{-\infty}^{\infty}"
– NEVER double-escape: r"\\alpha" is WRONG
– Examples: MathTex(r"\psi(x) = e^{-x^2/2} \cos(3x)")
– Greek letters: \alpha, \beta, \gamma, \Delta, \theta, \lambda, \psi (NOT α, β, Δ)

# ===================================================================
# MANDATORY LAYOUT RULES (NON-NEGOTIABLE)
# ===================================================================

## VERTICAL ZONES - NEVER VIOLATE
Title Zone:     y > 2.5     (titles only, use .to_edge(UP, buff=0.5))
Content Zone:   -3 < y < 2  (graphs, equations, main content)
Caption Zone:   y < -3      (optional captions, use .to_edge(DOWN))

## TEMPORAL ISOLATION - PREVENT ALL COLLISIONS
Rule: Before showing NEW content, REMOVE or FADE OUT old content

## CONTENT POSITIONING STRATEGY
- After title fades out, position main content HIGHER on screen
- Default position for graphs/visualizations: UP * 0.5 (slightly above center)
- Alternative: move_to(ORIGIN) or shift(UP * 0.3) for centered content
- Only shift DOWN if content needs to be lower or if multiple objects need spacing

CORRECT PATTERN FOR EACH SECTION:
```python
# Section heading
section_title = Text("Section Heading").to_edge(UP, buff=0.5)
self.play(Write(section_title))
self.wait(1)
self.play(FadeOut(section_title))

# Main content (positioned HIGH)
content = create_section_content().shift(UP * 0.5)
self.play(Create(content))
self.wait(2)

# Transition: fade out before next section
self.play(FadeOut(content))
```

• Final Output Format
– Your final answer must contain ONLY the complete Python Manim script
– No extra text before or after
– No commentary
– No markdown formatting
– Follow the teaching plan's structure and content exactly"""

    user_prompt = f"""USER_QUERY: {user_query}

TEACHING PLAN (FOLLOW THIS EXACTLY):
{formatted_plan}

KNOWLEDGE BASE SEARCH RESULTS (for animation techniques):
{retrieved_chunks}

Generate the complete Manim script now (raw Python code only, no markdown).
Translate each section of the teaching plan into animations.
Use the Title → Fade → High Content pattern for each section.
Follow the plan's content, order, and visual specifications exactly."""

    response = bedrock_runtime.converse(
        modelId=CLAUDE_SONNET_MODEL_ID,
        messages=[{"role": "user", "content": [{"text": user_prompt}]}],
        system=[{"text": system_prompt}],
        inferenceConfig={"maxTokens": 4000, "temperature": 0.3}
    )

    code = response["output"]["message"]["content"][0]["text"]

    if "```" in code:
        code = code.split("```")[1].replace("python", "").strip()

    print("✅ Code Generated\n")
    return code

# ===================================================================
# QA REVIEW (GPT-4o) — ONE TIME ONLY
# ===================================================================

def qa_review_code(user_query: str, teaching_plan: dict, script_text: str) -> dict:
    print("🔎 Running Timeline-Aware QA Review (SINGLE PASS)...")

    temp_path = "temp_generated_scene.py"
    with open(temp_path, "w") as f:
        f.write(script_text)

    try:
        timeline_data = extract_timeline_layout(temp_path)
        collisions = detect_collisions(timeline_data)
        
        timeline_json = json.dumps(timeline_data, indent=2)
        collision_json = json.dumps(collisions, indent=2)
        plan_json = json.dumps(teaching_plan, indent=2)
        
        qa_prompt = f"""
You are a Manim CE 0.19 TIMELINE validator with TEACHING PLAN AWARENESS.

CRITICAL RULES TO ENFORCE:
1. Title Zone (y > 2.5): ONLY titles/headers allowed
2. Content Zone (-3 < y < 2): Main visualizations, graphs, equations
3. Fade-Out Old Content: Before new content appears, old content MUST be removed
4. Content Positioning: After title removal, content should be positioned HIGH (UP * 0.5 or ORIGIN)
5. Text Before Graphs: If text shown first, it MUST be removed/faded before graph appears
6. TEACHING PLAN ADHERENCE: Verify that all sections from the teaching plan are implemented
7. CONTENT ACCURACY: Check that equations, visuals, and explanations match the teaching plan

--- ORIGINAL TEACHING PLAN ---
{plan_json}

--- GENERATED SCRIPT ---
{script_text}

--- TIMELINE DATA (object positions over time) ---
{timeline_json}

--- DETECTED COLLISIONS ---
{collision_json}

Your tasks:
✓ Check for ANY overlaps in the collision data
✓ Verify titles are in title zone (y > 2.5)
✓ Verify content positioning is appropriate (prefer higher positioning after title removal)
✓ Ensure old objects are removed before new ones appear
✓ Check for LaTeX errors, API misuse, off-screen content
✓ Detect invalid use of VGroup(*self.mobjects), which causes TypeError
✓ VERIFY teaching plan adherence:
  - Are all sections from the teaching plan present?
  - Are they in the correct order?
  - Are the specified equations included?
  - Are the specified visuals implemented?
  - Is any content added that wasn't in the plan?

For EACH issue found, create an entry with:
- Exact time when issue occurs (if applicable)
- Which objects are affected
- Specific fix needed
- Priority level (1=critical, 5=minor)

Return ONLY JSON:
{{
  "has_issues": true/false,
  "total_collisions": {len(collisions)},
  "teaching_plan_adherence": {{
    "all_sections_present": true/false,
    "correct_order": true/false,
    "missing_sections": [],
    "extra_content": [],
    "equations_match": true/false,
    "visuals_match": true/false
  }},
  "issues_found": [
    {{
      "type": "timeline_collision|spacing|off_screen|api_error|latex_error|plan_deviation",
      "priority": 1-5,
      "time": <seconds or null>,
      "description": "...",
      "suggestion": "..."
    }}
  ]
}}
"""
        
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a strict layout and pedagogy validator. Return ONLY valid JSON."},
                {"role": "user", "content": qa_prompt}
            ],
            temperature=0,
            response_format={"type": "json_object"}
        )
        
        out = json.loads(response.choices[0].message.content)
        
        if out.get("has_issues"):
            print(f"⚠️ Issues found: {len(out['issues_found'])} (including {len(collisions)} collisions)")
            if not out.get("teaching_plan_adherence", {}).get("all_sections_present"):
                print("⚠️ WARNING: Some sections from teaching plan are missing!")
        else:
            print("🎉 No static analysis issues found")
        
        print()
        return out
        
    except Exception as e:
        print(f"[⛔ QA ERROR] {e}")
        return {"has_issues": False, "issues_found": []}

# ===================================================================
# FIX PASS (CLAUDE) — BASED ON STATIC ANALYSIS
# ===================================================================

def fix_manim_code(user_query, teaching_plan, script_text, qa_report, retrieved_chunks):
    print("🔧 Fixing script based on static analysis...")

    temp_path = "temp_generated_scene.py"
    with open(temp_path, "w") as f:
        f.write(script_text)
    
    try:
        timeline_data = extract_timeline_layout(temp_path)
        collisions = detect_collisions(timeline_data)
    except:
        timeline_data = []
        collisions = []
    
    timeline_json = json.dumps(timeline_data, indent=2)
    collision_json = json.dumps(collisions, indent=2)
    issues_json = json.dumps(qa_report, indent=2)
    formatted_plan = format_teaching_plan_for_claude(teaching_plan)

    system_prompt = """
You are an expert Manim CE 0.19.x code fixer with TIMELINE AND TEACHING PLAN AWARENESS.

MANDATORY FIXES (IN ORDER OF PRIORITY):
1. TEACHING PLAN ADHERENCE: Ensure all sections from the plan are included in correct order
2. COLLISION FIXES: For EVERY collision, add FadeOut BEFORE new content appears
3. HIGH POSITIONING: After title removal, position content HIGH: use .shift(UP * 0.5) or move_to(ORIGIN)
4. ZONE COMPLIANCE: Keep titles in title zone (y > 2.5) with .to_edge(UP, buff=0.5)
5. PATTERN COMPLIANCE: Use the Title → Fade → High Content pattern for each section
6. SPACING: Maintain spacing >= 0.5 between all objects
7. API/LATEX: Fix any LaTeX errors or API misuse

Example fix for collision with HIGH positioning:
```python
# BEFORE (has collision + low positioning):
title = Text("Example")
graph = Axes()
self.play(Write(title), Create(graph))  # COLLISION!

# AFTER (fixed with HIGH positioning):
title = Text("Example").to_edge(UP, buff=0.5)
self.play(Write(title))
self.wait(1)
self.play(FadeOut(title))  # Remove before graph

graph = Axes().shift(UP * 0.5)  # HIGH positioning
self.play(Create(graph))
```

IMPORTANT: Do NOT remove content from the teaching plan. If a section is missing, ADD it.
Do NOT reorder sections. Follow the teaching plan structure exactly.

Output ONLY the corrected Python Manim script. No markdown, no explanations.
"""

    user_prompt = f"""
USER QUERY:
{user_query}

TEACHING PLAN (MUST FOLLOW EXACTLY):
{formatted_plan}

CURRENT SCRIPT:
{script_text}

TIMELINE DATA:
{timeline_json}

DETECTED COLLISIONS:
{collision_json}

QA ISSUES:
{issues_json}

Fix ALL collisions by adding FadeOut statements before new content appears.
Position content HIGH after title removal (shift UP * 0.5 or ORIGIN).
Ensure all sections from the teaching plan are present and in correct order.
Generate the corrected script now (raw Python only).
"""

    response = bedrock_runtime.converse(
        modelId=CLAUDE_SONNET_MODEL_ID,
        system=[{"text": system_prompt}],
        messages=[{"role": "user", "content": [{"text": user_prompt}]}],
        inferenceConfig={"maxTokens": 4000, "temperature": 0.2}
    )

    fixed_code = response["output"]["message"]["content"][0]["text"]

    if "```" in fixed_code:
        fixed_code = fixed_code.split("```")[1].replace("python", "").strip()

    print("✅ Static analysis fixes applied\n")
    return fixed_code

# ===================================================================
# EXECUTE MANIM SCRIPT AND CAPTURE ERRORS
# ===================================================================

def execute_manim_script(script_path: str, scene_name: str = None) -> dict:
    """
    Execute a Manim script and capture output/errors.
    
    Returns:
        dict with:
            - success: bool
            - stdout: str
            - stderr: str
            - error_message: str (if failed)
    """
    print("🎬 Executing Manim script...")
    
    # Auto-detect scene name if not provided
    if scene_name is None:
        with open(script_path, 'r') as f:
            content = f.read()
            # Look for class definitions that inherit from Scene
            import re
            matches = re.findall(r'class\s+(\w+)\s*\(.*Scene.*\)', content)
            if matches:
                scene_name = matches[0]
            else:
                return {
                    "success": False,
                    "stdout": "",
                    "stderr": "",
                    "error_message": "Could not find a Scene class in the script"
                }
    
    # Run manim with low quality for faster testing
    cmd = ["manim", "-ql", "--disable_caching", script_path, scene_name]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
        
        if result.returncode == 0:
            print("✅ Manim execution succeeded!\n")
            return {
                "success": True,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "error_message": None
            }
        else:
            print(f"❌ Manim execution failed with return code {result.returncode}\n")
            return {
                "success": False,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "error_message": result.stderr or result.stdout
            }
            
    except subprocess.TimeoutExpired:
        print("⏱️ Manim execution timed out\n")
        return {
            "success": False,
            "stdout": "",
            "stderr": "",
            "error_message": "Execution timed out after 120 seconds"
        }
    except Exception as e:
        print(f"⛔ Execution error: {e}\n")
        return {
            "success": False,
            "stdout": "",
            "stderr": "",
            "error_message": str(e)
        }

# ===================================================================
# RUNTIME ERROR FIX (CLAUDE)
# ===================================================================

def fix_runtime_errors(user_query, teaching_plan, script_text, execution_result, retrieved_chunks):
    """Fix script based on actual runtime errors from Manim execution."""
    print("🔧 Fixing runtime errors...")
    
    formatted_plan = format_teaching_plan_for_claude(teaching_plan)
    
    system_prompt = """
You are an expert Manim CE 0.19.x debugger specializing in RUNTIME ERROR FIXES.

You are given:
1. A Manim script that failed to execute
2. The actual error output from running the script
3. The teaching plan it should follow

Your job:
- Analyze the ACTUAL runtime error (not hypothetical issues)
- Fix the specific bugs causing the failure
- Common Manim runtime errors:
  * AttributeError: object has no attribute (wrong API usage)
  * TypeError: wrong number of arguments
  * ValueError: invalid parameter values
  * LaTeX rendering errors
  * Import errors
  * IndexError: list index out of range
  * NameError: undefined variables

CRITICAL RULES:
1. Keep ALL content from the teaching plan
2. Fix ONLY what caused the runtime error
3. Do NOT refactor working code
4. Maintain the same structure and flow
5. Use correct Manim CE API (not old versions)

Output ONLY the corrected Python Manim script. No markdown, no explanations.
"""

    error_details = f"""
STDOUT:
{execution_result['stdout']}

STDERR:
{execution_result['stderr']}

ERROR MESSAGE:
{execution_result['error_message']}
"""

    user_prompt = f"""
USER QUERY:
{user_query}

TEACHING PLAN:
{formatted_plan}

CURRENT SCRIPT (FAILED TO RUN):
{script_text}

RUNTIME ERROR OUTPUT:
{error_details}

KNOWLEDGE BASE EXAMPLES:
{retrieved_chunks}

Analyze the runtime error and fix the script. Output corrected Python code only.
"""

    response = bedrock_runtime.converse(
        modelId=CLAUDE_SONNET_MODEL_ID,
        system=[{"text": system_prompt}],
        messages=[{"role": "user", "content": [{"text": user_prompt}]}],
        inferenceConfig={"maxTokens": 4000, "temperature": 0.2}
    )

    fixed_code = response["output"]["message"]["content"][0]["text"]

    if "```" in fixed_code:
        fixed_code = fixed_code.split("```")[1].replace("python", "").strip()

    print("✅ Runtime error fixes applied\n")
    return fixed_code

# ===================================================================
# UPDATED MAIN PIPELINE WITH OLLAMA KEYWORD EXTRACTION
# ===================================================================

def generate_manim_animation(query: str):
    print("\n" + "="*60)
    print(" AI → MANIM → EXECUTION PIPELINE WITH OLLAMA ")
    print("="*60 + "\n")

    # STEP 0: Extract Keywords with Ollama
    print("🔑 STEP 0: Extracting Keywords with Ollama...")
    keywords = extract_keywords_with_ollama(query)
    if not keywords:
        print("⚠️ No keywords extracted, proceeding without KB filtering\n")
    print()

    # STEP 1: Teacher Pass
    print("📖 STEP 1: Creating Teaching Plan...")
    teaching_plan = create_teaching_plan(query)
    save_teaching_plan(teaching_plan, "teaching_plan.json")
    print()

    # STEP 2: KB Retrieval with Keyword Filtering
    print("📚 STEP 2: Retrieving Animation Techniques (with keyword filter)...")
    kb_chunks = retrieve_from_kb(query, keywords=keywords)
    print()

    # STEP 3: Generate Initial Code
    print("🎨 STEP 3: Generating Manim Code...")
    script = generate_manim_code(query, teaching_plan, kb_chunks)
    
    # Save initial version
    with open("manim_script_v1_initial.py", "w") as f:
        f.write(script)
    print("💾 Saved: manim_script_v1_initial.py\n")

    # STEP 4: Static QA (ONE TIME)
    print("🔍 STEP 4: Static QA Review (Timeline Analysis)...")
    qa_report = qa_review_code(query, teaching_plan, script)

    # STEP 5: Apply Static Fixes (if needed)
    if qa_report.get("has_issues"):
        print("🔧 STEP 5: Applying Static Analysis Fixes...")
        script = fix_manim_code(query, teaching_plan, script, qa_report, kb_chunks)
        with open("manim_script_v2_static_fixed.py", "w") as f:
            f.write(script)
        print("💾 Saved: manim_script_v2_static_fixed.py\n")
    else:
        print("✅ STEP 5: No static issues found, skipping fixes\n")

    # STEP 6: Execute Manim Script
    print("🎬 STEP 6: Executing Manim Script...")
    script_path = "manim_script_current.py"
    with open(script_path, "w") as f:
        f.write(script)
    
    execution_result = execute_manim_script(script_path)

    # STEP 7: Runtime Error Fix (if needed)
    if not execution_result["success"]:
        print("🔧 STEP 7: Fixing Runtime Errors...")
        print(f"Error encountered:\n{execution_result['error_message'][:500]}...\n")
        
        script = fix_runtime_errors(query, teaching_plan, script, execution_result, kb_chunks)
        
        with open("manim_script_v3_runtime_fixed.py", "w") as f:
            f.write(script)
        print("💾 Saved: manim_script_v3_runtime_fixed.py\n")
        
        # Try executing one more time
        print("🎬 STEP 7 (cont): Re-executing Fixed Script...")
        execution_result = execute_manim_script("manim_script_v3_runtime_fixed.py")
        
        if execution_result["success"]:
            print("🎉 SUCCESS after runtime fix!\n")
        else:
            print("⚠️ Still has errors. Manual review needed.\n")
            print(f"Final error:\n{execution_result['error_message']}\n")
    else:
        print("🎉 STEP 7: Script executed successfully on first try!\n")

    print("="*60)
    print(" PIPELINE COMPLETE ")
    print("="*60 + "\n")

    return script, teaching_plan, execution_result, keywords

# ===================================================================
# RUN MAIN
# ===================================================================

if __name__ == "__main__":
    test_query = "Teach me minimum spanning trees in computer science using Prim's algorithm"
    final_code, final_plan, exec_result, extracted_keywords = generate_manim_animation(test_query)

    # Save final output
    with open("final_manim_scene.py", "w") as f:
        f.write(final_code)
    
    with open("final_teaching_plan.json", "w") as f:
        json.dump(final_plan, f, indent=2)
    
    # Save extracted keywords
    with open("extracted_keywords.json", "w") as f:
        json.dump({"query": test_query, "keywords": extracted_keywords}, f, indent=2)

    print("💾 Saved: final_manim_scene.py")
    print("💾 Saved: final_teaching_plan.json")
    print("💾 Saved: extracted_keywords.json")
    
    if exec_result["success"]:
        print("\n✅ Video rendered successfully!")
        print("📹 Check the media/videos folder for output")
    else:
        print("\n⚠️ Final script still has errors:")
        print(exec_result["error_message"][:1000])