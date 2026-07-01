"""
Interactive chat to demonstrate conversation management live (built for recording).

Chat normally, then watch the active strategy curate the context window after
every turn. Switch strategies mid-conversation to show, on camera, how Sliding
Window forgets an early fact while Summarization / Combination keep it.

Run:
    uv run chat.py                 # starts on the Combination strategy
    uv run chat.py sliding         # start on a specific strategy

Commands (type inside the chat):
    /strategy none|sliding|summary|combination   switch strategy (keeps history)
    /compact       force summarization/trim now (summary triggers on overflow)
    /context       print the current managed history
    /reset         clear the conversation
    /help          list commands
    /quit          exit

Suggested recording script (run the SAME conversation under two strategies):
    1. /strategy sliding
    2. "My deploy budget is $500/month, remember it."
    3. Chat 5-6 filler turns to bury it (watch the status line trim messages).
    4. "What is my monthly deploy budget?" → it has forgotten.
    5. /reset  → /strategy combination
    6. Repeat steps 2-3, then /compact
    7. "What is my monthly deploy budget?" → it remembers.

Note: switching to Combination AFTER Sliding Window has already trimmed the fact
cannot bring it back — the data is gone. That is why the honest comparison resets
and replays the conversation under each strategy.

This demo uses Strands Agents. Sliding window, summarization, and combination
are general agent concepts and carry over to other agent frameworks.
"""

import os
import sys
from dotenv import load_dotenv
from strands import Agent
# Using OpenAI-compatible interface via Strands SDK (not direct OpenAI usage)
from strands.models.openai import OpenAIModel
from strands.agent.conversation_manager import (
    NullConversationManager,
    SlidingWindowConversationManager,
    SummarizingConversationManager,
)

# Suppress noisy OpenTelemetry warnings
os.environ["OTEL_SDK_DISABLED"] = "true"

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    raise ValueError(
        "OPENAI_API_KEY not set. Get your API key from https://platform.openai.com/api-keys "
        "then either: 1) Add OPENAI_API_KEY=your-key to a .env file, or "
        "2) Run: export OPENAI_API_KEY=your-key"
    )

MODEL = OpenAIModel(model_id="gpt-4o-mini")

# Tunable strategy parameters (shown in the status line so the recording is self-documenting).
SLIDING_WINDOW = 6          # messages kept by Sliding Window
SUMMARY_RATIO = 0.5         # fraction of oldest messages summarized (Combination)
PRESERVE_RECENT = 4         # recent messages kept verbatim (Combination)

SYSTEM_PROMPT = "You are a concise assistant. Remember facts the user tells you and answer briefly."


# ── ANSI colors (kept simple for terminal recordings) ─────────────────────────
DIM = "\033[2m"
BOLD = "\033[1m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RESET = "\033[0m"


def make_manager(strategy: str):
    """Return a fresh conversation manager for the named strategy, plus whether it summarizes."""
    if strategy == "none":
        return NullConversationManager(), False, "keep the full history"
    if strategy == "sliding":
        return (
            SlidingWindowConversationManager(window_size=SLIDING_WINDOW),
            False,
            f"keep the last {SLIDING_WINDOW} messages",
        )
    if strategy == "summary":
        return (
            SummarizingConversationManager(summary_ratio=0.8, preserve_recent_messages=0),
            True,
            "summarize old, keep none verbatim",
        )
    if strategy == "combination":
        return (
            SummarizingConversationManager(
                summary_ratio=SUMMARY_RATIO, preserve_recent_messages=PRESERVE_RECENT
            ),
            True,
            f"summary of old + last {PRESERVE_RECENT} verbatim",
        )
    raise ValueError(f"Unknown strategy: {strategy}")


class ChatSession:
    """Holds the conversation and rebuilds the agent when the strategy changes."""

    def __init__(self, strategy: str):
        self.messages = []
        self.set_strategy(strategy, announce=False)

    def set_strategy(self, strategy: str, announce: bool = True):
        manager, summarizes, desc = make_manager(strategy)
        self.strategy = strategy
        self.summarizes = summarizes
        self.desc = desc
        # Rebuild the agent with the new manager, carrying over the current history.
        self.agent = Agent(
            model=MODEL,
            system_prompt=SYSTEM_PROMPT,
            conversation_manager=manager,
            callback_handler=None,  # we print the answer ourselves for clean output
        )
        self.agent.messages = self.messages
        if announce:
            print(f"{YELLOW}→ strategy: {strategy} ({desc}){RESET}")

    def send(self, text: str):
        """Send a user turn, print the answer and a live context status line."""
        before = len(self.agent.messages)
        response = self.agent(text)
        self.messages = self.agent.messages  # manager may have curated in place
        after = len(self.messages)

        answer = str(response).strip()
        tokens = 0
        if response.metrics and response.metrics.accumulated_usage:
            tokens = response.metrics.accumulated_usage["totalTokens"]

        print(f"{CYAN}bot>{RESET} {answer}")
        trimmed = f" (trimmed {before + 2 - after} msgs)" if after < before + 2 else ""
        print(
            f"{DIM}[{self.strategy} · {after} msgs in context · "
            f"{tokens:,} tokens this turn{trimmed}]{RESET}"
        )

    def compact(self):
        """Force the manager to compact now (summary triggers on overflow in production)."""
        before = len(self.messages)
        try:
            self.agent.conversation_manager.reduce_context(self.agent)
        except Exception as exc:  # e.g. Null manager cannot reduce
            print(f"{YELLOW}Cannot compact with '{self.strategy}': {exc}{RESET}")
            return
        self.messages = self.agent.messages
        after = len(self.messages)
        print(f"{YELLOW}→ compacted: {before} → {after} messages{RESET}")

    def show_context(self):
        """Print the current managed history so viewers see what the model actually reads."""
        print(f"{BOLD}--- context ({len(self.messages)} messages) ---{RESET}")
        for msg in self.messages:
            role = msg.get("role", "?")
            text = " ".join(
                block.get("text", "")
                for block in msg.get("content", [])
                if isinstance(block, dict)
            )
            snippet = text[:100] + ("…" if len(text) > 100 else "")
            print(f"  {role:>9}: {snippet}")
        print(f"{BOLD}--- end context ---{RESET}")

    def reset(self):
        self.messages = []
        self.set_strategy(self.strategy, announce=False)
        print(f"{YELLOW}→ conversation cleared{RESET}")


HELP = """
Commands:
  /strategy none|sliding|summary|combination   switch strategy (keeps history)
  /compact     force summarization/trim now
  /context     print the current managed history
  /reset       clear the conversation
  /help        show this help
  /quit        exit
"""


def main():
    strategy = sys.argv[1] if len(sys.argv) > 1 else "combination"
    if strategy not in ("none", "sliding", "summary", "combination"):
        print(f"Unknown strategy '{strategy}'. Use: none | sliding | summary | combination")
        sys.exit(1)

    print("=" * 70)
    print(f"{BOLD}  Conversation Management — live chat demo{RESET}")
    print("=" * 70)
    print("  Chat, then watch the active strategy curate the context after each turn.")
    print("  Type /help for commands, /quit to exit.")
    print(f"  Sliding keeps {SLIDING_WINDOW} msgs · Combination = summary + last {PRESERVE_RECENT}.")

    session = ChatSession(strategy)
    print(f"\n{YELLOW}→ strategy: {session.strategy} ({session.desc}){RESET}")

    while True:
        try:
            text = input(f"\n{GREEN}you>{RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye")
            break

        if not text:
            continue

        if text in ("/quit", "/exit"):
            print("bye")
            break
        if text == "/help":
            print(HELP)
            continue
        if text == "/context":
            session.show_context()
            continue
        if text == "/compact":
            session.compact()
            continue
        if text == "/reset":
            session.reset()
            continue
        if text.startswith("/strategy"):
            parts = text.split()
            if len(parts) != 2 or parts[1] not in ("none", "sliding", "summary", "combination"):
                print("Usage: /strategy none|sliding|summary|combination")
            else:
                session.set_strategy(parts[1])
            continue
        if text.startswith("/"):
            print(f"Unknown command: {text}. Type /help.")
            continue

        session.send(text)


if __name__ == "__main__":
    main()
