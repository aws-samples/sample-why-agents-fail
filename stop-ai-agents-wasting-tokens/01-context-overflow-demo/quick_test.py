"""Quick test of Memory Pointer Pattern using Strands agent.state"""

import os
from dotenv import load_dotenv
from strands import Agent
from strands.models.openai import OpenAIModel
from strands.agent.conversation_manager import SlidingWindowConversationManager
from tools import fetch_application_logs, analyze_error_patterns

load_dotenv()

print("Testing Memory Pointer Pattern with agent.state...\n")

agent = Agent(
    model=OpenAIModel(model_id="gpt-4o-mini"),
    conversation_manager=SlidingWindowConversationManager(window_size=40),
    tools=[fetch_application_logs, analyze_error_patterns]
)

query = "Fetch 6 hours of logs for 'payment-service' and count total errors"

print(f"Query: {query}\n")
print("Running agent...\n")

try:
    response = agent(query)
    print(f"\n✅ Response: {response}\n")
    print(f"📦 Memory pointers in agent.state: {len(agent.state._data)}")  # _data is internal; no public len() API yet

    for pointer in agent.state._data:  # _data is internal; no public iteration API yet
        data = agent.state.get(pointer)
        print(f"  - {pointer}: {len(str(data)):,} bytes")
            
except Exception as e:
    print(f"\n❌ Error: {type(e).__name__}: {e}")
