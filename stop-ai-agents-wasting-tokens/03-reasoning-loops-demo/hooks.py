"""Hooks for detecting and preventing reasoning loops (when agents repeatedly call the same tool without making progress).

Uses Strands Hooks API:
- BeforeToolCallEvent.cancel_tool to block duplicate calls
- BeforeInvocationEvent to reset state per invocation
- LimitToolCounts pattern from Strands Hooks Cookbook

See: https://strandsagents.com/latest/documentation/docs/user-guide/concepts/agents/hooks/
"""

from threading import Lock
from strands.hooks import HookProvider, HookRegistry, BeforeToolCallEvent, BeforeInvocationEvent


class DebounceHook(HookProvider):
    """Detects and blocks duplicate tool calls in a sliding window.

    Based on research: agents call the same tool repeatedly without progress.
    Uses BeforeToolCallEvent.cancel_tool to prevent execution.
    """

    def __init__(self, window_size=3):
        self._lock = Lock()
        self.call_history = []
        self.window_size = window_size
        self.blocked_count = 0

    def register_hooks(self, registry: HookRegistry) -> None:
        registry.add_callback(BeforeInvocationEvent, self.reset)
        registry.add_callback(BeforeToolCallEvent, self.check_duplicate)

    def reset(self, event: BeforeInvocationEvent) -> None:
        with self._lock:
            self.call_history = []
            self.blocked_count = 0

    def check_duplicate(self, event: BeforeToolCallEvent) -> None:
        key = (event.tool_use["name"], str(event.tool_use["input"]))
        with self._lock:
            recent = self.call_history[-self.window_size:]

            count = recent.count(key)
            if count >= 2:
                self.blocked_count += 1
                event.cancel_tool = f"BLOCKED: Duplicate call — {event.tool_use['name']} called {count} times with same input"
                print(f"🚫 Loop detected! Blocked duplicate call to {event.tool_use['name']}")
                return

            self.call_history.append(key)

    def get_stats(self):
        with self._lock:
            return {
                "total_calls": len(self.call_history),
                "blocked_calls": self.blocked_count,
                "unique_calls": len(set(self.call_history)),
            }


class LimitToolCounts(HookProvider):
    """Limits the number of times tools can be called per invocation.

    From Strands Hooks Cookbook — prevents runaway tool usage.
    See: https://strandsagents.com/latest/documentation/docs/user-guide/concepts/agents/hooks/
    """

    def __init__(self, max_tool_counts: dict[str, int]):
        self.max_tool_counts = max_tool_counts
        self.tool_counts = {}
        self._lock = Lock()

    def register_hooks(self, registry: HookRegistry) -> None:
        registry.add_callback(BeforeInvocationEvent, self.reset_counts)
        registry.add_callback(BeforeToolCallEvent, self.intercept_tool)

    def reset_counts(self, event: BeforeInvocationEvent) -> None:
        with self._lock:
            self.tool_counts = {}

    def intercept_tool(self, event: BeforeToolCallEvent) -> None:
        tool_name = event.tool_use["name"]
        with self._lock:
            max_count = self.max_tool_counts.get(tool_name)
            count = self.tool_counts.get(tool_name, 0) + 1
            self.tool_counts[tool_name] = count

            if max_count and count > max_count:
                event.cancel_tool = (
                    f"Tool '{tool_name}' has been invoked {count} times (limit: {max_count}). "
                    f"DO NOT CALL THIS TOOL ANYMORE."
                )
                print(f"🚫 Limit reached! {tool_name} blocked after {max_count} calls")
