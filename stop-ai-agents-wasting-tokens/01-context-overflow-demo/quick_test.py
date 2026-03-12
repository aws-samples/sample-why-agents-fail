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
    pointer = "logs-payment-service"
    stored = agent.state.get(pointer)
    if stored:
        print(f"📦 agent.state['{pointer}']: {len(str(stored)):,} bytes")
            
except Exception as e:
    print(f"\n❌ Error: {type(e).__name__}: {e}")
