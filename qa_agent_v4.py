import os
import json
import subprocess
import boto3
import requests
import ast
import re
from pathlib import Path
from teacher_pass import create_teaching_plan, format_teaching_plan_for_claude

# ===================================================================
# CONFIG
# ===================================================================

INTERMEDIATE_DIR = Path("Intermediate")
INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)

bedrock_runtime = boto3.client("bedrock-runtime", region_name=AWS_REGION)
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

def retrieve_from_kb(query: str, keywords: list = None, max_results: int = 10) -> str:
    """Smart retrieval with keyword filtering and fallback."""
    print(f"🔍 Retrieving KB examples for: {query}")
    
    if not keywords:
        return retrieve_from_kb_no_filter(query, max_results)
    
    print(f"   Keywords: {keywords}")
    
    # Try each keyword
    for keyword in keywords[:6]:
        chunks = try_filter_string_contains(query, keyword, max_results)
        if chunks:
            chunk_count = len(chunks.split('--- Result')) - 1
            if chunk_count > 0:
                print(f"   ✓ '{keyword}' returned {chunk_count} chunks")
                return chunks
        
        # Try splitting multi-word keywords
        if ' ' in keyword:
            for word in keyword.split():
                if len(word) > 4:
                    chunks = try_filter_string_contains(query, word, max_results)
                    if chunks and '--- Result' in chunks:
                        print(f"   ✓ '{word}' returned chunks")
                        return chunks
    
    print(f"   ⚠️ No filtered results, retrieving without filter")
    return retrieve_from_kb_no_filter(query, max_results)


def try_filter_string_contains(query: str, keyword: str, max_results: int) -> str:
    """Try filtering by keyword."""
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
        
        if response["retrievalResults"]:
            chunks = []
            for i, result in enumerate(response["retrievalResults"], 1):
                text = result["content"]["text"]
                topic = result.get("metadata", {}).get("topic", "unknown")
                chunks.append(f"--- Result {i} (topic: {topic}) ---\n{text}\n")
            return "\n".join(chunks)
    except Exception as e:
        print(f"      Filter error: {str(e)[:100]}")
    return ""


def retrieve_from_kb_no_filter(query: str, max_results: int = 10) -> str:
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
# SYNTAX VALIDATION & RULE-BASED FIXING
# ===================================================================

def validate_python_syntax(code: str) -> tuple[bool, str]:
    """Validate Python syntax without executing."""
    try:
        ast.parse(code)
        return True, ""
    except SyntaxError as e:
        error_msg = f"SyntaxError at line {e.lineno}: {e.msg}"
        if e.text and e.offset:
            error_msg += f"\n  {e.text.rstrip()}\n  {' ' * (e.offset - 1)}^"
        return False, error_msg
    except Exception as e:
        return False, f"Parse error: {str(e)}"


def quick_fix_syntax(code: str, error: str) -> tuple[str, bool]:
    """Fix common syntax errors with rule-based logic. Returns (fixed_code, was_fixed)."""
    
    # Fix unclosed parentheses
    if "'(' was never closed" in error or "unmatched ')'" in error:
        match = re.search(r'line (\d+)', error)
        if match:
            lines = code.split('\n')
            line_num = int(match.group(1)) - 1
            
            if 0 <= line_num < len(lines):
                line = lines[line_num]
                opens = line.count('(')
                closes = line.count(')')
                
                if opens > closes:
                    lines[line_num] = line.rstrip() + ')' * (opens - closes)
                    print(f"   🔧 Added {opens - closes} closing parenthesis")
                    return '\n'.join(lines), True
                elif closes > opens:
                    # Remove extra closing parens
                    lines[line_num] = line.replace(')', '', closes - opens)
                    print(f"   🔧 Removed {closes - opens} extra closing parenthesis")
                    return '\n'.join(lines), True
    
    # Fix unclosed brackets
    if "'[' was never closed" in error:
        match = re.search(r'line (\d+)', error)
        if match:
            lines = code.split('\n')
            line_num = int(match.group(1)) - 1
            
            if 0 <= line_num < len(lines):
                line = lines[line_num]
                opens = line.count('[')
                closes = line.count(']')
                
                if opens > closes:
                    lines[line_num] = line.rstrip() + ']' * (opens - closes)
                    print(f"   🔧 Added {opens - closes} closing bracket")
                    return '\n'.join(lines), True
    
    # Fix unclosed quotes
    if "unterminated string" in error or "EOL while scanning" in error:
        match = re.search(r'line (\d+)', error)
        if match:
            lines = code.split('\n')
            line_num = int(match.group(1)) - 1
            
            if 0 <= line_num < len(lines):
                line = lines[line_num]
                # Count quotes
                if line.count('"') % 2 == 1:
                    lines[line_num] = line.rstrip() + '"'
                    print(f"   🔧 Added closing double quote")
                    return '\n'.join(lines), True
                elif line.count("'") % 2 == 1:
                    lines[line_num] = line.rstrip() + "'"
                    print(f"   🔧 Added closing single quote")
                    return '\n'.join(lines), True
    
    return code, False


def get_error_context(code: str, error_line: int, context_lines: int = 3) -> str:
    """Get error line plus surrounding context."""
    lines = code.split('\n')
    start = max(0, error_line - context_lines - 1)
    end = min(len(lines), error_line + context_lines)
    
    context = []
    for i in range(start, end):
        marker = ">>> ERROR >>>" if i == error_line - 1 else "            "
        context.append(f"{marker} Line {i+1}: {lines[i]}")
    
    return "\n".join(context)

# ===================================================================
# UNIFIED CODE FIXING (SYNTAX & RUNTIME)
# ===================================================================

def fix_code_with_claude(query: str, script: str, error_info: str, error_type: str, 
                         retrieved_chunks: str, teaching_plan: dict = None) -> str:
    """Unified function to fix both syntax and runtime errors using Claude."""
    print(f"🔧 Fixing {error_type} errors with Claude...")
    
    if error_type == "syntax":
        system_prompt = """You are a Python syntax debugger for Manim code.

Fix ONLY the specific syntax error reported. Common fixes:
- Add missing closing parentheses, brackets, quotes
- Fix indentation issues
- Add missing colons after if/for/def

Do NOT refactor working code. Output ONLY the corrected Python script."""
    
    else:  # runtime
        system_prompt = """You are a Manim CE 0.19.x runtime debugger.

Fix ONLY the specific runtime error. Common issues:
- Wrong API usage (check Manim CE docs)
- Invalid parameter values
- LaTeX rendering errors
- Undefined variables

Preserve the teaching plan vision. Output ONLY the corrected Python script."""
    
    formatted_plan = format_teaching_plan_for_claude(teaching_plan) if teaching_plan else "No plan available"
    
    user_prompt = f"""USER QUERY: {query}

TEACHING PLAN:
{formatted_plan[:1500]}

CURRENT SCRIPT (HAS {error_type.upper()} ERROR):
{script}

ERROR:
{error_info}

KB EXAMPLES:
{retrieved_chunks[:1500]}

Fix the {error_type} error. Output corrected Python code only."""

    response = bedrock_runtime.converse(
        modelId=CLAUDE_SONNET_MODEL_ID,
        system=[{"text": system_prompt}],
        messages=[{"role": "user", "content": [{"text": user_prompt}]}],
        inferenceConfig={"maxTokens": 4000, "temperature": 0.2}
    )

    fixed_code = response["output"]["message"]["content"][0]["text"]
    
    if "```" in fixed_code:
        fixed_code = fixed_code.split("```")[1].replace("python", "").strip()

    print(f"✅ {error_type.capitalize()} error fixes applied\n")
    return fixed_code

# ===================================================================
# CODE GENERATION
# ===================================================================

def generate_manim_code_from_plan(user_query: str, teaching_plan: dict, retrieved_chunks: str) -> str:
    """Generate Manim code using teaching plan."""
    print("🎬 Generating Manim code from teaching plan...")
    
    formatted_plan = format_teaching_plan_for_claude(teaching_plan)
    
    system_prompt = r"""You are an expert Manim Community Edition animator who creates educational visualizations.

Your job: Convert a detailed teaching plan into a complete Manim animation script.

CRITICAL REQUIREMENTS:

1. FOLLOW THE TEACHING PLAN EXACTLY
   - Each section in the plan = a sequence in your animation
   - Implement ALL visuals specified in the plan
   - Show ALL equations mentioned in the plan
   - Address misconceptions as noted

2. MANIM TECHNICAL REQUIREMENTS
   - Use ONLY Manim Community Edition v0.19.x API
   - All LaTeX in raw strings: MathTex(r"...")
   - ONE Scene class with construct() method
   - Clear screen between major sections: self.play(FadeOut(*self.mobjects))
   - Use proper imports: from manim import *

3. VISUAL LAYOUT (3-ZONE SYSTEM)
   - Title Zone: y > 2.5 (section headings)
   - Content Zone: -3 < y < 2 (main visuals, equations)
   - Caption Zone: y < -3 (explanations, notes)

4. ANIMATION TIMING
   - Follow duration estimates in the plan
   - Use run_time parameter for precise timing
   - Add wait() calls for comprehension pauses

5. PEDAGOGICAL CLARITY
   - Animate step-by-step (don't show everything at once)
   - Use colors to distinguish concepts
   - Highlight key elements when explaining them
   - Show transitions between ideas smoothly

6. CODE QUALITY
   - No syntax errors (check parentheses, brackets, quotes)
   - No undefined variables
   - Use descriptive variable names
   - Add comments for complex sections

OUTPUT: Complete Python Manim script only. No markdown, no explanations."""

    user_prompt = f"""TEACHING PLAN TO IMPLEMENT:
{formatted_plan[:3500]}

USER'S ORIGINAL QUERY: {user_query}

KNOWLEDGE BASE EXAMPLES (Manim techniques):
{retrieved_chunks[:2000]}

Generate a complete, working Manim script that brings this teaching plan to life.
Make it educational, clear, and visually engaging.

Output Python code only."""

    response = bedrock_runtime.converse(
        modelId=CLAUDE_SONNET_MODEL_ID,
        messages=[{"role": "user", "content": [{"text": user_prompt}]}],
        system=[{"text": system_prompt}],
        inferenceConfig={"maxTokens": 6000, "temperature": 0.3}
    )

    code = response["output"]["message"]["content"][0]["text"]
    
    if "```" in code:
        code = code.split("```")[1].replace("python", "").strip()

    print("✅ Manim code generated!\n")
    return code

# ===================================================================
# MANIM EXECUTION
# ===================================================================

def execute_manim_script(script_path: str, scene_name: str = None) -> dict:
    """Execute Manim script and capture output."""
    print("🎬 Executing Manim script...")
    
    if scene_name is None:
        with open(script_path, 'r') as f:
            matches = re.findall(r'class\s+(\w+)\s*\(.*Scene.*\)', f.read())
            if matches:
                scene_name = matches[0]
            else:
                return {"success": False, "stdout": "", "stderr": "", 
                       "error_message": "No Scene class found"}
    
    cmd = ["manim", "-ql", "--disable_caching", script_path, scene_name]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ Manim execution succeeded!\n")
            return {"success": True, "stdout": result.stdout, "stderr": result.stderr, "error_message": None}
        else:
            print(f"❌ Manim failed with return code {result.returncode}\n")
            return {"success": False, "stdout": result.stdout, "stderr": result.stderr,
                   "error_message": result.stderr or result.stdout}
            
    except subprocess.TimeoutExpired:
        print("⏱️ Execution timed out\n")
        return {"success": False, "stdout": "", "stderr": "", "error_message": "Timeout after 120s"}
    except Exception as e:
        print(f"⛔ Execution error: {e}\n")
        return {"success": False, "stdout": "", "stderr": "", "error_message": str(e)}

# ===================================================================
# MAIN PIPELINE
# ===================================================================

def generate_manim_animation(query: str):
    print("\n" + "="*60)
    print(" 🎬 MANIM GENERATION PIPELINE ")
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
        return None, None, None, None

    # STEP 1: Extract Keywords
    print("🔑 STEP 1: Extracting Keywords...")
    keywords = extract_keywords_with_ollama(query)
    
    keywords_file = INTERMEDIATE_DIR / "extracted_keywords.json"
    with open(keywords_file, "w") as f:
        json.dump({"query": query, "keywords": keywords}, f, indent=2)
    print(f"💾 Saved: {keywords_file}\n")

    # STEP 2: KB Retrieval
    print("📚 STEP 2: Retrieving from Knowledge Base...")
    kb_chunks = retrieve_from_kb(query, keywords=keywords)
    
    chunks_file = INTERMEDIATE_DIR / "kb_retrieved_chunks.txt"
    with open(chunks_file, "w") as f:
        f.write(kb_chunks)
    print(f"💾 Saved: {chunks_file}\n")

    # STEP 3: Generate Code
    print("🎬 STEP 3: Generating Manim Code...")
    script = generate_manim_code_from_plan(query, teaching_plan, kb_chunks)
    
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
        
        # Try rule-based fix FIRST
        script, was_fixed = quick_fix_syntax(script, syntax_error)
        
        if was_fixed:
            print("   ✅ Fixed with rule-based logic")
        else:
            # Only ask Claude if rule-based failed
            line_match = re.search(r'line (\d+)', syntax_error)
            error_context = get_error_context(script, int(line_match.group(1))) if line_match else "N/A"
            
            full_error = f"{syntax_error}\n\nContext:\n{error_context}"
            script = fix_code_with_claude(query, script, full_error, "syntax", kb_chunks, teaching_plan)
        
        # Save fixed version
        fixed_file = INTERMEDIATE_DIR / f"manim_script_v1_syntax_fix_{syntax_fix_count}.py"
        with open(fixed_file, "w") as f:
            f.write(script)
        print(f"💾 Saved: {fixed_file}\n")
        
        # Validate again
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
        print(f"Error:\n{execution_result['error_message'][:500]}...\n")
        
        error_info = f"STDOUT:\n{execution_result['stdout']}\n\nSTDERR:\n{execution_result['stderr']}\n\nERROR:\n{execution_result['error_message']}"
        
        script = fix_code_with_claude(query, script, error_info, "runtime", kb_chunks, teaching_plan)
        
        fixed_file = INTERMEDIATE_DIR / f"manim_script_v{runtime_fix_count + 1}_runtime_fixed.py"
        with open(fixed_file, "w") as f:
            f.write(script)
        print(f"💾 Saved: {fixed_file}\n")
        
        # Validate syntax before re-executing
        is_valid, syntax_error = validate_python_syntax(script)
        if not is_valid:
            print(f"⚠️ Fixed code has syntax errors, attempting quick fix...")
            script, _ = quick_fix_syntax(script, syntax_error)
        
        # Re-execute
        print(f"🎬 Re-executing (Attempt {runtime_fix_count})...")
        with open(script_path, "w") as f:
            f.write(script)
        execution_result = execute_manim_script(str(script_path))
        
        if execution_result["success"]:
            print(f"🎉 SUCCESS after {runtime_fix_count} fix(es)!\n")
            break

    # Save final output
    final_script = INTERMEDIATE_DIR / "final_scene.py"
    with open(final_script, "w") as f:
        f.write(script)
    print(f"💾 Saved: {final_script}")

    print("\n" + "="*60)
    print(" 🎬 PIPELINE COMPLETE ")
    print("="*60 + "\n")

    if execution_result["success"]:
        print("🎉 VIDEO RENDERED SUCCESSFULLY!")
        print("📹 Check media/videos folder\n")
    else:
        print("⚠️ Final script has errors:")
        print(execution_result["error_message"][:500])

    return script, execution_result, keywords, teaching_plan


# ===================================================================
# MAIN
# ===================================================================

if __name__ == "__main__":
    test_query = "Can you explain the A* algorithm"
    
    print(f"🎬 Testing with query: '{test_query}'\n")
    
    final_code, exec_result, keywords, plan = generate_manim_animation(test_query)
    
    if exec_result and exec_result["success"]:
        print("\n✅ COMPLETE SUCCESS!")
    else:
        print("\n⚠️ Review Intermediate folder for debugging")