# AI Agent Guardrails That Self-Correct Instead of Block

> Strands Hooks block rule violations with `cancel_tool` — the agent reports failure and the user must retry. Agent Control goes further: it **steers** the agent to fix the problem and complete the task, instead of just failing.

![Hooks (Block) vs Agent Control (Self-Correct) comparison](./images/hooks-vs-agent-control.jpg)

Based on: [Strands Agents with Agent Control](https://strandsagents.com/blog/strands-agents-with-agent-control/)

> This demo uses Strands Agents and Agent Control. Similar guardrail patterns can be applied with other agent frameworks that support lifecycle hooks.

---

## The Problem with Blocking

[Demo 04 (Neurosymbolic Guardrails)](../04-neurosymbolic-demo/) showed that Strands Hooks can enforce business rules at the tool level. When a rule is violated, `cancel_tool` blocks the call and the agent tells the user it cannot proceed.

But blocking is a blunt instrument. If a user requests 15 guests and the maximum is 10, the agent could adjust to 10 and complete the booking. Instead, with hooks alone, it asks the user to change their request — interrupting the flow.

## The Solution: Steer Instead of Block

![Agent Control steer flow: User Request → LLM → Agent Control server evaluates → Self-Correct → Final Response](./images/Agent-Control.jpg)

[Agent Control](https://github.com/agentcontrol/agent-control) introduces **steer controls** — server-managed policies that guide the agent to self-correct when a violation is detected, instead of terminating the operation:

```
Hooks:          15 guests → BLOCKED → "Would you like to adjust?" (flow stopped)
Agent Control:  15 guests → Guide("reduce to 10") → retries → BK002 confirmed (flow completed)
```

## How It Differs from Hooks

| | Hooks ([Demo 04](../04-neurosymbolic-demo/)) | Agent Control (this demo) |
|---|---|---|
| Where rules live | Python code (`rules.py`) | Server — API/dashboard |
| When a rule fails | `cancel_tool = "BLOCKED"` → agent fails | `Guide("reduce to 10")` → agent retries corrected |
| To change a rule | Edit code, redeploy | API call or dashboard — no code changes |
| Integration | `HookProvider` + `hooks=[...]` | `Plugin` + `plugins=[...]` |
| Evaluators | Custom Python lambdas | regex, list, JSON schema, AI (Galileo Luna-2) |
| Scope | `BeforeToolCallEvent` only | LLM input/output, tool input/output, pre/post |

## The Tools

Three booking tools in `tools.py` — clean, no validation logic:

| Tool | What it does | Key behavior |
|------|-------------|--------------|
| `book_hotel(hotel, check_in, check_out, guests)` | Books a hotel room | Returns `"SUCCESS: Booking BK001..."` — no guest limit in the tool |
| `process_payment(amount, booking_id)` | Processes payment | Returns `"SUCCESS"` or `"ERROR: Booking not found"` |
| `confirm_booking(booking_id)` | Confirms a booking | Returns `"SUCCESS: Confirmed BK001"` |

The tools do NOT enforce the max-guests rule. That is the guardrail layer's job — either Hooks or Agent Control.

**Strands Agents makes this simple** — Agent Control integrates as a Plugin with two lines:

```python
# Hooks (existing approach — block):
agent = Agent(tools=[...], hooks=[MaxGuestsHook()])

# Agent Control (new approach — steer):
agent = Agent(tools=[...], plugins=[AgentControlPlugin(...), AgentControlSteeringHandler(...)])
```

## What We Test

Same query, same tools, same model — only the guardrail changes:

| Test | Guardrail | Outcome |
|------|-----------|---------|
| 1 — Hooks | `MaxGuestsHook` with `cancel_tool` | Agent is BLOCKED → asks user what to do |
| 2 — Agent Control | `AgentControlSteeringHandler` with `Guide()` | Agent self-corrects to 10 guests → booking completes |

---

## Two Ways to Define Controls

| Mode | Best for | How it works |
|------|----------|-------------|
| **Server** (this demo) | Teams, production, dashboard management | Controls live on the Agent Control server — change via API or dashboard without redeploying |
| **Local YAML** | Quick prototyping, single-developer projects | Controls defined in a `controls.yaml` file — no server needed, `agent_control.init(controls_file="controls.yaml")` |

This demo uses the **server approach**. See the [Agent Control docs](https://docs.agentcontrol.dev/) for YAML-based local mode or server setup instructions.

---

## Prerequisites

- Python 3.9+
- OpenAI API key (or any [Strands-supported provider](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/model-providers/))
- [Agent Control server](https://docs.agentcontrol.dev/) running locally (see [setup instructions](https://github.com/agentcontrol/agent-control))

---

## Quick Start

### 1. Start Agent Control server

Follow the [Agent Control setup instructions](https://github.com/agentcontrol/agent-control) to start the server locally.

```bash
# Verify it's running
curl http://localhost:8000/health
```

### 2. Install dependencies

```bash
uv venv && uv pip install -r requirements.txt
```

### 3. Configure API key

```bash
# Create .env with your OpenAI key
echo "OPENAI_API_KEY=your-key-here" > .env
```

### 4. Setup controls on the server

```bash
uv run setup_controls.py
```

### 5. Run the comparison

```bash
uv run test_hooks_vs_control.py
```

Or open `test_hooks_vs_control.ipynb` in Jupyter, Kiro, or your preferred notebook environment.

---

## Controls Created by setup_controls.py

| Control | Type | Scope | What it does |
|---------|------|-------|-------------|
| `steer-max-guests` | STEER | LLM output (post) | Guides agent to reduce guest count to <= 10 and inform the user |
| `deny-no-payment` | DENY | Tool input (pre) on `confirm_booking` | Blocks booking confirmation without payment |

---

## Expected Output

```
Test 1 — Hooks:          "Would you like to adjust the number of guests?"  (blocked)
Test 2 — Agent Control:  "Adjusted to 10 guests. Booking ID: BK002."      (self-corrected)
```

---

## Cleanup

Stop the Agent Control server following the [shutdown instructions](https://docs.agentcontrol.dev/).

---

## Files

| File | Purpose |
|------|---------|
| `tools.py` | Booking tools — clean, no validation logic |
| `setup_controls.py` | Creates steer + deny controls on Agent Control server |
| `test_hooks_vs_control.py` | Runs both approaches on the same query, compares results |
| `test_hooks_vs_control.ipynb` | Interactive notebook version |
| `requirements.txt` | Dependencies |

---

## References

### Research
- [ATA: Autonomous Trustworthy Agents (2024)](https://arxiv.org/html/2510.16381v1) — Guardrail failure patterns in AI agents
- [Enhancing LLMs through Neuro-Symbolic Integration](https://arxiv.org/pdf/2504.07640v1) — Combining neural + symbolic reasoning

### Strands Agents
- [Strands Agents with Agent Control](https://strandsagents.com/blog/strands-agents-with-agent-control/) — Blog announcement
- [Agent Control Plugin](https://strandsagents.com/docs/community/plugins/agent-control/) — Strands integration docs
- [Strands Hooks](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/agents/hooks/) — `BeforeToolCallEvent`, `cancel_tool`
- [Strands Steering](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/plugins/steering/) — `Guide`, `Proceed`, `SteeringHandler`
- [Strands Model Providers](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/model-providers/) — Swap to Amazon Bedrock, Anthropic, Ollama

### Agent Control
- [Agent Control GitHub](https://github.com/agentcontrol/agent-control) — Open source, Apache 2.0
- [Agent Control Docs](https://docs.agentcontrol.dev/) — Server setup and API reference

---

## Contributing

Contributions are welcome! See [CONTRIBUTING](../../CONTRIBUTING.md) for more information.

---

## Security

If you discover a potential security issue in this project, notify AWS/Amazon Security via the [vulnerability reporting page](http://aws.amazon.com/security/vulnerability-reporting/). Please do **not** create a public GitHub issue.

---

## License

This library is licensed under the MIT-0 License. See the [LICENSE](../../LICENSE) file for details.
