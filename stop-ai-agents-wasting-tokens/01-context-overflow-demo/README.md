# Fix AI Agent Context Window Overflow: Memory Pointer Pattern (IBM Research)

**Problem:** AI agents fail when tool outputs exceed the context window, preventing task completion.

**Solution:** Memory Pointer Pattern - Store large data outside context, interact with pointers instead of raw data.

Based on IBM Research paper: [Solving Context Window Overflow in AI Agents](https://arxiv.org/html/2511.22729v1)

---

## 🎯 What This Demo Shows

### Real-World Scenario: Log Analysis System

An AI agent processes application logs to detect errors and anomalies:

1. **Fetch logs** - Tool returns 24 hours of events (~86,400 events, >5MB)
2. **Analyze patterns** - Requires complete dataset (indivisible)
3. **Generate report** - Combines multiple analyses

**Why this matters:**
- Logs cannot be truncated without losing critical events
- Analysis requires full dataset for accuracy
- Common problem in DevOps/SRE workflows

---

![Without Memory Pointer vs Memory Pointer Pattern comparison](../images/Without-Memory-Pointer.jpg)

## 📊 Four Scenarios Demonstrated

| Scenario | Approach | Expected Result |
|----------|----------|-----------------|
| **1. Baseline** | No context management | ❌ Fails or degrades |
| **2. Memory Pointer** | IBM Research pattern | ✅ 7x token reduction |
| **3. Custom Window** | Smaller window (20 msgs) | ✅ Further optimization |
| **4. Per-Turn** | Proactive management | ✅ Complex workflows |
| **5. Swarm Multi-Agent** | Collector → Analyzer → Reporter | ✅ Autonomous coordination |

![Token usage comparison across context management strategies](../images/context-overflow-tokens.png)

---

## 🚀 Quick Start

### Prerequisites

```bash
# Python 3.9+
python --version

# OpenAI API key
export OPENAI_API_KEY="your-key-here"
```

> You can swap to any provider supported by Strands — see [Strands Model Providers](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/model-providers/) for configuration.

### Installation

```bash
uv venv && uv pip install -r requirements.txt
```

### Run Demo

```bash
# Single-agent demo (4 scenarios)
uv run python test_context_overflow.py

# Multi-agent Swarm demo (Collector → Analyzer → Reporter)
uv run python swarm_demo.py

# Quick test
uv run python quick_test.py

# Jupyter notebooks
# Open test_context_overflow.ipynb  (single-agent) or swarm_demo.ipynb (multi-agent)
# in Jupyter, Kiro, or your preferred notebook environment
```

---

## 📁 Files

| File | Purpose |
|------|---------|
| `tools.py` | Log analysis tools using `ToolContext` + `agent.state` for Memory Pointer Pattern |
| `test_context_overflow.py` | Single-agent demo with 4 scenarios |
| `test_context_overflow.ipynb` | Interactive single-agent notebook |
| `swarm_demo.py` | Multi-agent Swarm demo (Collector → Analyzer → Reporter) |
| `swarm_demo.ipynb` | Interactive Swarm notebook with follow-up investigation |
| `quick_test.py` | Quick smoke test |
| `requirements.txt` | Dependencies |

---

## 🔬 How It Works

### Problem: Large Tool Outputs

```python
# Tool returns 86,400 log events (~5MB JSON)
logs = fetch_application_logs("payment-service", hours=24)

# ❌ This overflows context window
agent.run("Analyze these logs: " + logs)
```

### Solution: Memory Pointer Pattern

```python
# 1. Tool stores large data in agent.state, returns pointer
@tool(context=True)
def fetch_application_logs(app_name: str, tool_context: ToolContext, hours: int = 24) -> str:
    logs = generate_logs(hours)  # Large dataset
    
    if len(logs) > threshold:
        pointer = f"logs-{app_name}"
        tool_context.agent.state.set(pointer, logs)
        return f"Data stored at: {pointer}"
    
    return logs

# 2. Agent receives pointer (small)
# "Fetched 86,400 events. Data stored at: logs-payment-service"

# 3. Next tool resolves pointer from agent.state
@tool(context=True)
def analyze_error_patterns(logs_pointer: str, tool_context: ToolContext) -> str:
    logs = tool_context.agent.state.get(logs_pointer)  # Get actual data
    # ... analyze full dataset
```

**Key Benefits:**
- ✅ No information loss
- ✅ 7x token reduction (paper result)
- ✅ Transparent to agent
- ✅ Works with any tool

---

## 🐝 Swarm Multi-Agent Demo

The same Memory Pointer Pattern works across multiple agents using [Strands Swarm](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/multi-agent/swarm/). Three specialized agents coordinate autonomously, sharing data via `invocation_state`:

```
Collector → Analyzer → Reporter
   │            │           │
   │ fetch logs │ analyze   │ generate
   │ store in   │ read from │ read from
   │ inv_state  │ inv_state │ inv_state
   └────────────┴───────────┘
    tool_context.invocation_state
         (145KB+, shared)
```

All tools use `@tool(context=True)` + `ToolContext` to access `invocation_state` — the official Strands API for [multi-agent data sharing](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/multi-agent/multi-agent-patterns/):

```python
from strands import Agent, tool, ToolContext
from strands.multiagent import Swarm

@tool(context=True)
def fetch_application_logs(app_name: str, tool_context: ToolContext, hours: int = 6) -> str:
    logs = generate_logs(hours)  # 145KB+
    pointer = f"logs-{app_name}"
    tool_context.invocation_state[pointer] = logs  # Shared across all agents
    return f"Stored as '{pointer}'. Hand off to analyzer."

@tool(context=True)
def analyze_error_patterns(logs_pointer: str, tool_context: ToolContext) -> str:
    logs = tool_context.invocation_state.get(logs_pointer)  # Read from shared state
    errors = [l for l in logs if l["level"] == "ERROR"]
    result = {"total_errors": len(errors), ...}
    tool_context.invocation_state["error_analysis"] = result
    return json.dumps(result)

collector = Agent(name="collector", tools=[fetch_application_logs], ...)
analyzer = Agent(name="analyzer", tools=[analyze_error_patterns, ...], ...)
reporter = Agent(name="reporter", tools=[generate_incident_report], ...)

swarm = Swarm([collector, analyzer, reporter], entry_point=collector)
result = swarm("Fetch logs, analyze, and generate incident report")
# Status: COMPLETED | Agents: collector → analyzer → reporter | ~14s
```

After the swarm completes, the data stays in `invocation_state` for follow-up investigation — no re-fetching needed.

**Key difference from single-agent:**
- Single-agent: `tool_context.agent.state` (scoped to one agent)
- Multi-agent: `tool_context.invocation_state` (shared across all agents in the swarm)

Both use the same `ToolContext` API — just different stores.

---

## 📊 Expected Results

### Scenario 1: Baseline (Fails)
```
❌ Context overflow or severe performance degradation
📊 Estimated tokens: 150,000+
```

### Scenario 2: Memory Pointer (Succeeds)
```
✅ Success
📊 Estimated tokens: ~20,000 (7x reduction)
📦 Memory store entries: 3
🔗 Memory Pointers:
  - fetch_logs-a3f2b1c8: 5,234,567 bytes
  - analyze_errors-f9d4e2a1: 12,345 bytes
```

### Scenario 3: Custom Window (Optimized)
```
✅ Success
📊 Estimated tokens: ~15,000
💬 Messages in window: 20
```

### Scenario 4: Per-Turn (Proactive)
```
✅ Success with proactive management
📊 Estimated tokens: ~18,000
```

---

## 🔑 Key Concepts

### 1. Context Window Overflow

**What happens:**
- Tool returns large output (>100KB)
- Agent tries to add to context
- Context window fills up
- Agent fails or performance degrades

**Why it matters:**
- Cannot truncate indivisible data (logs, matrices, datasets)
- Summarization loses critical information
- Blocks entire workflow

### 2. Memory Pointer Pattern

**How it works:**
1. **Store** - Large data stored in `agent.state`
2. **Pointer** - Tool returns small reference key
3. **Resolve** - Next tool reads from `agent.state` automatically
4. **Transparent** - Agent doesn't know it's using pointers

**From IBM Research:**
- 20M tokens → 1,234 tokens (Materials Science experiment)
- 6,411 tokens → 841 tokens (SDS extraction experiment)
- ~7x reduction in both cases

### 3. Sliding Window Conversation Manager

**Strands built-in solution:**
```python
from strands.agent.conversation_manager import SlidingWindowConversationManager

agent = Agent(
    model=OpenAIModel(model_id="gpt-4o-mini"),
    conversation_manager=SlidingWindowConversationManager(
        window_size=40,  # Keep last 40 messages
        per_turn=True    # Apply every model call
    ),
    tools=[...]
)
```

**Features:**
- Automatic trimming when window exceeds size
- Preserves tool pairs (toolUse + toolResult)
- Automatic retry on overflow
- Per-turn or per-N-calls management

---

## 🎓 Learning Objectives

After completing this demo, you will understand:

1. ✅ Why context overflow happens with large tool outputs
2. ✅ How Memory Pointer Pattern solves the problem
3. ✅ When to use different context management strategies
4. ✅ How to implement the pattern in your own agents
5. ✅ Trade-offs between different approaches

---

## 🔧 Customization

### Change Model Provider

```python
# Use Amazon Bedrock instead of OpenAI
from strands.models.bedrock import BedrockModel

agent = Agent(
    model=BedrockModel(
        model_id="anthropic.claude-3-haiku-20240307-v1:0",
        region="us-east-1"
    ),
    tools=[...]
)
```

See [Strands Model Providers](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/model-providers/) for all options.

### Adjust Log Size

```python
# In tools.py, change hours parameter
logs = fetch_application_logs("app-name", hours=48)  # 2 days
```

### Add Custom Tools

```python
from strands import tool, ToolContext

@tool(context=True)
def your_custom_tool(data_pointer: str, tool_context: ToolContext) -> str:
    """Your tool that works with pointers."""
    data = tool_context.agent.state.get(data_pointer)
    # ... process data
    return result
```

---

## 📚 References

### Research Papers
- [Solving Context Window Overflow in AI Agents](https://arxiv.org/html/2511.22729v1) — IBM Research, Nov 2025
- [Towards Effective GenAI Multi-Agent Collaboration](https://arxiv.org/pdf/2412.05449) — Amazon, Dec 2024. Payload referencing between agents
- [Context Window Limits Explained](https://airbyte.com/agentic-data/context-window-limit) — Airbyte, Dec 2025

### Strands Documentation
- [Agent State](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/agents/state/) — ToolContext and agent.state
- [Conversation Management](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/agents/conversation-management/) — Sliding window and context overflow
- [Swarm](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/multi-agent/swarm/) — Multi-agent orchestration

---

## 🐛 Troubleshooting

**"OPENAI_API_KEY not set"**
```bash
export OPENAI_API_KEY="your-key-here"
# Or create .env file with: OPENAI_API_KEY=your-key-here
```

**"Module not found: strands"**
```bash
pip install strands-agents
```

**OpenTelemetry warnings**
- Ignore "Failed to detach context" warnings
- They don't affect functionality

**Agent still fails with overflow**
- Reduce `hours` parameter in `fetch_application_logs()`
- Increase `window_size` in `SlidingWindowConversationManager`
- Check if Memory Pointer Pattern is working (look for "Data stored at:" in output)

---

## 💡 Next Steps

1. ✅ Complete this demo
2. ➡️ Try [Demo 02: MCP Tools Not Responding](../02-mcp-timeout-demo/) - Handle external APIs that stop responding
3. ➡️ Try [Demo 03: Reasoning Loops](../03-reasoning-loops-demo/) - Prevent infinite loops

---

## 📄 License

MIT-0 License. See [LICENSE](../../LICENSE) for details.
