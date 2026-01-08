import os
import json
from pathlib import Path
import ollama

# ============================
# CONFIG
# ============================

KB_FOLDERS = [
    Path("/Users/milanpatel/Desktop/Knowlify/manim_examples"),
    Path("/Users/milanpatel/Desktop/Knowlify/manim_kb")
]

# ============================
# OLLAMA CONFIG
# ============================
OLLAMA_MODEL = "codellama"
OLLAMA_CLIENT = ollama.Client(host='http://localhost:11434')

# ============================
# Ensure Folders Exist
# ============================
def check_folders():
    for folder in KB_FOLDERS:
        if not folder.exists():
            print(f"❌ ERROR: Folder not found at {folder.absolute()}")
            print("Fix the folder path.")
            exit(1)
        else:
            print(f"Using folder at: {folder.absolute()}")


# ============================
# Ollama Helper Function
# ============================
def generate_topic_with_ollama(code_content: str) -> str:
    """Sends code to Ollama to generate a short descriptive topic."""
    
    system_prompt = (
        "Analyze the Manim code and identify what mathematical concept, algorithm, or visualization it creates. "
        "Output ONLY a keyword phrase (maximum 10 words) naming the specific concept. "
        "Use noun phrases only. NO verbs like 'demonstrate' or 'show'. NO full sentences. NO generic terms like 'animation' or 'visualization'. "
        "Be specific and describe what THIS particular code actually implements or teaches."
    )

    try:
        # Handle both string and list formats
        if isinstance(code_content, list):
            code_text = "".join(code_content)
        else:
            code_text = code_content
            
        response = OLLAMA_CLIENT.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"What specific concept does THIS code implement?\n\n{code_text[:2000]}"}
            ],
            options={
                "temperature": 0.3,  # Slightly higher for more variety
                "num_ctx": 4096,
                "num_predict": 25  # Allow up to 10 words
            }
            
        )
        
        topic = response['message']['content'].strip().replace('\n', ' ')
        
        # Aggressive cleaning of common filler words and phrases
        filler_patterns = [
            "this code demonstrates",
            "this code shows",
            "this demonstrates",
            "this shows",
            "demonstrates",
            "showing",
            "visualizes",
            "visualizing",
            "animation of",
            "animation showing",
            "the code",
            "this animation",
            "code for",
            "manim animation",
            "keywords:",
            "concept:",
        ]
        
        topic_lower = topic.lower()
        for phrase in filler_patterns:
            if phrase in topic_lower:
                # Remove the phrase and everything before it
                idx = topic_lower.index(phrase)
                topic = topic[idx + len(phrase):].strip()
                topic_lower = topic.lower()
        
        # Remove common verb prefixes at the start
        verb_prefixes = ["demonstrate", "show", "visualize", "animate", "display", "present"]
        words = topic.split()
        if words and words[0].lower() in verb_prefixes:
            topic = " ".join(words[1:])
        
        # Clean up punctuation and quotes
        topic = topic.strip('"\'.:;,')
        
        # If it's still too long or sentence-like, try to extract just the noun phrase
        if len(topic.split()) > 8 or any(c in topic.lower() for c in ["how to", "in order to"]):
            # Try to find the main noun phrase after common prepositions
            for prep in [" of ", " for ", " about "]:
                if prep in topic.lower():
                    parts = topic.lower().split(prep, 1)
                    if len(parts[1].split()) <= 6:
                        topic = parts[1].strip()
                        break
        
        return topic if topic else "code analysis"
        
    except Exception as e:
        print(f"❌ Ollama API Error: {e}")
        return "processing failed"


# ============================
# Main Processing Function
# ============================
def process_folders():
    for base_folder in KB_FOLDERS:
        print("\n============================")
        print(f"Processing: {base_folder}")
        print("============================")

        if not base_folder.exists():
            print(f"❌ Folder not found: {base_folder}")
            continue

        for root, dirs, files in os.walk(base_folder):
            for file in files:
                # Only process .json files (not .json.metadata.json)
                if not file.endswith(".json") or file.endswith(".metadata.json"):
                    continue

                json_path = Path(root) / file
                filename_no_ext = file[:-5]  # Remove .json extension

                # Check if metadata already exists
                metadata_name = f"{file}.metadata.json"
                metadata_path = Path(root) / metadata_name
                
                if metadata_path.exists():
                    print(f"⏭  Skipping (metadata exists): {file}")
                    continue

                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        code_content = data.get("code", "")
                        
                        if not code_content:
                            print(f"⚠️  No code found in: {file}")
                            continue
                            
                except Exception as e:
                    print(f"❌ Could not read file {json_path}: {e}")
                    continue

                print(f"\n🧠 Calling Ollama for: {file}")
                
                topic = generate_topic_with_ollama(code_content)
                
                # Write metadata JSON
                metadata = {
                    "topic": topic
                }

                with open(metadata_path, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, indent=4)

                print(f"✔ Saved metadata | Topic: '{topic}'")

    print("\nDone.")


# ============================
# Run Everything
# ============================
if __name__ == "__main__":
    check_folders()
    process_folders()