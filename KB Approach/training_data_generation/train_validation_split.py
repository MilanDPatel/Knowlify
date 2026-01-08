import json
import random
from pathlib import Path

def split_training_validation(input_jsonl: str, train_output: str, val_output: str, val_split: float = 0.2):
    """Split JSONL into training and validation sets."""
    
    print(f"📊 Splitting data into train/validation...")
    
    # Read all examples
    with open(input_jsonl, 'r', encoding='utf-8') as f:
        all_examples = [json.loads(line) for line in f]
    
    total = len(all_examples)
    
    # Shuffle for random split
    random.seed(42)  # For reproducibility
    random.shuffle(all_examples)
    
    # Split
    val_size = int(total * val_split)
    train_size = total - val_size
    
    train_examples = all_examples[:train_size]
    val_examples = all_examples[train_size:]
    
    # Write training set
    with open(train_output, 'w', encoding='utf-8') as f:
        for example in train_examples:
            f.write(json.dumps(example) + '\n')
    
    # Write validation set
    with open(val_output, 'w', encoding='utf-8') as f:
        for example in val_examples:
            f.write(json.dumps(example) + '\n')
    
    print(f"✅ Split complete:")
    print(f"   Training: {train_size} examples ({train_size/total*100:.1f}%)")
    print(f"   Validation: {val_size} examples ({val_size/total*100:.1f}%)")
    print(f"   Total: {total}")
    print(f"\n💾 Files created:")
    print(f"   Train: {train_output}")
    print(f"   Val: {val_output}")

# Usage
split_training_validation(
    input_jsonl="training_data_generation/manim_finetuning.jsonl",
    train_output="training_data_generation/manim_train.jsonl",
    val_output="training_data_generation/manim_val.jsonl",
    val_split=0.2
)
