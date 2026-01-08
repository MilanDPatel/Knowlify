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
    fix_code_with_claude, execute_manim_script, validate_manim_api,
    auto_fix_deprecated_api
)

# ===================================================================
# CONFIG
# ===================================================================

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION")
KB_ID = os.getenv("KB_ID")
CLAUDE_SONNET_MODEL_ID = os.getenv("CLAUDE_SONNET_MODEL_ID")

INTERMEDIATE_DIR = Path("Intermediate")
INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)

from botocore.config import Config

bedrock_config = Config(
    read_timeout=180,
    connect_timeout=10,
    retries={'max_attempts': 3}
)

bedrock_runtime = boto3.client("bedrock-runtime", region_name=AWS_REGION, config=bedrock_config)
bedrock_agent_runtime = boto3.client("bedrock-agent-runtime", region_name=AWS_REGION)

# ===================================================================
# ANIMATION REQUIREMENT EXTRACTION
# ===================================================================

def analyze_context_usage(storyboard_text, kb_chunks, teaching_plan_text):
    """Log how much context we're actually using."""
    total_chars = (
        len(storyboard_text or "") +
        len(kb_chunks or "") +
        len(teaching_plan_text or "")
    )
    
    print(f"📊 CONTEXT USAGE ANALYSIS:")
    print(f"   Storyboard: {len(storyboard_text or '')} chars")
    print(f"   KB Examples: {len(kb_chunks or '')} chars")
    print(f"   Teaching Plan: {len(teaching_plan_text or '')} chars")
    print(f"   TOTAL: {total_chars} chars")
    
    # Claude's context window is ~200K tokens, but chars to tokens is ~4:1
    estimated_tokens = total_chars / 4
    print(f"   Estimated tokens: ~{int(estimated_tokens)}")
    
    if estimated_tokens > 180000:
        print(f"   ⚠️ WARNING: Approaching context limit!")
    
    print()

def extract_animation_types_with_claude(teaching_plan: dict, storyboard: dict = None) -> list:
    """Extract animation type keywords for KB retrieval."""
    print("🤖 Analyzing teaching plan to extract animation types with Claude...")
    
    formatted_plan = format_teaching_plan_for_claude(teaching_plan)
    
    storyboard_text = ""
    if storyboard:
        storyboard_text = f"\n\nSTORYBOARD:\n{json.dumps(storyboard, indent=2)[:5000]}"
    
    system_prompt = """You are an expert at analyzing educational content and identifying what types of animations are needed.

Your task: Read the teaching plan and identify what ANIMATION TECHNIQUES are required.

Focus on the VISUAL/ANIMATION aspects, not the subject matter.

Examples of animation types to identify:
- "3d visualization" or "3d surface plot"
- "2d graph" or "function plot"
- "matrix visualization" or "matrix operations"
- "geometric shapes" or "geometric transformations"
- "parametric curve"
- "vector field"
- "network diagram" or "graph visualization"
- "equation animation" or "latex rendering"
- "text animation"
- "transformation animation"
- "calculus visualization" (integrals, derivatives)
- "probability distribution"
- "number line"

Return ONLY a JSON array of concise animation type keywords.
Each keyword should be 2-5 words, describing the TYPE of animation needed.

Example output:
["3d surface plot", "matrix visualization", "parametric curve", "equation animation"]

Be specific but concise. Focus on WHAT needs to be animated, not WHY."""

    user_prompt = f"""TEACHING PLAN TO ANALYZE:
{formatted_plan[:8000]}
{storyboard_text}

Extract the animation types needed. Return ONLY a JSON array of animation type keywords.
Focus on the visual/animation techniques, not the subject matter."""

    try:
        response = bedrock_runtime.converse(
            modelId=CLAUDE_SONNET_MODEL_ID,
            messages=[{"role": "user", "content": [{"text": user_prompt}]}],
            system=[{"text": system_prompt}],
            inferenceConfig={"maxTokens": 1000, "temperature": 0.3}
        )

        response_text = response["output"]["message"]["content"][0]["text"]
        
        if "```" in response_text:
            response_text = response_text.split("```")[1].replace("json", "").strip()
        
        animation_types = json.loads(response_text)
        
        if not isinstance(animation_types, list):
            print("⚠️ Claude didn't return a list, using fallback")
            animation_types = []
        
        print(f"✅ Extracted {len(animation_types)} animation types:")
        for atype in animation_types:
            print(f"   - {atype}")
        print()
        
        return animation_types
        
    except Exception as e:
        print(f"⚠️ Error extracting animation types: {e}")
        print("   Using fallback: empty list (will use semantic search)\n")
        return []


# ===================================================================
# KNOWLEDGE BASE RETRIEVAL
# ===================================================================

def try_filter_string_contains(query: str, keyword: str, max_results: int) -> list:
    """Try filtering by keyword in topic field."""
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

def retrieve_from_kb_by_animation_types(
    query: str, 
    animation_types: list, 
    chunks_per_type: int = 2,
    max_total_chunks: int = 12
) -> str:
    """Retrieve KB chunks with fair distribution across animation types."""
    print(f"🔍 Retrieving KB examples by animation types...")
    
    if not animation_types:
        print("   No animation types provided, using semantic search")
        return retrieve_from_kb_no_filter(query, max_total_chunks)
    
    print(f"   Animation types: {animation_types}")
    print(f"   Strategy: {chunks_per_type} chunks per type, then fill to {max_total_chunks} total\n")
    
    all_results = []
    seen_texts = set()
    per_type_results = {}
    
    # First pass: Guarantee chunks_per_type for each animation type
    print("📍 FIRST PASS: Ensuring each animation type gets examples...")
    
    for anim_type in animation_types:
        type_results = []
        
        results = try_filter_string_contains(query, anim_type, chunks_per_type * 2)
        
        for result in results:
            text = result["content"]["text"]
            if text not in seen_texts:
                seen_texts.add(text)
                type_results.append(result)
                if len(type_results) >= chunks_per_type:
                    break
        
        if len(type_results) < chunks_per_type and ' ' in anim_type:
            for word in anim_type.split():
                if len(word) > 3 and len(type_results) < chunks_per_type:
                    sub_results = try_filter_string_contains(query, word, chunks_per_type * 2)
                    
                    for result in sub_results:
                        text = result["content"]["text"]
                        if text not in seen_texts:
                            seen_texts.add(text)
                            type_results.append(result)
                            if len(type_results) >= chunks_per_type:
                                break
        
        if type_results:
            per_type_results[anim_type] = type_results
            all_results.extend(type_results)
            print(f"   ✓ '{anim_type}': {len(type_results)} chunk(s)")
        else:
            per_type_results[anim_type] = []
            print(f"   ✗ '{anim_type}': 0 chunks (no matches)")
    
    print(f"\n   First pass total: {len(all_results)} chunks")
    
    # Second pass: Fill remaining slots
    remaining_slots = max_total_chunks - len(all_results)
    
    if remaining_slots > 0:
        print(f"\n📍 SECOND PASS: Filling {remaining_slots} remaining slots...")
        
        types_by_count = sorted(per_type_results.items(), key=lambda x: len(x[1]))
        
        for anim_type, existing_results in types_by_count:
            if remaining_slots <= 0:
                break
            
            needed = min(remaining_slots, 5)
            results = try_filter_string_contains(query, anim_type, needed * 2)
            
            added = 0
            for result in results:
                if remaining_slots <= 0:
                    break
                
                text = result["content"]["text"]
                if text not in seen_texts:
                    seen_texts.add(text)
                    all_results.append(result)
                    added += 1
                    remaining_slots -= 1
            
            if added > 0:
                print(f"   ✓ '{anim_type}': +{added} additional chunk(s)")
            
            if remaining_slots > 0 and ' ' in anim_type:
                for word in anim_type.split():
                    if len(word) > 3 and remaining_slots > 0:
                        sub_results = try_filter_string_contains(query, word, 3)
                        
                        for result in sub_results:
                            if remaining_slots <= 0:
                                break
                            
                            text = result["content"]["text"]
                            if text not in seen_texts:
                                seen_texts.add(text)
                                all_results.append(result)
                                remaining_slots -= 1
    
    if all_results:
        chunks = []
        for i, result in enumerate(all_results[:max_total_chunks], 1): 
            text = result["content"]["text"]
            topic = result.get("metadata", {}).get("topic", "unknown")
            chunks.append(f"--- Result {i} (topic: {topic}) ---\n{text}\n")
        
        print(f"\n📚 Retrieved {len(chunks)} unique chunks with fair distribution\n")
        return "\n".join(chunks)
    
    print(f"   ⚠️ No filtered results found, falling back to semantic search")
    
    if animation_types:
        fallback_query = f"{query} - Manim animation techniques for: {', '.join(animation_types[:5])}"
    else:
        fallback_query = query
    
    print(f"   Fallback query: {fallback_query[:100]}...")
    return retrieve_from_kb_no_filter(fallback_query, max_total_chunks)


def retrieve_from_kb_no_filter(query: str, max_results: int = 15) -> str:
    """Retrieve without filter using semantic search only."""
    print(f"🔍 Retrieving KB examples using semantic search (no filter)...")
    
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
        
        print(f"📚 Retrieved {len(chunks)} chunks (semantic search)\n")
        return "\n".join(chunks)
    except Exception as e:
        print(f"⚠️ KB retrieval error: {e}")
        return ""

# ===================================================================
# TWO-STAGE GENERATION
# ===================================================================

def generate_animation_storyboard(user_query: str, teaching_plan: dict) -> dict:
    """STAGE 1: Generate storyboard for 4-5 minute animation."""
    print("📋 STAGE 1: Generating animation storyboard...")
    
    formatted_plan = format_teaching_plan_for_claude(teaching_plan)
    
    system_prompt = """You are an animation storyboard designer for educational content.

Your task: Create a DETAILED storyboard for a Manim animation based on a teaching plan.

# CORE PRINCIPLES

1. ONE SLIDE = ONE CONCEPT
   Each moment presents exactly one visual concept, then completely clears the screen before the next.
   Clean slate between every single moment - no carryover, no accumulation.

2. TIMING & PACING
   - Total duration: 4-5 minutes (240-300 seconds)
   - Each moment: 15-25 seconds
   - Always include explicit fadeout at end of each moment

3. SCREEN TRANSITIONS
   Every moment must end with complete screen clear.
   Start each new moment with empty screen.

4. VISUAL SPECIFICATIONS
   - Specify exactly what appears and where (centered, left, top, etc.)
   - Use colored shapes with labels, not images
   - State explicitly when to clear screen (every moment transition)

OUTPUT FORMAT (JSON):
{
  "title": "Animation title",
  "total_duration_seconds": 270,
  "sections": [
    {
      "section_number": 1,
      "heading": "Section title",
      "duration_seconds": 70,
      "key_moments": [
        {
          "moment": "Show concept A",
          "duration_seconds": 20,
          "what_appears": "Specific visual description",
          "what_happens": "Animation sequence",
          "transition": "Complete fadeout - clear entire screen"
        },
        {
          "moment": "Show concept B",
          "duration_seconds": 18,
          "what_appears": "Next visual on clean slate",
          "what_happens": "New animation sequence",
          "transition": "Complete fadeout - clear entire screen"
        }
      ]
    }
  ]
}

Remember: One concept per slide. Complete fadeout between every moment. Clean, non-overlapping animations."""

    user_prompt = f"""TEACHING PLAN:
{formatted_plan[:8000]}

USER QUERY: {user_query}

Create a storyboard for 4-5 minutes (240-300 seconds).

KEY RULES:
- ONE concept per moment
- COMPLETE fadeout after each moment
- Start each moment with empty screen
- 15-25 seconds per moment
- Specify positions clearly

Return ONLY valid JSON."""

    response = bedrock_runtime.converse(
        modelId=CLAUDE_SONNET_MODEL_ID,
        messages=[{"role": "user", "content": [{"text": user_prompt}]}],
        system=[{"text": system_prompt}],
        inferenceConfig={"maxTokens": 65536, "temperature": 0.5}
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
            "total_duration_seconds": 270,
            "sections": [],
            "overall_flow": "Fallback due to parsing error"
        }


def generate_manim_from_storyboard(user_query: str, teaching_plan: dict, storyboard: dict, retrieved_chunks: str) -> str:
    """STAGE 2: Convert storyboard to Manim code."""
    print("🎬 STAGE 2: Converting storyboard to Manim code...")
    
    formatted_plan = format_teaching_plan_for_claude(teaching_plan)
    storyboard_text = json.dumps(storyboard, indent=2)

    analyze_context_usage(
        storyboard_text=storyboard_text[:15000],
        kb_chunks=retrieved_chunks[:6000],
        teaching_plan_text=formatted_plan[:5000]
    )
    
    system_prompt = r"""You are an expert Manim code generator that converts storyboards into clean, engaging animations.

# CRITICAL RULE: AGGRESSIVE FADEOUT POLICY

Every moment must follow this exact pattern:
1. Create and show content
2. Wait for viewing
3. FadeOut(*self.mobjects) - complete screen clear
4. Wait briefly before next moment

NO EXCEPTIONS. Every transition clears the entire screen.

# POSITIONING & LAYOUT

Use these positioning methods:
- .next_to(object, UP/DOWN/LEFT/RIGHT, buff=0.3)
- .to_edge(UP/DOWN/LEFT/RIGHT, buff=0.5)
- .shift(UP*2, RIGHT*3)
- .arrange(RIGHT/DOWN, buff=1.5)
- .move_to(ORIGIN)
- .scale(0.8) before positioning

Font sizes: Titles=48, Headers=36, Labels=24, Text=18

# HIGHLIGHTING

Always use SurroundingRectangle for highlights:
```python
box = SurroundingRectangle(object, buff=0.2, color=YELLOW)
self.play(Create(box))
```

# MANDATORY MOMENT STRUCTURE
```python
# Moment N: [description]
obj = create_content()
self.play(Create(obj), run_time=2)
self.wait(3)

# MANDATORY: Complete fadeout
self.play(FadeOut(*self.mobjects), run_time=1)
self.wait(0.5)

# Moment N+1: [description] - screen is now clean
next_obj = create_new_content()
self.play(Write(next_obj), run_time=2)
self.wait(3)

# MANDATORY: Complete fadeout
self.play(FadeOut(*self.mobjects), run_time=1)
self.wait(0.5)
```

# IMPLEMENTATION RULES

1. Follow storyboard exactly - one moment = one slide
2. Use FadeOut(*self.mobjects) after EVERY single moment
3. Never skip fadeouts or combine moments
4. Use KB examples for correct Manim syntax
5. Never use ImageMobject - use colored shapes with labels
6. Standard animations only: Create(), Write(), FadeIn(), FadeOut()
7. Total duration must match storyboard (240-300 seconds)

OUTPUT: Complete Python Manim script only. No markdown, no explanations."""

    user_prompt = f"""STORYBOARD TO IMPLEMENT:
{storyboard_text[:15000]}

TEACHING PLAN (context):
{formatted_plan[:5000]}

USER QUERY: {user_query}

KB EXAMPLES (use for syntax):
{retrieved_chunks[:6000]}

Convert storyboard to Manim code.

CRITICAL REMINDERS:
- ONE slide per moment
- FadeOut(*self.mobjects) after EVERY moment without exception
- Complete screen clear between all moments
- Use SurroundingRectangle for highlights
- Proper layout: .arrange(), .to_edge(), .scale()
- Duration: {storyboard.get('total_duration_seconds', 270)} seconds
- Use KB patterns, don't invent

Output: Python code only."""

    response = bedrock_runtime.converse(
        modelId=CLAUDE_SONNET_MODEL_ID,
        messages=[{"role": "user", "content": [{"text": user_prompt}]}],
        system=[{"text": system_prompt}],
        inferenceConfig={"maxTokens": 65536, "temperature": 0.4}
    )

    code = response["output"]["message"]["content"][0]["text"]
    
    if "```" in code:
        code = code.split("```")[1].replace("python", "").strip()

    print("✅ Manim code generated from storyboard!\n")
    return code

def generate_manim_animation(query: str):
    """Main pipeline - always uses two-stage approach."""
    print("\n" + "="*60)
    print(" 🎬 TWO-STAGE MANIM GENERATION PIPELINE ")
    print("="*60 + "\n")

    # STEP 1: Create Teaching Plan
    print("👨‍🏫 STEP 1: Creating Teaching Plan...")
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

    # STEP 2: Generate Animation Storyboard
    print("📋 STEP 2: Generating Animation Storyboard...")
    storyboard = generate_animation_storyboard(query, teaching_plan)

    storyboard_file = INTERMEDIATE_DIR / "animation_storyboard.json"
    with open(storyboard_file, "w") as f:
        json.dump(storyboard, f, indent=2)
    print(f"💾 Saved: {storyboard_file}\n")

    # STEP 3: Extract Animation Requirements
    print("🎨 STEP 3: Extracting Animation Requirements...")
    animation_types = extract_animation_types_with_claude(teaching_plan, storyboard)

    animation_types_file = INTERMEDIATE_DIR / "animation_types.json"
    with open(animation_types_file, "w") as f:
        json.dump({"query": query, "animation_types": animation_types}, f, indent=2)
    print(f"💾 Saved: {animation_types_file}\n")


    # STEP 4: Targeted KB Retrieval
    print("📚 STEP 4: Retrieving Targeted KB Examples...")
    kb_chunks = retrieve_from_kb_by_animation_types(
        query=query,
        animation_types=animation_types,
        chunks_per_type=2,
        max_total_chunks=12
    )

    analyze_context_usage(
        storyboard_text=json.dumps(storyboard, indent=2)[:15000],
        kb_chunks=kb_chunks[:6000],
        teaching_plan_text=format_teaching_plan_for_claude(teaching_plan)[:5000]
    )

    chunks_file = INTERMEDIATE_DIR / "kb_retrieved_chunks.txt"
    with open(chunks_file, "w") as f:
        f.write(kb_chunks)
    print(f"💾 Saved: {chunks_file}\n")

    # STEP 5: Generate Manim Code from Storyboard
    print("🎬 STEP 5: Generating Manim Code from Storyboard...")
    script = generate_manim_from_storyboard(query, teaching_plan, storyboard, kb_chunks)

    initial_script_file = INTERMEDIATE_DIR / "manim_script_v1.py"
    with open(initial_script_file, "w") as f:
        f.write(script)
    print(f"💾 Saved: {initial_script_file}\n")

    # STEP 6: Manim API Validation & Auto-Fix
    print("🔍 STEP 6A: Validating Manim API Compatibility...")
    is_api_valid, api_issues = validate_manim_api(script)
    
    if not is_api_valid:
        print(f"⚠️ Found {len(api_issues)} API compatibility issue(s):")
        for issue in api_issues[:5]:
            print(f"   {issue}")
        print()
        
        print("🔧 Auto-fixing deprecated API calls...")
        script, fixes_applied = auto_fix_deprecated_api(script)
        
        if fixes_applied:
            for fix in fixes_applied:
                print(f"   ✅ {fix}")
            
            api_fixed_file = INTERMEDIATE_DIR / "manim_script_v1_api_fixed.py"
            with open(api_fixed_file, "w") as f:
                f.write(script)
            print(f"💾 Saved: {api_fixed_file}\n")
        else:
            print("   ℹ️ No auto-fixes available for detected issues\n")

    # STEP 6B: Syntax Validation & Fixing
    print("🔍 STEP 6B: Validating Python Syntax...")
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

    # STEP 7: Execute Manim
    print("🎬 STEP 7: Executing Manim Script...")
    script_path = INTERMEDIATE_DIR / "manim_script_current.py"
    with open(script_path, "w") as f:
        f.write(script)
    
    execution_result = execute_manim_script(str(script_path))
    
    exec_log_file = INTERMEDIATE_DIR / "execution_log.json"
    with open(exec_log_file, "w") as f:
        json.dump(execution_result, f, indent=2)
    print(f"💾 Saved: {exec_log_file}\n")

    # STEP 8: Runtime Error Fixing
    max_runtime_fixes = 2
    runtime_fix_count = 0
    
    while not execution_result["success"] and runtime_fix_count < max_runtime_fixes:
        runtime_fix_count += 1
        print(f"🔧 STEP 8 (Attempt {runtime_fix_count}/{max_runtime_fixes}): Fixing Runtime Errors...")
        
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
        
        # Validate syntax after runtime fix
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
        
        # Check for API issues before re-executing
        is_api_valid, api_issues = validate_manim_api(script)
        if not is_api_valid:
            print("🔧 Detected API issues, auto-fixing...")
            script, fixes_applied = auto_fix_deprecated_api(script)
            if fixes_applied:
                for fix in fixes_applied:
                    print(f"   ✅ {fix}")
        
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
    query = "Explain what Carnot cycle is in thermodynamics"
    generate_manim_animation(query)