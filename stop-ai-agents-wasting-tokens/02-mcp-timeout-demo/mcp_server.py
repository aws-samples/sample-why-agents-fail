"""Simple MCP server that simulates real timeout scenarios from research."""

import asyncio
import uuid
from mcp.server import FastMCP

# Create MCP server
mcp = FastMCP("Timeout Scenarios Server")

# Store for async jobs
JOBS = {}

@mcp.tool(description="Fast API - responds immediately")
async def fast_api(query: str) -> str:
    """Simulates a fast, reliable API."""
    await asyncio.sleep(1)
    return f"SUCCESS: Fast response for '{query}'"

@mcp.tool(description="Slow API - takes 15 seconds, causes poor UX")
async def slow_api(query: str) -> str:
    """Simulates slow external API (e.g., database query, file processing)."""
    await asyncio.sleep(15)
    return f"SUCCESS: Slow response for '{query}' after 15s"

@mcp.tool(description="Unresponsive API - stops responding indefinitely, never completes")
async def unresponsive_api(query: str) -> str:
    """Simulates an unresponsive API - request accepted but never completes.

    This represents the real problem from research:
    - Request neither succeeds nor fails
    - Agent waits indefinitely
    - Requires session restart

    An API that accepts requests but never completes them, leaving the caller in an unresponsive state.
    """
    # Simulate accepting request but never completing
    await asyncio.sleep(300)  # 5 minutes - effectively infinite
    return f"This will never be reached for '{query}'"

@mcp.tool(description="Failing API - returns error after delay")
async def failing_api(query: str) -> str:
    """Simulates API that fails after processing.
    
    Represents 424 Failed Dependency error from research.
    """
    await asyncio.sleep(5)
    raise Exception("424 Failed Dependency: External service unavailable")

@mcp.tool(description="Start long-running job - returns handle immediately")
async def start_long_job(task: str) -> str:
    """Async pattern solution: Return handle immediately.
    
    Based on research: 'Return immediately with handleId'
    Prevents timeout by responding ASAP.
    """
    job_id = str(uuid.uuid4())[:8]
    
    # Store job (in real scenario, this would start background worker)
    JOBS[job_id] = {
        "status": "processing",
        "task": task,
        "result": None
    }
    
    # Simulate background processing
    async def process_job():
        await asyncio.sleep(10)  # Long processing
        JOBS[job_id]["status"] = "completed"
        JOBS[job_id]["result"] = f"Processed: {task}"
    
    asyncio.create_task(process_job())
    
    return f"JOB_STARTED: {job_id} - Use check_job_status to get result"

@mcp.tool(description="Check status of long-running job")
async def check_job_status(job_id: str) -> str:
    """Check status of async job.
    
    Part of async pattern solution from research.
    """
    if job_id not in JOBS:
        return f"ERROR: Job {job_id} not found"
    
    job = JOBS[job_id]
    
    if job["status"] == "processing":
        return f"PROCESSING: Job {job_id} still running"
    elif job["status"] == "completed":
        return f"COMPLETED: {job['result']}"
    else:
        return f"UNKNOWN: Job {job_id} in unknown state"

if __name__ == "__main__":
    mcp.run(transport="stdio")
