"""Hook for preventing reasoning loops (when agents repeatedly call the same tool).

`LimitToolCounts` is the official recipe from the Strands Hooks Cookbook — copied
here verbatim, not a custom class. Strands does not ship it as an importable symbol;
the Cookbook shows the code so you paste it into your own project.

Recipe: https://strandsagents.com/docs/user-guide/concepts/agents/hooks/ (see "Cookbook → Limit Tool Counts")
"""

from threading import Lock
from strands.hooks import HookProvider, HookRegistry, BeforeToolCallEvent, BeforeInvocationEvent


class LimitToolCounts(HookProvider):
    """Limits the number of times tools can be called per agent invocation.

    Official recipe from the Strands Hooks Cookbook. When a tool exceeds its limit,
    subsequent calls are cancelled via BeforeToolCallEvent.cancel_tool, so the agent
    cannot exceed the ceiling regardless of LLM behavior.
    """

    def __init__(self, max_tool_counts: dict[str, int]):
        """Initializer.

        Args:
            max_tool_counts: A dictionary mapping tool names to max call counts for
                tools. If a tool is not specified in it, the tool can be called as many
                times as desired.
        """
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
