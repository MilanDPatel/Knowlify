import boto3
inport os
from dotenv import load_dotenv

load_dotenv()

KB_ID = os.getenv("KB_ID")

client = boto3.client("bedrock-agent-runtime", region_name=os.getenv("AWS_REGION"))

response = client.retrieve(
    knowledgeBaseId=KB_ID,
    retrievalQuery={"text": "homotopy manim"},
    retrievalConfiguration={
        "vectorSearchConfiguration": {"numberOfResults": 5}
    }
)

results = response.get("retrievalResults", [])

print("\nRetrieved", len(results), "chunks\n")

for i, r in enumerate(results, 1):
    md = r.get("metadata", {})
    print(f"----- Chunk {i} -----")
    print("File:", md.get("file"))
    print("Repo:", md.get("repo"))
    print("Lines:", md.get("lines"))
    print("Preview:", r["content"]["text"][:200], "...\n")
