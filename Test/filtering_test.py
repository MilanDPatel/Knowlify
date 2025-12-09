import os
import json
import boto3
import requests
from pathlib import Path
from dotenv import load_dotenv

# ===================================================================
# CONFIG
# ===================================================================

load_dotenv()
AWS_REGION = os.getenv("AWS_REGION")
KB_ID = os.getenv("KB_ID")

# Ollama Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")
# Create Intermediate folder if it doesn't exist
INTERMEDIATE_DIR = Path("Intermediate")
INTERMEDIATE_DIR.mkdir(parents=True, exist_ok=True)

bedrock_agent_runtime = boto3.client("bedrock-agent-runtime", region_name=AWS_REGION)

# ===================================================================
# IMPROVED KEYWORD EXTRACTION
# ===================================================================

def extract_keywords_with_ollama_fixed(query: str) -> list:
    """
    Improved keyword extraction that handles case sensitivity.
    """
    print(f"🤖 Extracting keywords from query using Ollama ({OLLAMA_MODEL})...")
    
    # Better prompt for educational math concepts
    prompt = f"""Analyze this educational query and extract the main mathematical concepts.
Focus on proper nouns and technical terms that would be capitalized.

Query: "{query}"

Important: Return the concepts EXACTLY as they should appear in text (with proper capitalization).
Return ONLY a comma-separated list, nothing else.

Examples of proper capitalization:
- "Pythagorean theorem" not "pythagorean theorem"
- "Right triangle" not "right triangle" 
- "Geometry" not "geometry"

Now extract from the query above:"""

    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.1
            },
            timeout=90
        )
        
        if response.status_code == 200:
            result = response.json()
            response_text = result.get("response", "").strip()
            
            print(f"📝 Raw Ollama response: {response_text[:200]}")
            
            import re
            
            # Remove any JSON formatting
            response_text = response_text.replace('[', '').replace(']', '').replace('{', '').replace('}', '')
            response_text = response_text.replace('"', '').replace("'", '')
            
            # Remove prefixes
            response_text = re.sub(r'^(Answer:|Keywords:|Concepts:|The concepts are:)\s*', '', response_text, flags=re.IGNORECASE)
            
            # Split by delimiters
            parts = re.split(r'[,\n;]', response_text)
            keywords = []
            
            for part in parts:
                cleaned = part.strip()
                # Only keep meaningful terms
                if cleaned and len(cleaned) > 2:
                    keywords.append(cleaned)
            
            # If Ollama fails, use a simple rule-based extractor
            if not keywords:
                print(f"⚠️ Ollama returned no keywords, using rule-based extraction")
                keywords = extract_keywords_rule_based(query)
            else:
                # Ensure we have "Pythagorean" capitalized if it's in the query
                query_lower = query.lower()
                keywords_lower = [k.lower() for k in keywords]
                
                if 'pythagorean' in query_lower and 'pythagorean' not in keywords_lower:
                    keywords.append('Pythagorean theorem')
                if 'triangle' in query_lower and 'triangle' not in keywords_lower:
                    keywords.append('Triangle')
            
            keywords = keywords[:5]  # Limit to 5
            
            print(f"✅ Extracted keywords: {keywords}\n")
            return keywords
            
        else:
            print(f"⚠️ Ollama API error: {response.status_code}")
            return extract_keywords_rule_based(query)
            
    except Exception as e:
        print(f"⚠️ Error calling Ollama: {e}")
        return extract_keywords_rule_based(query)


def extract_keywords_rule_based(query: str) -> list:
    """Simple rule-based keyword extraction as fallback."""
    print(f"🔧 Using rule-based keyword extraction")
    
    # Common math concepts with proper capitalization
    math_concepts = {
        'pythagorean': 'Pythagorean theorem',
        'theorem': 'Pythagorean theorem',
        'triangle': 'Triangle',
        'right triangle': 'Right triangle',
        'geometry': 'Geometry',
        'trigonometry': 'Trigonometry',
        'algebra': 'Algebra',
        'calculus': 'Calculus',
        'derivative': 'Derivative',
        'integral': 'Integral',
        'function': 'Function',
        'equation': 'Equation',
        'graph': 'Graph',
        'angle': 'Angle',
        'hypotenuse': 'Hypotenuse',
        'proof': 'Proof',
        'formula': 'Formula'
    }
    
    query_lower = query.lower()
    keywords = []
    
    # Check for specific concepts
    for term, concept in math_concepts.items():
        if term in query_lower and concept not in keywords:
            keywords.append(concept)
    
    # Also extract multi-word phrases
    words = query.split()
    for i in range(len(words) - 1):
        bigram = f"{words[i]} {words[i+1]}".lower()
        if bigram in math_concepts and math_concepts[bigram] not in keywords:
            keywords.append(math_concepts[bigram])
    
    # If still no keywords, use important capitalized words from query
    if not keywords:
        for word in query.split():
            if word[0].isupper() and len(word) > 3:
                keywords.append(word)
    
    # Fallback to just important words
    if not keywords:
        stop_words = {'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'and', 'or', 'but', 'is', 'are', 'was', 'were', 'be', 'been', 'being'}
        words = query.replace('?', '').replace('.', '').split()
        keywords = [w.capitalize() for w in words if w.lower() not in stop_words and len(w) > 3][:5]
    
    return keywords[:5]

# ===================================================================
# SMART KB RETRIEVAL WITH CASE-HANDLING
# ===================================================================

def retrieve_from_kb_smart(query: str, keywords: list = None, max_results: int = 10) -> str:
    """
    Smart retrieval that handles case sensitivity issues.
    """
    print(f"🔍 Retrieving KB examples for: {query}")
    
    if not keywords:
        print(f"   No keywords provided, retrieving without filter")
        return retrieve_from_kb_no_filter(query, max_results)
    
    print(f"   Keywords to filter by: {keywords}")
    
    # Strategy: Try different filter approaches
    results_by_approach = {}
    
    # Approach 1: Try exact match with original case
    for keyword in keywords[:3]:  # Try first 3 keywords
        print(f"\n   Testing keyword: '{keyword}'")
        
        # Try the keyword as-is
        chunks = try_filter(query, keyword, max_results)
        if chunks:
            key_terms = ["Pythagorean", "theorem", "triangle"]
            if any(term.lower() in keyword.lower() for term in key_terms):
                print(f"   ✓ Keyword '{keyword}' returned {len(chunks.split('--- Result')) - 1} chunks")
                return chunks
        
        # Try lowercase version
        if keyword != keyword.lower():
            chunks_lower = try_filter(query, keyword.lower(), max_results)
            if chunks_lower:
                print(f"   ✓ Lowercase version '{keyword.lower()}' returned {len(chunks_lower.split('--- Result')) - 1} chunks")
                return chunks_lower
        
        # Try splitting multi-word keywords
        if ' ' in keyword:
            for word in keyword.split():
                if len(word) > 4:  # Only try substantial words
                    chunks_word = try_filter(query, word, max_results)
                    if chunks_word:
                        print(f"   ✓ Word '{word}' from '{keyword}' returned {len(chunks_word.split('--- Result')) - 1} chunks")
                        return chunks_word
    
    print(f"\n   ⚠️ No filter approach worked with keywords, retrieving without filter")
    return retrieve_from_kb_no_filter(query, max_results)


def try_filter(query: str, keyword: str, max_results: int) -> str:
    """Try a single filter and return results if successful."""
    try:
        response = bedrock_agent_runtime.retrieve(
            knowledgeBaseId=KB_ID,
            retrievalQuery={"text": query},
            retrievalConfiguration={
                "vectorSearchConfiguration": {
                    "numberOfResults": max_results,
                    "filter": {
                        "stringContains": {
                            "key": "topic",
                            "value": keyword
                        }
                    }
                }
            }
        )
        
        if response["retrievalResults"]:
            chunks = []
            for i, result in enumerate(response["retrievalResults"], 1):
                text = result["content"]["text"]
                metadata = result.get("metadata", {})
                topic = metadata.get("topic", "unknown")
                chunks.append(f"--- Result {i} (topic: {topic}) ---\n{text}\n")
            return "\n".join(chunks)
    except Exception:
        pass
    return ""


def retrieve_from_kb_no_filter(query: str, max_results: int = 10) -> str:
    """Retrieve without any filter."""
    try:
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
            metadata = result.get("metadata", {})
            topic = metadata.get("topic", "unknown")
            chunks.append(f"--- Result {i} (topic: {topic}) ---\n{text}\n")
        
        return "\n".join(chunks)
    except Exception as e:
        print(f"⚠️ KB retrieval error: {e}")
        return ""

# ===================================================================
# TEST THE FIXED VERSION
# ===================================================================

def test_fixed_version():
    print("\n" + "="*60)
    print(" TESTING FIXED KEYWORD EXTRACTION AND FILTERING ")
    print("="*60 + "\n")
    
    test_queries = [
        "Explain the pythagorean theorem in triangles",
        "Teach me about right triangles",
        "How does geometry work with the Pythagorean theorem?",
        "What is the hypotenuse of a triangle?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*40}")
        print(f" QUERY: {query}")
        print(f"{'='*40}")
        
        # Extract keywords
        keywords = extract_keywords_with_ollama_fixed(query)
        print(f"Extracted keywords: {keywords}")
        
        # Try retrieval with filtering
        print(f"\nAttempting filtered retrieval...")
        filtered_chunks = retrieve_from_kb_smart(query, keywords, max_results=5)
        
        filtered_count = len(filtered_chunks.split('--- Result')) - 1 if filtered_chunks else 0
        
        # Compare with no filter
        print(f"\nComparing with no-filter retrieval...")
        no_filter_chunks = retrieve_from_kb_no_filter(query, max_results=5)
        no_filter_count = len(no_filter_chunks.split('--- Result')) - 1 if no_filter_chunks else 0
        
        print(f"\n📊 Results for '{query}':")
        print(f"  With filter:    {filtered_count} chunks")
        print(f"  Without filter: {no_filter_count} chunks")
        
        if filtered_count > 0 and filtered_count < no_filter_count:
            print(f"  ✅ Filter is WORKING! Reduced from {no_filter_count} to {filtered_count} chunks")
        elif filtered_count == no_filter_count and filtered_count > 0:
            print(f"  ⚠️  Filter returned same number of chunks (might be matching all topics)")
        elif filtered_count == 0 and no_filter_count > 0:
            print(f"  ❌ Filter returned 0 chunks (filter too restrictive)")
        else:
            print(f"  ℹ️  No chunks retrieved")
        
        # Save results
        if filtered_chunks:
            filename = INTERMEDIATE_DIR / f"filtered_{query[:20].replace(' ', '_')}.txt"
            with open(filename, "w") as f:
                f.write(f"Query: {query}\nKeywords: {keywords}\n\n{filtered_chunks}")
    
    print(f"\n{'='*60}")
    print(f" ALL TESTS COMPLETE ")
    print(f"{'='*60}")

# ===================================================================
# RUN TEST
# ===================================================================

if __name__ == "__main__":
    test_fixed_version()