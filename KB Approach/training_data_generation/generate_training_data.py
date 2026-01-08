import json
import os
from pathlib import Path
from openai import OpenAI
import time
from dotenv import load_dotenv


load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# ===================================================================
# STEP 1: ENRICH KB WITH TOPIC + DESCRIPTION
# ===================================================================

def enrich_single_code_snippet(code_lines: list) -> dict:
    """Use OpenAI to analyze code and extract topic + description."""
    
    # Join code lines into single string
    code = "\n".join(code_lines) if isinstance(code_lines, list) else code_lines
    
    prompt = f"""Analyze this Manim animation code and provide:
1. A concise topic (2-5 words describing the type of animation)
2. A clear description (1 sentence describing what the animation shows)

Code:
```python
{code[:3000]}
```

Return ONLY valid JSON in this exact format:
{{"topic": "...", "description": "..."}}

Examples:
- {{"topic": "2D function graph", "description": "Shows a parabola f(x)=x² plotted on coordinate axes with equation label"}}
- {{"topic": "3D surface plot", "description": "Displays a parametric 3D surface with rotating camera view"}}
- {{"topic": "text animation", "description": "Animates text appearing with Write effect and transformation"}}
- {{"topic": "matrix transformation", "description": "Animates a 2x2 matrix transforming a square into a parallelogram"}}

Be specific about what the animation does, not just what objects it creates."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an expert at analyzing Manim code. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )
        
        text = response.choices[0].message.content.strip()
        
        # Clean up response
        if "```" in text:
            text = text.split("```")[1].replace("json", "").strip()
        
        result = json.loads(text)
        
        return {
            "topic": result.get("topic", "unknown"),
            "description": result.get("description", "")
        }
        
    except Exception as e:
        print(f"      ⚠️ Error: {e}")
        return {"topic": "unknown", "description": ""}


def process_all_kb_folders(kb_folders: list, output_dir: str):
    """Process manim_examples and manim_kb folders."""
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    all_enriched_data = []
    total_processed = 0
    
    for folder in kb_folders:
        folder_path = Path(folder)
        
        if not folder_path.exists():
            print(f"⚠️ Folder not found: {folder}")
            continue
        
        print(f"\n📁 Processing folder: {folder}")
        print("="*60)
        
        # Find all .json files (excluding .metadata.json)
        json_files = [f for f in folder_path.rglob("*.json") if not f.name.endswith(".metadata.json")]

        
        print(f"   Found {len(json_files)} JSON files\n")
        
        for json_file in json_files:
            print(f"   📄 {json_file.name}")
            
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                code = data.get('code', [])
                
                if not code:
                    print(f"      ⚠️ Empty code, skipping\n")
                    continue
                
                print(f"      Analyzing with OpenAI...", end=" ")
                
                metadata = enrich_single_code_snippet(code)
                
                print(f"✅")
                print(f"      Topic: {metadata['topic']}")
                print(f"      Description: {metadata['description'][:80]}...")
                
                # Create enriched entry (remove source_url)
                enriched_item = {
                    "code": code,
                    "topic": metadata["topic"],
                    "description": metadata["description"]
                }
                
                all_enriched_data.append(enriched_item)
                total_processed += 1
                
                print()
                
                # Rate limiting: sleep to avoid hitting OpenAI rate limits
                time.sleep(0.5)
                
            except Exception as e:
                print(f"      ❌ Error processing file: {e}\n")
    
    # Save all enriched data to single file
    enriched_file = output_path / "all_enriched_kb.json"
    with open(enriched_file, 'w', encoding='utf-8') as f:
        json.dump(all_enriched_data, f, indent=2)
    
    print("\n" + "="*60)
    print(f"✅ ENRICHMENT COMPLETE")
    print(f"   Total entries processed: {total_processed}")
    print(f"💾 Saved to: {enriched_file}")
    print("="*60 + "\n")
    
    return str(enriched_file), total_processed


# ===================================================================
# STEP 2: GENERATE SYNTHETIC STORYBOARDS + CREATE TRAINING PAIRS
# ===================================================================

def create_synthetic_storyboard(topic: str, description: str) -> dict:
    """Create a synthetic storyboard from topic + description."""
    
    return {
        "title": topic,
        "total_duration_seconds": 30,
        "sections": [{
            "section_number": 1,
            "heading": topic,
            "duration_seconds": 30,
            "key_moments": [{
                "moment": description,
                "duration_seconds": 25,
                "what_appears": f"Visual for {topic}",
                "what_happens": "Animation sequence",
                "transition": "Complete fadeout - clear entire screen"
            }]
        }]
    }


def create_training_data(enriched_kb_path: str, output_jsonl_path: str):
    """Generate training pairs in AWS Bedrock format."""
    
    print("\n📊 GENERATING TRAINING DATA")
    print("="*60 + "\n")
    
    with open(enriched_kb_path, 'r', encoding='utf-8') as f:
        kb_data = json.load(f)
    
    output_path = Path(output_jsonl_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    training_examples = []
    skipped = 0
    
    for i, item in enumerate(kb_data, 1):
        code = item.get('code', [])
        topic = item.get('topic', '')
        description = item.get('description', '')
        
        # Skip if missing critical data
        if not code or not topic or not description:
            print(f"   ⚠️ Entry {i}: Missing data, skipping")
            skipped += 1
            continue
        
        # Join code lines into string
        code_string = "\n".join(code) if isinstance(code, list) else code
        
        # Create synthetic storyboard
        storyboard = create_synthetic_storyboard(topic, description)
        storyboard_json = json.dumps(storyboard, indent=2)
        
        # Create prompt
        prompt = f"""Convert this storyboard to Manim code.

STORYBOARD:
{storyboard_json}

Generate complete, working Manim code that:
- Follows the storyboard structure exactly
- Implements one concept per moment
- Uses complete fadeouts between all moments (FadeOut(*self.mobjects))
- Matches the specified duration
- Uses proper Manim positioning and layout

Output Python code only, no markdown formatting."""

        # Create training pair
        training_pair = {
            "prompt": prompt,
            "completion": code_string
        }
        
        training_examples.append(training_pair)
        
        if i % 50 == 0:
            print(f"   Processed {i}/{len(kb_data)} entries...")
    
    # Write to JSONL (one JSON object per line)
    with open(output_path, 'w', encoding='utf-8') as f:
        for example in training_examples:
            f.write(json.dumps(example) + '\n')
    
    print()
    print("="*60)
    print(f"✅ TRAINING DATA CREATED")
    print(f"   Total examples: {len(training_examples)}")
    print(f"   Skipped: {skipped}")
    print(f"💾 Saved to: {output_path}")
    print("="*60 + "\n")
    
    return len(training_examples)


# ===================================================================
# MAIN EXECUTION
# ===================================================================

def main():
    print("\n" + "="*60)
    print(" 🎬 MANIM TRAINING DATA GENERATION PIPELINE ")
    print("="*60 + "\n")
    
    # Configuration
    KB_FOLDERS = [
        "manim_examples",
        "manim_kb"
    ]
    
    ENRICHED_OUTPUT_DIR = "training_data_generation"
    TRAINING_JSONL_OUTPUT = "training_data_generation/manim_finetuning.jsonl"
    
    # STEP 1: Enrich KB with OpenAI
    print("STEP 1: ENRICHING KB WITH OPENAI")
    print("-" * 60)
    enriched_file, total_enriched = process_all_kb_folders(KB_FOLDERS, ENRICHED_OUTPUT_DIR)
    
    if total_enriched == 0:
        print("❌ No data enriched. Exiting.")
        return
    
    # STEP 2: Generate training data
    print("\nSTEP 2: CREATING TRAINING DATA")
    print("-" * 60)
    num_examples = create_training_data(enriched_file, TRAINING_JSONL_OUTPUT)
    
    # Final summary
    print("\n" + "="*60)
    print(" 🎉 PIPELINE COMPLETE ")
    print("="*60)
    print(f"\n📊 Summary:")
    print(f"   KB entries enriched: {total_enriched}")
    print(f"   Training examples created: {num_examples}")
    print(f"\n📁 Output files:")
    print(f"   Enriched KB: {enriched_file}")
    print(f"   Training data: {TRAINING_JSONL_OUTPUT}")
    print(f"\n🚀 Next steps:")
    print(f"   1. Review {TRAINING_JSONL_OUTPUT}")
    print(f"   2. Upload to AWS S3")
    print(f"   3. Create fine-tuning job in AWS Bedrock")
    print(f"   4. Use fine-tuned model ARN in your pipeline")
    print("\n" + "="*60 + "\n")


if __name__ == "__main__":
    # Make sure you have OPENAI_API_KEY set in your environment
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("   Set it with: export OPENAI_API_KEY='your-key-here'")
        exit(1)
    
    main()