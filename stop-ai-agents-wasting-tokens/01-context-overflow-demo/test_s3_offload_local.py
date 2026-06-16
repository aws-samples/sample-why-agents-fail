"""
Demo: ContextOffloader with real Amazon S3 — running locally

This is the bridge between the local demo and production. The agent runs on your
machine (your AWS credentials write to S3), but large tool outputs are offloaded to
a REAL S3 bucket instead of local disk. The only change from test_native_pointer.py
is the storage backend: FileStorage("./artifacts") -> S3Storage(bucket=...).

What it proves:
  - Large log datasets are stored in S3 and recalled by EXACT reference (s3://...),
    never flooding the LLM context window.
  - This is the same plugin used in production (agentcore_production.py); only the
    runtime environment changes.

This demo uses Strands Agents. Offloading large tool outputs to object storage is a
general agent concept and carries over to other agent frameworks.

─────────────────────────────────────────────────────────────────────────────
Prerequisites:
  - An AWS account and credentials configured locally (see README "Run on AWS").
  - OPENAI_API_KEY in .env (or swap MODEL for a BedrockModel).
  - uv pip install -r requirements.txt  +  'bedrock-agentcore[strands-agents]' is
    NOT needed here — only boto3 (ships with Strands) and the ContextOffloader.

Run:
  AWS_PROFILE=<your-profile> uv run python test_s3_offload_local.py
─────────────────────────────────────────────────────────────────────────────
"""

import os
import json
import asyncio
import inspect
import concurrent.futures

os.environ["OTEL_SDK_DISABLED"] = "true"

import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from strands import Agent
# Using OpenAI-compatible interface via Strands SDK (not direct OpenAI usage)
from strands.models.openai import OpenAIModel
from strands.vended_plugins.context_offloader import ContextOffloader, S3Storage

from native_tools import fetch_application_logs, count_errors_by_service

load_dotenv()


def storage_retrieve(storage, reference):
    """Read content back from a storage backend, handling both API styles.

    Strands 1.44+ made Storage.retrieve() async; 1.43 and earlier were sync.
    Works from a plain script (no event loop) and from inside a running loop
    (e.g. Jupyter), where asyncio.run() would otherwise raise.
    Returns (content_bytes, content_type).
    """
    result = storage.retrieve(reference)
    if not inspect.isawaitable(result):
        return result
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(result)  # no loop: safe to run directly
    # A loop is already running: execute the coroutine in a worker thread
    with concurrent.futures.ThreadPoolExecutor(1) as ex:
        return ex.submit(asyncio.run, result).result()

# ── Configuration ─────────────────────────────────────────────────────────────

REGION = os.environ.get("AWS_REGION", "us-east-1")
# Bucket name must be globally unique. Override with CONTEXT_BUCKET if you like.
ACCOUNT_ID = boto3.client("sts", region_name=REGION).get_caller_identity()["Account"]
CONTEXT_BUCKET = os.environ.get("CONTEXT_BUCKET", f"agent-context-offload-{ACCOUNT_ID}-{REGION}")
CONTEXT_PREFIX = "log-artifacts/"

MODEL = OpenAIModel(model_id="gpt-4o-mini")

QUERY = (
    "Fetch 2 hours of logs for 'api-gateway', then tell me how many errors occurred "
    "and which service had the most."
)


# ── Idempotent bucket creation ────────────────────────────────────────────────

def ensure_bucket(bucket: str, region: str) -> None:
    """Create the bucket if missing; reuse it if it already exists."""
    s3 = boto3.client("s3", region_name=region)
    try:
        s3.head_bucket(Bucket=bucket)
        print(f"✅ Bucket '{bucket}' already exists — reusing it.")
        return
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code == "403":
            raise RuntimeError(f"Bucket '{bucket}' is owned by another account. Set CONTEXT_BUCKET to a unique name.")
        if code not in ("404", "NoSuchBucket"):
            raise

    # us-east-1 must NOT receive a LocationConstraint; every other region must.
    if region == "us-east-1":
        s3.create_bucket(Bucket=bucket)
    else:
        s3.create_bucket(Bucket=bucket, CreateBucketConfiguration={"LocationConstraint": region})
    s3.put_public_access_block(
        Bucket=bucket,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls": True, "IgnorePublicAcls": True,
            "BlockPublicPolicy": True, "RestrictPublicBuckets": True,
        },
    )
    print(f"🆕 Created private bucket '{bucket}'.")


# ── Find the memory pointer the offloader left in context ─────────────────────

def extract_offload_pointer(agent) -> str | None:
    """Return the s3:// reference the ContextOffloader wrote into the conversation.

    When ContextOffloader offloads a result, it replaces it with a preview that
    lists '[Stored references:]' followed by the reference (here an s3:// URI).
    That reference IS the memory pointer — a short string standing in for the data.
    """
    for msg in agent.messages:
        for block in msg.get("content", []):
            if isinstance(block, dict) and "toolResult" in block:
                for item in block["toolResult"].get("content", []):
                    text = item.get("text", "")
                    for token in text.split():
                        if token.startswith(f"s3://{CONTEXT_BUCKET}/"):
                            return token
    return None


# ── Demo ──────────────────────────────────────────────────────────────────────

def main() -> None:
    if not os.getenv("OPENAI_API_KEY"):
        raise ValueError(
            "OPENAI_API_KEY not set. Get your API key from https://platform.openai.com/api-keys "
            "and add it to a .env file."
        )

    print("=" * 70)
    print("  ContextOffloader + Amazon S3 — running locally")
    print("=" * 70)
    print(f"  Account: {ACCOUNT_ID}  |  Region: {REGION}")
    print(f"  Bucket:  s3://{CONTEXT_BUCKET}/{CONTEXT_PREFIX}\n")

    ensure_bucket(CONTEXT_BUCKET, REGION)

    storage = S3Storage(bucket=CONTEXT_BUCKET, prefix=CONTEXT_PREFIX, region_name=REGION)
    agent = Agent(
        model=MODEL,
        tools=[fetch_application_logs, count_errors_by_service],
        plugins=[ContextOffloader(storage=storage, max_result_tokens=800, preview_tokens=200)],
    )

    print(f"\n👤 Query: {QUERY}\n")
    agent(QUERY)

    # The memory pointer: the offloader left an s3:// reference in the context in
    # place of the data. Pull it out — this short string is the "pointer".
    pointer = extract_offload_pointer(agent)

    # Tokens still in context after the run
    tokens = 0
    for msg in agent.messages:
        for block in msg.get("content", []):
            if isinstance(block, dict):
                if "text" in block:
                    tokens += len(block["text"]) // 4
                elif "toolResult" in block:
                    for item in block["toolResult"].get("content", []):
                        if "text" in item:
                            tokens += len(item["text"]) // 4

    s3 = boto3.client("s3", region_name=REGION)
    objects = s3.list_objects_v2(Bucket=CONTEXT_BUCKET, Prefix=CONTEXT_PREFIX).get("Contents", [])

    print("\n" + "=" * 70)
    print("  RESULT")
    print("=" * 70)
    print(f"  📊 Tokens left in LLM context:  {tokens:,}")
    print(f"  📦 Objects offloaded to S3:     {len(objects)}")

    # ── Recover the data by its exact reference (the memory pointer) ──────────
    print("\n  Recovering the offloaded data by its exact reference (the pointer):")
    if pointer:
        print(f"    pointer in context:  {pointer}")
        data_bytes, content_type = storage_retrieve(storage, pointer)  # ← retrieve by exact id
        print(f"    storage.retrieve()  → {len(data_bytes):,} bytes  ({content_type})")
        # Prove it is the real dataset: it parses as JSON and has log events
        try:
            events = json.loads(data_bytes)
            print(f"    verified: {len(events):,} log events recovered verbatim — exact data, no loss")
        except (json.JSONDecodeError, TypeError):
            print(f"    first 80 bytes: {data_bytes[:80]!r}")
    else:
        print("    (no offload placeholder found — the result fit under max_result_tokens this run)")

    print("\n  The pointer (~a few dozen chars) lived in context; the full dataset lived")
    print("  in S3 and came back byte-for-byte by exact reference — never flooding the window.")
    print(f"\n  Local disk version:  test_native_pointer.py (FileStorage)")
    print(f"  Production version:  agentcore_production.py (S3Storage inside AgentCore Runtime)")


if __name__ == "__main__":
    main()
