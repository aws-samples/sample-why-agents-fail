# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0
"""Log-analysis agent with two kinds of memory — AgentCore Runtime entry point.

This is the production version of the local context-overflow demos. It runs INSIDE
AgentCore Runtime and combines two distinct, separate memories:

  1. Conversation memory  → AgentCore Memory (STM_AND_LTM)
       Turns, user preferences, extracted facts. Recalled by SEMANTIC similarity.
       Wired via AgentCoreMemorySessionManager (actor_id from the request header).

  2. Context / data memory → Amazon S3 (ContextOffloader + S3Storage)
       Large tool outputs (logs, datasets). Recalled by EXACT reference (s3://...).
       The Runtime's execution role writes/reads the bucket — that is why the role
       needs S3 permissions (granted in setup_agentcore_s3.ipynb).

Why logs go to S3, not AgentCore Memory: AgentCore Memory recalls the semantically
most-similar memory, which is wrong for "give me that exact log dataset back". Logs
need exact-id object storage; conversation needs semantic recall. Two memories, each
doing what it is good at.

Model: this Runtime uses Amazon Bedrock (Claude) so NO API key needs to live in the
container — the execution role authenticates to AWS. The local demos use OpenAI;
the only thing that changes for production is the model and the storage backend.

This demo uses Strands Agents on Amazon Bedrock AgentCore. The two-memory split is a
general agent design and carries over to other frameworks.

Deploy with the starter toolkit — see setup_agentcore_s3.ipynb.
"""

import os

from bedrock_agentcore import BedrockAgentCoreApp, RequestContext
from bedrock_agentcore.memory.integrations.strands.config import (
    AgentCoreMemoryConfig,
    RetrievalConfig,
)
from bedrock_agentcore.memory.integrations.strands.session_manager import (
    AgentCoreMemorySessionManager,
)
from strands import Agent
from strands.models import BedrockModel
from strands.vended_plugins.context_offloader import ContextOffloader, S3Storage

from native_tools import fetch_application_logs, count_errors_by_service

# --- Configuration from environment variables (set at deploy time) ---

REGION = os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))
MEMORY_ID = os.environ.get("BEDROCK_AGENTCORE_MEMORY_ID")  # conversation memory
CONTEXT_BUCKET = os.environ["CONTEXT_BUCKET"]              # S3 data memory
CONTEXT_PREFIX = os.environ.get("CONTEXT_PREFIX", "log-artifacts/")

# Actor ID arrives as a custom HTTP header (AgentCore lowercases header names)
CUSTOM_HEADER_NAME = "x-amzn-bedrock-agentcore-runtime-custom-actor-id"

SYSTEM_PROMPT = (
    "You are an SRE incident assistant with long-term memory. Fetch and analyze "
    "application logs and explain error patterns clearly. Remember the user's "
    "preferences across sessions.\n\n"
    "Large tool outputs are offloaded to external storage — work from the provided "
    "previews and summaries, and only retrieve full content when you genuinely need it."
)

app = BedrockAgentCoreApp()

# Cached across invocations in the same container
_agent = None


def get_or_create_agent(actor_id: str, session_id: str) -> Agent:
    """Build the agent once per container, wiring both memories."""
    global _agent
    if _agent is not None:
        return _agent

    model = BedrockModel(region_name=REGION)

    # Conversation memory — AgentCore Memory (semantic recall, scoped by actor_id)
    memory_config = AgentCoreMemoryConfig(
        memory_id=MEMORY_ID,
        session_id=session_id,
        actor_id=actor_id,
        retrieval_config={
            f"/preferences/{actor_id}/": RetrievalConfig(top_k=5, relevance_score=0.7),
            f"/summaries/{actor_id}/{session_id}/": RetrievalConfig(top_k=3, relevance_score=0.5),
        },
    )
    session_manager = AgentCoreMemorySessionManager(memory_config, REGION)

    # Context / data memory — S3 via ContextOffloader (exact-reference retrieval).
    # Same plugin as the local demo; only the backend changes to S3Storage.
    offloader = ContextOffloader(
        storage=S3Storage(bucket=CONTEXT_BUCKET, prefix=CONTEXT_PREFIX, region_name=REGION),
        max_result_tokens=1500,
        preview_tokens=750,
    )

    _agent = Agent(
        model=model,
        tools=[fetch_application_logs, count_errors_by_service],
        system_prompt=SYSTEM_PROMPT,
        session_manager=session_manager,  # conversation memory
        plugins=[offloader],               # context/data memory
    )
    return _agent


@app.entrypoint
def invoke(payload, context: RequestContext = None):
    """Entry point for AgentCore Runtime invocations."""
    if not MEMORY_ID:
        return {"error": "Set BEDROCK_AGENTCORE_MEMORY_ID (see setup_agentcore_s3.ipynb)."}

    actor_id = "default-user"
    if context and getattr(context, "request_headers", None):
        actor_id = context.request_headers.get(CUSTOM_HEADER_NAME, "default-user")
    session_id = context.session_id if context and hasattr(context, "session_id") else "default-session"

    agent = get_or_create_agent(actor_id, session_id)

    prompt = payload if isinstance(payload, str) else payload.get("prompt", "")
    result = agent(prompt)
    return {"response": result.message.get("content", [{}])[0].get("text", str(result))}


if __name__ == "__main__":
    app.run()
