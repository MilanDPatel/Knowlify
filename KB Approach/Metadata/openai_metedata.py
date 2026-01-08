import os
import json
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ============================
# CONFIG
# ============================

KB_FOLDERS = [
    Path("/Users/milanpatel/Desktop/Knowlify/manim_examples"),
    Path("/Users/milanpatel/Desktop/Knowlify/manim_kb")
]

# ============================
# OPENAI CONFIG
# ============================
# Set your API key here or as environment variable OPENAI_API_KEY
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

OPENAI_MODEL = "gpt-4o-mini"  # Cheap and effective

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
            print(f"✓ Using folder at: {folder.absolute()}")


# ============================
# OpenAI Helper Function
# ============================
def generate_topic_with_openai(code_content: str) -> str:
    """Sends code to OpenAI to generate 3-5 keywords describing the animation."""
    
    system_prompt = (
        "You analyze Manim animation code and output exactly 3-5 keywords describing what the animation shows. "
        "Output only the keywords, no other text. Use lowercase. Separate with spaces. "
        "Examples: 'sine wave transformation', 'matrix multiplication visualization', 'binary tree traversal', 'fourier series approximation'."
    )

    try:
        # Handle both string and list formats
        if isinstance(code_content, list):
            code_text = "".join(code_content)
        else:
            code_text = code_content
            
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze this Manim code and output 3-5 keywords:\n\n{code_text[:3000]}"}
            ],
            temperature=0.3,
            max_tokens=20  # Force brevity (3-5 words = ~10-15 tokens)
        )
        
        topic = response.choices[0].message.content.strip()
        
        # Clean up any remaining issues
        topic = topic.strip('"\'.:;,')
        topic = topic.lower()
        
        # Remove any leftover sentence fragments
        if topic.startswith("keywords: "):
            topic = topic[10:].strip()
        
        # Limit to 5 words max
        words = topic.split()
        if len(words) > 5:
            topic = ' '.join(words[:5])
        
        return topic if topic else "animation code"
        
    except Exception as e:
        print(f"❌ OpenAI API Error: {e}")
        return "processing failed"


# ============================
# Main Processing Function
# ============================
def process_folders():
    total_processed = 0
    
    for base_folder in KB_FOLDERS:
        print("\n" + "="*50)
        print(f"Processing: {base_folder}")
        print("="*50)

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

                print(f"\n🤖 Calling OpenAI for: {file}")
                
                topic = generate_topic_with_openai(code_content)
                
                # Write metadata JSON
                metadata = {
                    "metadataAttributes": {
                        "topic": topic
                    }
                }

                with open(metadata_path, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, indent=4)

                print(f"✔ Saved | Topic: '{topic}'")
                total_processed += 1

    print("\n" + "="*50)
    print(f"✅ Done! Processed {total_processed} files.")
    print("="*50)


# ============================
# Run Everything
# ============================
if __name__ == "__main__":
    # Check API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("⚠️  WARNING: OPENAI_API_KEY not found in environment variables.")
        print("Set it with: export OPENAI_API_KEY='your-key-here'")
        print("Or add it directly in the code (line 20)")
        exit(1)
    
    check_folders()
    process_folders()