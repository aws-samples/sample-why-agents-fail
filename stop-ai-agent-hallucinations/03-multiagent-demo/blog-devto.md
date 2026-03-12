---
title: "Multi-Agent Validation: How to Stop AI Agents from Hallucinating Silently"
published: true
tags: agents, ai, python, tutorial
series: Stop AI Agent Hallucinations
cover_image: https://raw.githubusercontent.com/aws-samples/sample-why-agents-fail/main/stop-ai-agent-hallucinations/03-multiagent-demo/images/single-vs-multi-agent-accuracy.png
---

> AI agents fail silently. They confirm operations that never completed, return
> success when tools returned errors, and fabricate responses with full confidence.
> A single agent has no mechanism to detect its own hallucinations — and no second
> opinion to catch them before they reach users.

Single-agent architectures have a fundamental blind spot: the agent that executes a task is the same one that reports the result. There's no cross-check, no validation layer, no audit trail. When the LLM misinterprets a tool error or substitutes a different result than what was requested, it does so silently — and the user receives a confident, wrong answer.

This is one of the most common failure patterns in AI systems today. Research ([Teaming LLMs to Detect and Mitigate Hallucinations, 2024](https://arxiv.org/pdf/2510.19507)) identifies it as a structural problem, not a model quality problem: you can't prompt your way out of it. The solution is architectural.

Multi-agent validation introduces a separation of concerns: one agent executes, another verifies, a third approves. Each handoff is a checkpoint. Hallucinations that would pass undetected in a single-agent system get caught — before they reach users — with an explicit `FAILED` status instead of a silent wrong answer.

In this post we build an **Executor → Validator → Critic** swarm using [Strands Agents](https://strandsagents.com), demonstrate the failure with a single agent, and show exactly where the multi-agent chain catches it.

---

## Series Overview

This is Part 3 of a four-part series on stopping AI agent hallucinations:

1. **[RAG vs Graph-RAG](#)** — Knowledge graphs prevent hallucinated aggregations
2. **[Semantic Tool Selection](#)** — Vector filtering reduces wrong tool choices
3. **Multi-Agent Validation** (this post) — Swarms catch hallucinations before they reach users
4. **[AI Agent Guardrails](https://dev.to/aws/ai-agent-guardrails-rules-that-llms-cannot-bypass-596d)** — Symbolic rules the LLM cannot bypass

---

## The Problem: Single Agents Have No Self-Correction

Research ([Teaming LLMs to Detect and Mitigate Hallucinations, 2024](https://arxiv.org/pdf/2510.19507)) identifies four failure patterns in single-agent systems:

- **Claim success when operations failed** — No validation layer catches execution errors
- **Use wrong tools for requests** — No cross-check verifies tool appropriateness
- **Fabricate responses** — No second opinion challenges generated content
- **Provide inaccurate statistics** — No verification against ground truth

The root cause is structural. A single agent operates in isolation: it calls a tool, receives a result, and decides what to tell the user — all in the same reasoning loop. If the tool returns an error and the LLM interprets it as recoverable, it will find a way to complete the task anyway. From the model's perspective, it solved the problem. From the user's perspective, it hallucinated.

```
User → Agent → Tools → Response
              ↑
     hallucination happens here, undetected
```

There is no layer between tool execution and user response that can challenge the agent's interpretation. The only way to add one is architecturally.

---

## The Solution: Executor → Validator → Critic

![Executor Validator Critic multi-agent pipeline](https://raw.githubusercontent.com/aws-samples/sample-why-agents-fail/main/stop-ai-agent-hallucinations/03-multiagent-demo/images/single-vs-multi-agent-accuracy.png)

Three specialized agents, each with a single responsibility:

| Agent | Role | What it checks |
|-------|------|----------------|
| **Executor** | Executes requests using tools | Completes the task, reports exactly what the tools returned |
| **Validator** | Reviews the execution | Was the correct tool used? Does the response match what was requested? |
| **Critic** | Final approval | APPROVED or REJECTED with explicit reasoning |

No agent trusts its own output. Every response passes through two independent checkpoints before reaching the user. Strands Agents handles the coordination through autonomous handoffs, shared context across the entire swarm, and explicit status tracking.

```
User → Executor → Validator → Critic → Response
         ↓            ↓          ↓
       Tools       VALID or   APPROVED or
                HALLUCINATION   REJECTED
```

---

## Implementation

### Step 1 — Define the Tools

Plain booking tools — no validation logic, no special handling for hallucinations:

```python
from strands import tool

HOTELS = {
    "grand_hotel":   {"price": 200, "available": True,  "max_guests": 4},
    "budget_inn":    {"price": 80,  "available": True,  "max_guests": 2},
    "luxury_resort": {"price": 500, "available": False, "max_guests": 6},
}

BOOKINGS = {}

@tool
def search_hotels(location: str, guests: int = 1) -> str:
    """Search available hotels in a location."""
    available = [
        f"{k}: ${v['price']}/night, max {v['max_guests']} guests"
        for k, v in HOTELS.items()
        if v["available"] and v["max_guests"] >= guests
    ]
    return f"Hotels in {location}: {available}" if available else "No hotels available"

@tool
def book_hotel(hotel_id: str, guest_name: str, nights: int = 1) -> str:
    """Book a hotel room."""
    if hotel_id not in HOTELS:
        return f"ERROR: Hotel '{hotel_id}' not found"
    if not HOTELS[hotel_id]["available"]:
        return f"ERROR: {hotel_id} is not available"
    total = HOTELS[hotel_id]["price"] * nights
    booking_id = f"BK{len(BOOKINGS)+1:03d}"
    BOOKINGS[booking_id] = {
        "hotel": hotel_id, "guest": guest_name,
        "nights": nights, "total": total
    }
    return f"SUCCESS: Booking {booking_id} confirmed — {hotel_id}, {nights} nights, ${total}"

@tool
def get_booking(booking_id: str) -> str:
    """Get booking details."""
    if booking_id not in BOOKINGS:
        return f"ERROR: Booking '{booking_id}' not found"
    b = BOOKINGS[booking_id]
    return f"Booking {booking_id}: {b['hotel']} for {b['guest']}, {b['nights']} nights, ${b['total']}"
```

The tools return explicit `ERROR:` messages. Whether the agent respects them is the entire question this demo answers.

### Step 2 — Baseline: Single Agent

```python
from strands import Agent
from strands.models.openai import OpenAIModel

# Using OpenAI-compatible interface via Strands SDK (not direct OpenAI usage)
MODEL = OpenAIModel(model_id="gpt-4o-mini")
# You can swap to any provider supported by Strands:
# https://strandsagents.com/latest/documentation/docs/user-guide/concepts/model-providers/

single_agent = Agent(
    name="single",
    system_prompt="You are a hotel booking assistant. Use tools to complete requests.",
    tools=[search_hotels, book_hotel, get_booking],
    model=MODEL
)
```

### Step 3 — Multi-Agent Swarm

```python
from strands.multiagent import Swarm

executor = Agent(
    name="executor",
    system_prompt="""Execute booking requests using tools.
After EVERY action, call handoff_to_agent to pass to 'validator'.""",
    tools=[search_hotels, book_hotel, get_booking],
    model=MODEL
)

validator = Agent(
    name="validator",
    system_prompt="""Validate booking responses. Check:
- Was the correct tool used?
- Is the response accurate and consistent with what was requested?
Say VALID or HALLUCINATION with reasons.
Then call handoff_to_agent to pass to 'critic'.""",
    model=MODEL
)

critic = Agent(
    name="critic",
    system_prompt="""Final review. Say APPROVED or REJECTED with reasoning.
You are the last agent — do NOT hand off.""",
    model=MODEL
)

swarm = Swarm([executor, validator, critic], entry_point=executor, max_handoffs=5)
```

Identical tools. Identical model. Identical task. The only structural difference is the validation chain.

### Why Strands Makes This Simple

The entire coordination layer — autonomous handoffs between agents, shared conversation context, and explicit status tracking — is handled by Strands with a single call:

```python
swarm = Swarm([executor, validator, critic], entry_point=executor, max_handoffs=5)
result = swarm("Book the_ritz_paris for Sarah for 3 nights")
print(result.status)  # COMPLETED or FAILED
```

No message-passing code. No handoff logic to write. No loop detection. You define what each agent does via `system_prompt`; Strands handles how they coordinate — including the `handoff_to_agent` tool built into every agent automatically.

→ [Strands Swarm Documentation](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/multi-agent/swarm/)

---

## Results

```
[TEST 1] Single Agent — Valid Booking
✓ Response: I've booked the grand_hotel for John for 2 nights...

[TEST 2] Single Agent — Invalid Hotel (non-existent hotel)
⚠️  Response: I've booked the grand_hotel in Paris for Sarah...
    (Agent hallucinated — changed hotel without warning)

[TEST 3] Multi-Agent — Valid Booking with Validation
✓ Flow: executor → validator → critic
✓ Status: COMPLETED

[TEST 4] Multi-Agent — Invalid Hotel Detection
✓ Flow: executor → validator → critic
✓ Status: FAILED
    (Correctly detected the invalid hotel)
```

| Scenario | Single Agent | Multi-Agent Swarm |
|----------|-------------|-------------------|
| Valid booking | ✅ Executes correctly | ✅ Executes and validated |
| Invalid hotel requested | ❌ Silently substitutes another hotel | ✅ Detected → `FAILED` |

In TEST 2, the booking tool returned `ERROR: Hotel not found`. The single agent silently substituted a different hotel and reported success. In TEST 4, the Validator identified the discrepancy between what was requested and what the Executor actually booked — and returned an explicit `FAILED` status.

---

## Why This Pattern Works

The Validator doesn't retry the operation. It reads the Executor's full output — including what tools were called and what they returned — and checks whether the result is consistent with the original request.

This is the key insight: **hallucinations are often consistent internally but inconsistent with the request**. The single agent's substitution was internally valid (the hotel exists, the booking succeeded). The problem was that it wasn't what the user asked for. Only a separate agent comparing the request against the result can catch that.

The Critic adds a second independent checkpoint, producing an explicit verdict that makes the system's confidence level visible — `APPROVED` or `REJECTED`, not just a response the user has to interpret.

---

## Considerations

**Advantages:**
- Hallucinations caught before reaching users
- Explicit `COMPLETED` / `FAILED` status — errors surfaced, not hidden
- Full audit trail through the agent chain
- Each agent focused on a single responsibility — easier to debug

**Challenges:**
- Higher latency — three LLM calls per request instead of one
- Validator quality depends on its system prompt clarity
- More complex to tune than a single-agent prompt
- Cost increases with the number of agents in the chain

**When to use it:**
Prioritize multi-agent validation for operations where silent errors are costly — bookings, payments, cancellations, data writes. For low-stakes read-only queries, a single agent is likely sufficient.

---

## What Comes Next

Multi-agent validation catches hallucinations in multi-step reasoning chains. But some violations are more fundamental: parameter limits, payment prerequisites, capacity constraints. These require rules that execute *before* any tool runs — outside LLM control entirely.

[Part 4](https://dev.to/aws/ai-agent-guardrails-rules-that-llms-cannot-bypass-596d) covers neurosymbolic guardrails: symbolic rules enforced at the framework level via Strands Hooks, that the LLM cannot bypass regardless of how the user phrases the request.

---

## Key Takeaways

- Single agents have no self-correction mechanism — hallucinations go undetected by design
- The Executor → Validator → Critic pattern introduces cross-validation at every step
- Strands Swarm handles autonomous handoffs with shared context and explicit status tracking
- Identical tools and model — the difference is architectural, not model-dependent
- `Status.FAILED` makes errors explicit instead of returning a confident wrong answer
- Best applied to high-stakes operations where silent substitution has real consequences

---

## Run It Yourself

```bash
git clone https://github.com/aws-samples/sample-why-agents-fail
cd stop-ai-agent-hallucinations/03-multiagent-demo
uv venv && uv pip install -r requirements.txt
uv run test_multiagent_hallucinations.py
```

> You can swap to any provider supported by Strands — see [Strands Model Providers](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/model-providers/) for configuration.

---

## References

### Research
- [Teaming LLMs to Detect and Mitigate Hallucinations (2024)](https://arxiv.org/pdf/2510.19507)
- [Markov Chain Multi-Agent Debate (2024)](https://arxiv.org/html/2406.03075v1)
- [RAG-KG-IL: Multi-Agent Hybrid Framework](https://arxiv.org/pdf/2503.13514)

### Strands Agents
- [Strands Swarm](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/multi-agent/swarm/) — Multi-agent orchestration with autonomous handoffs
- [Multi-Agent Patterns](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/multi-agent/multi-agent-patterns/) — Shared state across agents
- [Strands Model Providers](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/model-providers/) — Swap to Bedrock, Anthropic, Ollama
- [Strands Agents Documentation](https://strandsagents.com) — Full framework docs

### Code
- [Code Repository](https://github.com/aws-samples/sample-why-agents-fail)
