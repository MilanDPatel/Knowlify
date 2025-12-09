import boto3
import os

# -----------------------------
# CONFIG
# -----------------------------
AWS_REGION = "us-east-1"             # Change if needed
BUCKET_NAME = "" # Replace with your bucket name
LOCAL_CHUNKS_DIR = "manim_chunks"    # Folder containing 3b1b/ and community/
S3_PREFIX = "manim_chunks"           # Prefix in S3 bucket

# -----------------------------
# INITIALIZE S3 CLIENT
# -----------------------------
s3 = boto3.client("s3", region_name=AWS_REGION)

# -----------------------------
# CREATE BUCKET
# -----------------------------
def create_bucket(bucket_name, region):
    existing_buckets = [b['Name'] for b in s3.list_buckets()['Buckets']]
    if bucket_name not in existing_buckets:
        if region == "us-east-1":
            # us-east-1 does NOT allow LocationConstraint
            s3.create_bucket(Bucket=bucket_name)
        else:
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={"LocationConstraint": region}
            )
        print(f"Bucket {bucket_name} created.")
    else:
        print(f"Bucket {bucket_name} already exists.")

# -----------------------------
# UPLOAD FILES
# -----------------------------
def upload_chunks(local_dir, bucket_name, s3_prefix):
    for root, dirs, files in os.walk(local_dir):
        for fname in files:
            if not (fname.endswith(".txt") or fname.endswith(".json")):
                continue

            local_path = os.path.join(root, fname)
            rel_path = os.path.relpath(local_path, local_dir)
            s3_path = f"{s3_prefix}/{rel_path.replace(os.sep, '/')}"

            s3.upload_file(local_path, bucket_name, s3_path)
            print(f"Uploaded {local_path} → s3://{bucket_name}/{s3_path}")

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    create_bucket(BUCKET_NAME, AWS_REGION)
    upload_chunks(LOCAL_CHUNKS_DIR, BUCKET_NAME, S3_PREFIX)
    print("\nAll files uploaded successfully!")
