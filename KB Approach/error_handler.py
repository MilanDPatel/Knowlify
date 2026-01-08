import ast
import re
import json
from pathlib import Path
import subprocess

# ===================================================================
# MANIM API COMPATIBILITY (PREVENTION LAYER 1)
# ===================================================================

MANIM_API_COMPATIBILITY = {
    "deprecated_methods": {
        r'\bShowCreation\b': ('Create', 'ShowCreation is deprecated in Manim CE v0.19.x'),
        r'\bApplyMethod\b': ('.animate', 'Use .animate syntax instead of ApplyMethod'),
        r'\bShowPassingFlash\b': ('ShowPassingFlash', 'Check if this method still exists'),
        r'\bTransformFromCopy\b': ('TransformFromCopy', 'May be deprecated, verify usage'),
    },
    "camera_patterns": {
        r'self\.camera\.frame\.animate': ('self.camera.animate', 'MovingCameraScene uses self.camera.animate directly'),
    }
}

def validate_manim_api(code: str) -> tuple[bool, list[str]]:
    """
    Validate code for deprecated Manim API usage.
    Returns (is_valid, list_of_issues)
    """
    issues = []
    
    # Check deprecated methods
    for pattern, (replacement, message) in MANIM_API_COMPATIBILITY["deprecated_methods"].items():
        matches = re.finditer(pattern, code)
        for match in matches:
            line_num = code[:match.start()].count('\n') + 1
            issues.append(f"Line {line_num}: {message}")
            issues.append(f"  Found: {match.group()}")
            issues.append(f"  Replace with: {replacement}")
    
    # Check camera usage
    for pattern, (replacement, message) in MANIM_API_COMPATIBILITY["camera_patterns"].items():
        matches = re.finditer(pattern, code)
        for match in matches:
            line_num = code[:match.start()].count('\n') + 1
            issues.append(f"Line {line_num}: {message}")
            issues.append(f"  Found: {match.group()}")
            issues.append(f"  Replace with: {replacement}")
    
    return len(issues) == 0, issues


def auto_fix_deprecated_api(code: str) -> tuple[str, list[str]]:
    """
    Automatically fix common deprecated API calls.
    Returns (fixed_code, list_of_fixes_applied)
    """
    fixes_applied = []
    original_code = code
    
    # Fix ShowCreation → Create
    if 'ShowCreation' in code:
        code = re.sub(r'\bShowCreation\b', 'Create', code)
        count = original_code.count('ShowCreation')
        fixes_applied.append(f"ShowCreation → Create ({count} occurrences)")
    
    # Fix camera.frame.animate → camera.animate (for MovingCameraScene)
    if 'self.camera.frame.animate' in code:
        code = re.sub(r'self\.camera\.frame\.animate', 'self.camera.animate', code)
        count = original_code.count('self.camera.frame.animate')
        fixes_applied.append(f"self.camera.frame.animate → self.camera.animate ({count} occurrences)")
    
    # Fix ApplyMethod to .animate syntax (simple cases)
    # ApplyMethod(obj.method, arg) → obj.animate.method(arg)
    apply_method_pattern = r'ApplyMethod\((\w+)\.(\w+),\s*([^)]+)\)'
    if re.search(apply_method_pattern, code):
        def replace_apply_method(match):
            obj, method, args = match.groups()
            return f"{obj}.animate.{method}({args})"
        
        new_code = re.sub(apply_method_pattern, replace_apply_method, code)
        if new_code != code:
            count = len(re.findall(apply_method_pattern, code))
            fixes_applied.append(f"ApplyMethod → .animate syntax ({count} occurrences)")
            code = new_code
    
    return code, fixes_applied


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
                    lines[line_num] = line.replace(')', '', closes - opens)
                    print(f"   🔧 Removed {closes - opens} extra closing parenthesis")
                    return '\n'.join(lines), True
    
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
    
    if "unterminated string" in error or "EOL while scanning" in error:
        match = re.search(r'line (\d+)', error)
        if match:
            lines = code.split('\n')
            line_num = int(match.group(1)) - 1
            
            if 0 <= line_num < len(lines):
                line = lines[line_num]
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
# UNIFIED CODE FIXING (SYNTAX & RUNTIME) - ENHANCED
# ===================================================================

def fix_code_with_claude(bedrock_runtime, model_id: str, query: str, script: str, error_info: str, 
                         error_type: str, retrieved_chunks: str, teaching_plan: dict = None,
                         storyboard: dict = None) -> str:
    """Unified function to fix both syntax and runtime errors using Claude."""
    print(f"🔧 Fixing {error_type} errors with Claude...")
    
    # Enhanced error detection for deprecated API issues
    is_deprecated_api_error = False
    if error_type == "runtime":
        deprecated_indicators = ['ShowCreation', 'ApplyMethod', 'not defined', 'NameError']
        is_deprecated_api_error = any(indicator in error_info for indicator in deprecated_indicators)
    
    if error_type == "syntax":
        system_prompt = """You are a Python syntax debugger for Manim code.

Fix ONLY the specific syntax error reported. Common fixes:
- Add missing closing parentheses, brackets, quotes
- Fix indentation issues
- Add missing colons after if/for/def

Do NOT refactor working code. Output ONLY the corrected Python script."""
    
    else:  # runtime
        base_prompt = """You are a Manim CE 0.19.x runtime debugger.

Fix ONLY the specific runtime error. Common issues:
- Wrong API usage (check Manim CE docs)
- **MovingCameraScene uses self.camera.animate, NOT self.camera.frame.animate**
- Invalid parameter values
- LaTeX rendering errors
- Undefined variables

CRITICAL MANIM API RULES FOR v0.19.x:
- MovingCameraScene: Use self.camera.animate.scale() and self.camera.animate.move_to()
- Regular Scene: Cannot use camera animations
- LaggedStartMap is deprecated, use individual Write() calls in a loop

### DEPRECATED METHODS (DO NOT USE):
- ShowCreation → Use `Create` instead (CRITICAL - causes NameError)
- ApplyMethod → Use `.animate` syntax instead
- ShowPassingFlash → Verify if still exists or use alternatives

### CORRECT METHODS FOR v0.19.x:
- Create(mobject) - for drawing/creating objects (NOT ShowCreation)
- Write(mobject) - for writing text
- FadeIn(mobject) - for fading in
- FadeOut(mobject) - for fading out
- Transform(mobject1, mobject2) - for morphing
- ReplacementTransform(mobject1, mobject2) - for replacing
- Indicate(mobject) - for highlighting
- GrowArrow(arrow) - for growing arrows
- GrowFromCenter(mobject) - for growing from center

**NEVER use ShowCreation - it will cause NameError in v0.19.x**

Preserve the teaching plan vision and storyboard timing. Output ONLY the corrected Python script."""
        
        # Add specific guidance for deprecated API errors
        if is_deprecated_api_error:
            base_prompt += """

⚠️ DEPRECATED API ERROR DETECTED:
This is a Manim Community Edition v0.19.x compatibility issue.

The error message indicates use of a deprecated/removed method. Common fixes:
- ShowCreation(obj) → Create(obj)
- ApplyMethod(obj.method, arg) → obj.animate.method(arg)
- self.camera.frame.animate → self.camera.animate (for MovingCameraScene)

Search the entire code for ALL occurrences of deprecated methods and replace them."""
        
        system_prompt = base_prompt
    
    formatted_plan = json.dumps(teaching_plan, indent=2) if teaching_plan else "No plan available"
    storyboard_text = json.dumps(storyboard, indent=2) if storyboard else "No storyboard available"
    
    user_prompt = f"""USER QUERY: {query}

TEACHING PLAN:
{formatted_plan[:4000]}

STORYBOARD:
{storyboard_text[:2000]}

CURRENT SCRIPT (HAS {error_type.upper()} ERROR):
{script}

ERROR:
{error_info}

KB EXAMPLES:
{retrieved_chunks[:2000]}

Fix the {error_type} error. Maintain the storyboard's timing and completeness. Output corrected Python code only."""

    response = bedrock_runtime.converse(
        modelId=model_id,
        system=[{"text": system_prompt}],
        messages=[{"role": "user", "content": [{"text": user_prompt}]}],
        inferenceConfig={"maxTokens": 65536, "temperature": 0.2}
    )

    fixed_code = response["output"]["message"]["content"][0]["text"]
    
    if "```" in fixed_code:
        fixed_code = fixed_code.split("```")[1].replace("python", "").strip()

    print(f"✅ {error_type.capitalize()} error fixes applied\n")
    return fixed_code


# ===================================================================
# MANIM EXECUTION
# ===================================================================

def execute_manim_script(script_path: str, scene_name: str = None) -> dict:
    """Execute Manim script and capture output."""
    print("🎬 Executing Manim script...")
    
    if scene_name is None:
        with open(script_path, 'r') as f:
            content = f.read()
            matches = re.findall(r'class\s+(\w+)\s*\(.*Scene.*\)', content)
            if matches:
                scene_name = matches[0]
            else:
                return {"success": False, "stdout": "", "stderr": "", 
                       "error_message": "No Scene class found"}
    
    cmd = ["manim", "-ql", "--disable_caching", script_path, scene_name]
    print(f"   Rendering {scene_name}... (this may take 5-10 minutes)")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0:
            print("✅ Manim execution succeeded!\n")
            return {"success": True, "stdout": result.stdout, "stderr": result.stderr, "error_message": None}
        else:
            print(f"❌ Manim failed with return code {result.returncode}\n")
            
            # Extract the actual error from stderr/stdout
            error_output = result.stderr + "\n" + result.stdout
            
            # Look for common error patterns
            actual_error = None
            
            # Pattern 1: Python exceptions
            if "Traceback" in error_output:
                # Extract from "Traceback" to the end
                traceback_start = error_output.find("Traceback")
                actual_error = error_output[traceback_start:]
            
            # Pattern 2: SyntaxError specifically
            elif "SyntaxError" in error_output:
                syntax_start = error_output.find("SyntaxError") - 200
                actual_error = error_output[max(0, syntax_start):]
            
            # Pattern 3: NameError (for deprecated API)
            elif "NameError" in error_output:
                name_error_start = error_output.find("NameError") - 500
                actual_error = error_output[max(0, name_error_start):]
            
            # Pattern 4: Other Python errors
            elif "Error:" in error_output or "error:" in error_output.lower():
                error_lines = [line for line in error_output.split('\n') 
                              if 'error' in line.lower() or 'Error' in line]
                actual_error = "\n".join(error_lines[-10:])  # Last 10 error lines
            
            # Pattern 5: Fallback - last 1000 chars
            if not actual_error or len(actual_error) < 50:
                actual_error = error_output[-1000:]
            
            print(f"📋 Captured error ({len(actual_error)} chars):")
            print(actual_error[:300])
            print()
            
            return {
                "success": False, 
                "stdout": result.stdout, 
                "stderr": result.stderr,
                "error_message": actual_error
            }
            
    except subprocess.TimeoutExpired:
        print("⏱️ Execution timed out\n")
        return {"success": False, "stdout": "", "stderr": "", "error_message": "Timeout after 600s"}
    except Exception as e:
        print(f"⛔ Execution error: {e}\n")
        return {"success": False, "stdout": "", "stderr": "", "error_message": str(e)}