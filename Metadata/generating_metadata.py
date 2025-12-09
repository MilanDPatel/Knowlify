import os
import json
from pathlib import Path
import ollama

# ============================
# CONFIG
# ============================

REPO_FOLDER = Path("/Users/milanpatel/Desktop/videos")
OUTPUT_FOLDER = Path.home() / "Desktop/knowlify/Metadata/S3_Upload_Updated"
YEARS = [str(y) for y in range(2015, 2026)]

# ============================
# OLLAMA CONFIG
# ============================
OLLAMA_MODEL = "codellama"
OLLAMA_CLIENT = ollama.Client(host='http://localhost:11434')

# ============================
# Ensure Repo Exists
# ============================
def clone_repo_if_missing():
    if not REPO_FOLDER.exists():
        print(f"❌ ERROR: Local repo not found at {REPO_FOLDER}")
        print("Fix the REPO_FOLDER path.")
        exit(1)
    else:
        print(f"Using local repo at: {REPO_FOLDER}")


# ============================
# Ensure Output Folder Exists
# ============================
OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)


# ============================
# Ollama Helper Function
# ============================
def generate_topic_with_ollama(code_content: str) -> str:
    """Sends code to Ollama to generate a short descriptive topic."""
    
    # UPDATED: Much more direct prompt focused on the animation/concept itself
    system_prompt = (
        "You are analyzing Manim animation code. "
        "Output ONLY the mathematical concept or animation objective being demonstrated. "
        "Maximum 10 words. No mention of 'code', 'python', 'manim', 'animation', or technical terms. "
        "Examples: 'demonstrate pythagorean theorem' or 'visualize sine wave transformation' or 'show binary tree traversal'. "
        "Just state what is being shown or taught."
    )

    try:
        response = OLLAMA_CLIENT.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"What concept does this code demonstrate?\n\n{code_content[:2000]}"}
            ],
            options={
                "temperature": 0.1,
                "num_ctx": 4096,
                "num_predict": 20  # Limit output tokens to force brevity
            }
        )
        
        topic = response['message']['content'].strip().replace('\n', ' ')
        
        # Post-processing to remove common fluff phrases
        fluff_phrases = [
            "this code demonstrates",
            "this code shows",
            "the code",
            "this animation",
            "this demonstrates",
            "this shows",
            "demonstrates:",
            "shows:"
        ]
        
        topic_lower = topic.lower()
        for phrase in fluff_phrases:
            if topic_lower.startswith(phrase):
                topic = topic[len(phrase):].strip()
                break
        
        # Remove quotes if present
        topic = topic.strip('"\'')
        
        return topic if topic else "Code Summary Error"
        
    except Exception as e:
        print(f"❌ Ollama API Error: {e}")
        return "Ollama Processing Failed"


# ============================
# Main Processing Function
# ============================
def process_repo():
    for year in YEARS:
        folder_name = f"_{year}"
        year_path = REPO_FOLDER / folder_name

        print("\n============================")
        print(f"Processing: {folder_name}")
        print("============================")

        if not year_path.exists():
            print(f"❌ Folder not found: {folder_name}")
            continue

        for root, dirs, files in os.walk(year_path):
            for file in files:
                if not file.endswith(".py"):
                    continue

                py_path = Path(root) / file
                filename_no_ext = file[:-3]

                try:
                    with open(py_path, "r", encoding="utf-8") as f:
                        code_lines = f.readlines()
                        code_content = "".join(code_lines)
                except Exception as e:
                    print(f"❌ Could not read file {py_path}: {e}")
                    continue

                print(f"\n🧠 Calling Ollama for: {file}")
                
                topic = generate_topic_with_ollama(code_content)
                
                metadata_name = f"{filename_no_ext}.json.metadata.json"
                output_name = f"{filename_no_ext}.json"

                # Write main JSON
                main_json_path = OUTPUT_FOLDER / output_name
                main_json = {
                    "topic": topic,
                    "code": code_lines
                }

                with open(main_json_path, "w", encoding="utf-8") as f:
                    json.dump(main_json, f, indent=4)

                # Write metadata JSON
                metadata_json_path = OUTPUT_FOLDER / metadata_name
                metadata = {
                    "metadataAttributes": {
                        "year": int(year),
                        "topic": topic
                    }
                }

                with open(metadata_json_path, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, indent=4)

                print(f"✔ Saved: {output_name} + metadata | Topic: '{topic}'")

    print("\nDone.")


# ============================
# Run Everything
# ============================
if __name__ == "__main__":
    clone_repo_if_missing()
    process_repo()