"""
Maniflow Processing Script - Convert PDF to animated educational videos
Accepts PDF path as command line argument
"""

import os
import sys
import pathlib

# Force unbuffered output for real-time logging (Python 3.7+)
try:
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
except AttributeError:
    # Older Python versions - rely on -u flag and PYTHONUNBUFFERED env var
    pass

import httpx
from dotenv import load_dotenv
from google import genai
from google.genai import types as gemini_types
from langchain_google_genai import ChatGoogleGenerativeAI
from tqdm import tqdm

from maniflow import ManiflowAnimationClient, ManiflowBreakdownClient


def main(pdf_path: str):
    # Setup
    print("=== Setup ===")
    load_dotenv()

    aistudio_gemini_api_key = os.environ.get('GOOGLE_API_KEY')
    if not aistudio_gemini_api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is not set")
    
    print(f"API Key: {aistudio_gemini_api_key[:3]}...{aistudio_gemini_api_key[-1:]}")
    gemini_client = genai.Client(api_key=aistudio_gemini_api_key)

    MODEL_NAME = "gemini-3-pro-preview"

    # Validate PDF path
    pdf_file = pathlib.Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    # Breakdown
    print("\n=== Starting Breakdown ===")
    maniflow_breakdown_client = ManiflowBreakdownClient(gemini_client)

    breakdown_obj, raw_breakdown_response = maniflow_breakdown_client.breakdown(
        file_path=pdf_file,
        model=MODEL_NAME,
        thinking_level="high"
    )

    print("Breakdown completed successfully!")

    # Generate storyboards
    print("\n=== Generating Storyboards ===")
    storyboards = {}

    for i, topic in tqdm(enumerate(breakdown_obj.topics), desc="Creating storyboards"):
        storyboard_obj, raw_storyboard_response = maniflow_breakdown_client.storyboard(
            topic=topic,
            model=MODEL_NAME,
            thinking_level="high",
            source_file=str(pdf_file)
        )
        storyboards[topic.name] = storyboard_obj

    print(f"Generated {len(storyboards)} storyboards")

    # Animation
    print("\n=== Setting up Animation Client ===")
    langchain_client = ChatGoogleGenerativeAI(
        model=MODEL_NAME,
        temperature=1.0,
        max_tokens=None,
        timeout=None,
        max_retries=2,
    )
    langchain_client.client = gemini_client

    maniflow_animation_client = ManiflowAnimationClient(
        langchain_client, 
        agent_workspace_path='./agent_workspace/'
    )

    # Progress callback
    def progress_callback(topic_idx, iteration, message):
        print(f"[Topic {topic_idx}, Iteration {iteration}] {message}")

    # Generate animations for all topics
    print("\n=== Generating Animations ===")
    all_animation_results = {}

    for i, topic in enumerate(breakdown_obj.topics):
        topic_name = topic.name
        
        if topic_name in storyboards:
            print(f"\n--- Starting Animation for Topic {i}: {topic_name} ---")
            
            results = maniflow_animation_client.animate_single(
                breakdown=breakdown_obj,
                storyboard=storyboards[topic_name],
                topic_index=i,
                max_iterations=5,
                on_progress=progress_callback,
                ratelimit=0
            )
            
            all_animation_results[topic_name] = results
        else:
            print(f"Warning: No storyboard found for topic: {topic_name}")

    print("\n=== Processing Complete ===")
    print(f"Generated animations for {len(all_animation_results)} topics")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python process_pdf.py <path_to_pdf>")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    main(pdf_path)

