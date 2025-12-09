import os
import ast
import hashlib
import json
from pathlib import Path

# -----------------------------
# CONFIG
# -----------------------------
REPOS = {
    "3b1b": "manim_3b1b",
    "community": "manim_community",
}

OUTPUT_DIR = "manim_chunks"
MAX_FILENAME_LEN = 120  # Safe limit for macOS/Linux


# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def safe_filename(base_name: str, chunk_name: str) -> str:
    """
    Generate a short, safe filename with a hash to avoid filesystem limits.
    """
    hash_id = hashlib.sha1(chunk_name.encode("utf-8")).hexdigest()[:10]
    return f"{base_name}_{hash_id}"


def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print(f"Failed to read {path}: {e}")
        return None


# -----------------------------
# AST-BASED CHUNKING
# -----------------------------
def ast_chunks(source: str, file_path: str):
    """
    Extract class and function blocks using AST for meaningful chunks.
    """
    try:
        tree = ast.parse(source)
    except Exception:
        return []

    lines = source.split("\n")
    chunks = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            start = node.lineno - 1
            end = getattr(node, "end_lineno", start + 1)
            block = "\n".join(lines[start:end])

            chunks.append({
                "type": node.__class__.__name__,
                "name": node.name,
                "start": start,
                "end": end,
                "content": block
            })

    return chunks


# -----------------------------
# FALLBACK SIMPLE CHUNKER
# -----------------------------
def simple_chunks(source: str, file_path: str, size=200):
    lines = source.split("\n")
    chunks = []
    for i in range(0, len(lines), size):
        block = "\n".join(lines[i:i+size])
        chunks.append({
            "type": "SimpleChunk",
            "name": f"chunk_{i//size}",
            "start": i,
            "end": i+size,
            "content": block
        })
    return chunks


# -----------------------------
# GENERATE CHUNKS
# -----------------------------
def generate_chunks(source: str, file_path: str):
    ast_result = ast_chunks(source, file_path)
    if len(ast_result) == 0:
        return simple_chunks(source, file_path)
    return ast_result


# -----------------------------
# SAVE CHUNK AS TXT + JSON
# -----------------------------
def save_chunk(repo_key, rel_path, chunk, out_dir):
    file_stem = Path(rel_path).stem
    chunk_id = f"{file_stem}_{chunk['type']}_{chunk['name']}"
    safe_name = safe_filename(file_stem, chunk['name'])

    os.makedirs(out_dir, exist_ok=True)

    # TXT file (human-readable)
    txt_path = os.path.join(out_dir, f"{safe_name}.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"# File: {rel_path}\n")
        f.write(f"# ChunkType: {chunk['type']}\n")
        f.write(f"# Name: {chunk['name']}\n")
        f.write(f"# Lines: {chunk['start']}–{chunk['end']}\n\n")
        f.write(chunk["content"])

    # JSON metadata file (machine-readable)
    metadata = {
        "repo": repo_key,
        "file": rel_path,
        "symbol": chunk["name"],
        "safe_symbol": safe_name,
        "type": chunk["type"],
        "lines": [chunk["start"], chunk["end"]],
    }

    json_path = os.path.join(out_dir, f"{safe_name}.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)


# -----------------------------
# PROCESS ONE REPO
# -----------------------------
def process_repo(repo_key, root):
    print(f"\n=== Processing repo: {repo_key} ({root}) ===")

    out_subdir = os.path.join(OUTPUT_DIR, repo_key)
    os.makedirs(out_subdir, exist_ok=True)

    for dirpath, dirs, files in os.walk(root):
        for fname in files:
            if not fname.endswith(".py"):
                continue

            abs_path = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(abs_path, root)

            source = read_file(abs_path)
            if not source:
                continue

            chunks = generate_chunks(source, rel_path)
            print(f"Processed {rel_path}, {len(chunks)} chunks")

            for c in chunks:
                save_chunk(repo_key, rel_path, c, out_subdir)


# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for key, path in REPOS.items():
        if not os.path.exists(path):
            print(f"WARNING: {path} does not exist. Skipping.")
            continue
        process_repo(key, path)

    print("\nAll done! Chunks saved in:", OUTPUT_DIR)
