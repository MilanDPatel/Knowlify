"""
Eduly Processing Script - Convert PDF to animated educational videos
"""

import os
import pathlib

import httpx
from dotenv import load_dotenv
from google import genai
from google.genai import types as gemini_types
from langchain_google_genai import ChatGoogleGenerativeAI
from tqdm import tqdm

from eduly import EdulyAnimationClient, EdulyBreakdownClient


def main():
    # Setup
    print("=== Setup ===")
    load_dotenv(dotenv_path="../.env")

    aistudio_gemini_api_key = os.environ['GOOGLE_API_KEY']
    print(f"API Key: {aistudio_gemini_api_key[:3]}...{aistudio_gemini_api_key[-1:]}")
    gemini_client = genai.Client(api_key=aistudio_gemini_api_key)

    MODEL_NAME = "gemini-3-pro-preview"

    # Breakdown
    print("\n=== Starting Breakdown ===")
    eduly_breakdown_client = EdulyBreakdownClient(gemini_client)

    breakdown_obj, raw_breakdown_response = eduly_breakdown_client.breakdown(
        file_path=pathlib.Path("./rlmpaper.pdf"),
        model=MODEL_NAME,
        thinking_level="high"
    )

    print("Breakdown completed successfully!")

    # Generate storyboards
    print("\n=== Generating Storyboards ===")
    storyboards = {}

    for i, topic in tqdm(enumerate(breakdown_obj.topics), desc="Creating storyboards"):
        storyboard_obj, raw_storyboard_response = eduly_breakdown_client.storyboard(
            topic=topic,
            model=MODEL_NAME,
            thinking_level="high",
            source_file="./rlmpaper.pdf"
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


    eduly_animation_client = EdulyAnimationClient(
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
            
            results = eduly_animation_client.animate_single(
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
    main()