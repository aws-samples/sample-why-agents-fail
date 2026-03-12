"""
Demo: Context Window Overflow with Large Tool Outputs

Based on IBM Research paper "Solving Context Window Overflow in AI Agents"
https://arxiv.org/html/2511.22729v1

This demo shows how agents fail when tool outputs are too large and how
to fix it using the Memory Pointer Pattern.
"""

import os
from dotenv import load_dotenv
from strands import Agent
# Using OpenAI-compatible interface via Strands SDK (not direct OpenAI usage)
from strands.models.openai import OpenAIModel
from strands.agent.conversation_manager import SlidingWindowConversationManager
from tools import (
    fetch_application_logs,
    analyze_error_patterns,
    detect_latency_anomalies,
    generate_incident_report
)
from strands_tools import calculator

load_dotenv()

# Ensure OpenAI API key is set
if not os.getenv("OPENAI_API_KEY"):
    raise ValueError(
        "OPENAI_API_KEY not set. Get your API key from https://platform.openai.com/api-keys "
        "then either: 1) Add OPENAI_API_KEY=your-key to a .env file, or "
        "2) Run: export OPENAI_API_KEY=your-key"
    )

def count_tokens(text: str) -> int:
    """Rough token count estimation (1 token ≈ 4 chars)."""
    return len(text) // 4

def run_scenario_1_baseline():
    """
    Scenario 1: BASELINE (FAILS)
    
    No context management. Agent tries to process large log dataset
    directly in context window. Will fail with context overflow.
    """
    print("\n" + "="*70)
    print("SCENARIO 1: BASELINE (No Context Management)")
    print("="*70)
    print("Expected: Context overflow or performance degradation\n")
    
    # Create agent WITHOUT conversation manager
    agent = Agent(
        model=OpenAIModel(model_id="gpt-4o-mini"),
        tools=[
            fetch_application_logs,
            analyze_error_patterns,
            calculator
        ]
    )
    
    # Reduced from 24 to 6 hours for faster execution
    query = (
        "Fetch 6 hours of logs for 'payment-service' and analyze error patterns. "
        "Report services with more than 20 errors."
    )
    
    print(f"Query: {query}\n")
    
    try:
        response = agent(query)
        print(f"Response: {response}")
        
        # Estimate token usage (simplified - just count response)
        tokens = count_tokens(query + str(response))
        print(f"\n📊 Estimated tokens: {tokens:,}")
        
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}: {str(e)[:200]}")

def run_scenario_2_memory_pointer():
    """
    Scenario 2: MEMORY POINTER PATTERN (SUCCEEDS)
    
    Uses memory pointers to store large data outside context window.
    Agent interacts with pointers instead of raw data.
    
    Based on IBM Research paper approach.
    """
    print("\n" + "="*70)
    print("SCENARIO 2: MEMORY POINTER PATTERN (IBM Research)")
    print("="*70)
    print("Expected: Success with 7x token reduction\n")
    
    # Clear memory store
    
    # Create agent with sliding window
    agent = Agent(
        model=OpenAIModel(model_id="gpt-4o-mini"),
        conversation_manager=SlidingWindowConversationManager(window_size=40),
        tools=[
            fetch_application_logs,
            analyze_error_patterns,
            detect_latency_anomalies,
            generate_incident_report,
            calculator
        ]
    )
    
    # Reduced from 24 to 12 hours for faster execution
    query = (
        "Fetch 12 hours of logs for 'payment-service', analyze error patterns "
        "and detect latency anomalies. Generate an incident report."
    )
    
    print(f"Query: {query}\n")
    
    try:
        response = agent(query)
        print(f"Response: {response}")
        
        # Calculate token usage (simplified)
        tokens = count_tokens(query + str(response))
        print(f"\n📊 Estimated tokens: {tokens:,}")
        print(f"📦 agent.state entries: {len(agent.state._data)}")  # _data is internal; no public len() API yet
        
        # Show memory pointers
        if agent.state._data:  # _data is internal; no public iteration API yet
            print("\n🔗 Memory Pointers in agent.state:")
            for pointer, data in agent.state._data.items():
                size = len(str(data))
                print(f"  - {pointer}: {size:,} bytes")
        
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}: {str(e)[:200]}")

def run_scenario_3_custom_window():
    """
    Scenario 3: CUSTOM SLIDING WINDOW
    
    Uses smaller window size (20 messages) for more aggressive pruning.
    """
    print("\n" + "="*70)
    print("SCENARIO 3: CUSTOM SLIDING WINDOW (20 messages)")
    print("="*70)
    print("Expected: Success with even lower token usage\n")
    
    agent = Agent(
        model=OpenAIModel(model_id="gpt-4o-mini"),
        conversation_manager=SlidingWindowConversationManager(window_size=20),
        tools=[
            fetch_application_logs,
            analyze_error_patterns,
            calculator
        ]
    )
    
    # Reduced from 12 to 6 hours for faster execution
    query = "Fetch 6 hours of logs for 'api-gateway' and analyze error patterns."
    
    print(f"Query: {query}\n")
    
    try:
        response = agent(query)
        print(f"Response: {response}")
        
        tokens = count_tokens(query + str(response))
        print(f"\n📊 Estimated tokens: {tokens:,}")
        
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}: {str(e)[:200]}")

def run_scenario_4_per_turn():
    """
    Scenario 4: PER-TURN MANAGEMENT
    
    Applies context management proactively every N model calls.
    Useful for agents with many tool operations.
    
    Note: per_turn parameter may not be available in current Strands version.
    """
    print("\n" + "="*70)
    print("SCENARIO 4: PER-TURN MANAGEMENT (Every 3 calls)")
    print("="*70)
    print("Expected: Proactive context management during execution\n")
    
    # Try with per_turn, fallback to basic if not supported
    try:
        agent = Agent(
            model=OpenAIModel(model_id="gpt-4o-mini"),
            conversation_manager=SlidingWindowConversationManager(
                window_size=30,
                per_turn=3  # Manage every 3 model calls
            ),
            tools=[
                fetch_application_logs,
                analyze_error_patterns,
                detect_latency_anomalies,
                calculator
            ]
        )
    except TypeError:
        print("⚠️  per_turn parameter not supported, using basic sliding window\n")
        agent = Agent(
            model=OpenAIModel(model_id="gpt-4o-mini"),
            conversation_manager=SlidingWindowConversationManager(window_size=30),
            tools=[
                fetch_application_logs,
                analyze_error_patterns,
                detect_latency_anomalies,
                calculator
            ]
        )
    
    # Reduced from 6 to 3 hours for faster execution
    query = (
        "Fetch 3 hours of logs for 'auth-service', analyze errors, "
        "and detect latency anomalies."
    )
    
    print(f"Query: {query}\n")
    
    try:
        response = agent(query)
        print(f"Response: {response}")
        
        tokens = count_tokens(query + str(response))
        print(f"\n📊 Estimated tokens: {tokens:,}")
        
    except Exception as e:
        print(f"❌ FAILED: {type(e).__name__}: {str(e)[:200]}")

def run_comparison():
    """
    Run all scenarios and compare results.
    """
    print("\n" + "="*70)
    print("CONTEXT OVERFLOW DEMO - LOG ANALYSIS SYSTEM")
    print("="*70)
    print("\nBased on IBM Research: 'Solving Context Window Overflow in AI Agents'")
    print("Paper: https://arxiv.org/html/2511.22729v1\n")
    
    scenarios = [
        ("Baseline (No Management)", run_scenario_1_baseline),
        ("Memory Pointer Pattern", run_scenario_2_memory_pointer),
        ("Custom Window (20 msgs)", run_scenario_3_custom_window),
        ("Per-Turn Management", run_scenario_4_per_turn)
    ]
    
    for name, func in scenarios:
        try:
            func()
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Scenario failed: {e}")
    
    print("\n" + "="*70)
    print("DEMO COMPLETE")
    print("="*70)
    print("\n📊 Key Findings:")
    print("  1. Baseline fails or uses excessive tokens")
    print("  2. Memory Pointer Pattern: ~7x token reduction")
    print("  3. Custom window: Further optimization possible")
    print("  4. Per-turn: Proactive management for complex workflows")
    print("\n💡 Recommendation: Use Memory Pointer Pattern for large tool outputs")

if __name__ == "__main__":
    run_comparison()
