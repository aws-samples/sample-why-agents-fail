# 🤖 Why AI Agents Fail (And How to Fix Them)


[![GitHub stars](https://img.shields.io/github/stars/aws-samples/sample-why-agents-fail.svg?style=for-the-badge&logo=github&color=yellow)](https://github.com/aws-samples/sample-why-agents-fail/stargazers) [![License](https://img.shields.io/badge/License-MIT--0-blue.svg?style=for-the-badge)](LICENSE) [![Python](https://img.shields.io/badge/Python-3.9+-green.svg?style=for-the-badge&logo=python)](https://python.org) [![AWS](https://img.shields.io/badge/AWS-Bedrock-orange.svg?style=for-the-badge&logo=amazon-aws)](https://aws.amazon.com/bedrock/) [![Strands](https://img.shields.io/badge/🧬-Strands_Agents-blue.svg?style=for-the-badge)](https://strandsagents.com)


*Research-backed solutions to the three critical failure modes that break AI agents in production: hallucinations, timeouts, and memory loss.*

⭐ **[Star this repository](https://github.com/aws-samples/sample-why-agents-fail)**

---

## 🎯 Learning Path: Understand → Prevent → Scale

This repository demonstrates research-backed techniques for preventing AI agent failures with working code examples.

| 🚨 Failure Mode | 💡 Solution Approach | 📊 Projects | ⏱️ Total Time |
|----------------|---------------------|-------------|---------------|
| **[Hallucinations](#-stop-ai-agent-hallucinations)** | Detection and mitigation through 4 techniques | 4 demos | 2 hours |
| **[Getting Stuck](#-stop-agents-from-wasting-tokens)** | Conversation management, context overflow, MCP timeouts, reasoning loops | 4 demos | 1.75 hours |
| **[Memory Loss](#-stop-agents-from-losing-memory)** | Memory decay, core memory pattern, semantic retrieval | 3 demos | 1.5 hours |

---

## 🎭 Stop AI Agent Hallucinations

**The Problem**: Agents fabricate statistics, choose wrong tools, ignore business rules, and claim success when operations fail.

**The Solution**: 4 research-backed techniques that detect, contain, and mitigate hallucinations before they cause damage.

### 📓 Hallucination Prevention Demos

| 📓 Demo | 🎯 Focus & Key Learning | ⏱️ Time | 📊 Level |
|---------|------------------------|----------|----------|
| **01 - [Graph-RAG vs Traditional RAG](stop-ai-agent-hallucinations/01-faq-graphrag-demo/)** | Structured data retrieval - Compare RAG vs Graph-RAG on 300 hotel FAQs, Neo4j knowledge graph with auto entity extraction, eliminate statistical hallucinations | 30 min | ![Intermediate](https://img.shields.io/badge/-Intermediate-yellow) |
| **02 - [Semantic Tool Selection](stop-ai-agent-hallucinations/02-semantic-tools-demo/)** | Intelligent tool filtering - Filter 31 tools to top 3 relevant, reduce errors and token costs, dynamic tool swapping | 45 min | ![Intermediate](https://img.shields.io/badge/-Intermediate-yellow) |
| **03 - [Multi-Agent Validation Pattern](stop-ai-agent-hallucinations/03-multiagent-demo/)** | Cross-validation workflows - Executor → Validator → Critic pattern catches hallucinations, Strands Swarm orchestration | 30 min | ![Intermediate](https://img.shields.io/badge/-Intermediate-yellow) |
| **04 - [Neurosymbolic Guardrails for AI Agents](stop-ai-agent-hallucinations/04-neurosymbolic-demo/)** | Symbolic validation - Compare prompt engineering vs symbolic rules, business rule compliance, LLM cannot bypass | 20 min |![Intermediate](https://img.shields.io/badge/-Intermediate-yellow) |

### 📊 Key Results

| 🎯 Technique | 📈 Improvement | 🔍 Metric |
|--------------|----------------|-----------|
| **Graph-RAG** | Accuracy | Precise queries on 300 hotel FAQs via knowledge graph |
| **Semantic Tool Selection** | Reduce errors and token costs | Tool selection hallucination detection (research validated), Token cost per query |
| **Neurosymbolic Rules** | Compliance | Business rule enforcement - LLM cannot bypass |
| **Multi-Agent Validation** | Detects errors | Invalid operation detection before reaching users |

**[→ Explore hallucination prevention demos](stop-ai-agent-hallucinations/)**

---

## 🔄 Stop Agents from Wasting Tokens

**The Problem**: Agents get stuck when context windows overflow with large data, MCP tools stop responding on slow APIs, or agents repeat the same tool calls without making progress — burning tokens and blocking workflows.

**The Solution**: start with built-in conversation management, then apply techniques that prevent context overflow, handle unresponsive APIs, and stop reasoning loops before they waste resources.

### 📓 Token Waste & Stuck Agent Demos

| 📓 Demo | 🎯 Focus & Key Learning | ⏱️ Time | 📊 Level |
|---------|------------------------|----------|----------|
| **00 - [Conversation Management](stop-ai-agents-wasting-tokens/00-conversation-management-demo/)** | The built-in default — compare Strands' four conversation managers (None, Sliding Window, Summarization, Combination) on the same recall question; a one-line default before reaching for advanced patterns | 15 min | ![Beginner](https://img.shields.io/badge/-Beginner-green) |
| **01 - [Context Window Overflow](stop-ai-agents-wasting-tokens/01-context-overflow-demo/)** | Memory management — store large data outside context with the Memory Pointer Pattern (manual `agent.state` + native `ContextOffloader`), recall by ID (~97% fewer context tokens in this demo; IBM Research reports ~7x on their workloads) | 30 min | ![Intermediate](https://img.shields.io/badge/-Intermediate-yellow) |
| **02 - [MCP Tools Not Responding](stop-ai-agents-wasting-tokens/02-mcp-timeout-demo/)** | Async patterns — Handle slow/unresponsive APIs with async handleId, prevent 424 errors, immediate responses | 20 min | ![Intermediate](https://img.shields.io/badge/-Intermediate-yellow) |
| **03 - [Reasoning Loops](stop-ai-agents-wasting-tokens/03-reasoning-loops-demo/)** | Loop prevention — clear SUCCESS/FAILED tool states stop retries, `LimitToolCounts` (Strands Hooks Cookbook) enforces a hard call ceiling | 25 min | ![Intermediate](https://img.shields.io/badge/-Intermediate-yellow) |

**[→ Explore token waste prevention demos](stop-ai-agents-wasting-tokens/)**

---

## 🧠 Stop Agents from Losing Memory

**The Problem**: Agents forget user preferences between turns, treat returning users as strangers, and waste tokens loading irrelevant memories when context grows large.

**The Solution**: 3 research-backed techniques that prevent memory decay, implement core memory for personalization, and retrieve only relevant memories at scale.

### 📓 Memory Loss Prevention Demos

| 📓 Demo | 🎯 Focus & Key Learning | ⏱️ Time | 📊 Level |
|---------|------------------------|----------|----------|
| **01 - [Memory Decay](stop-ai-agents-losing-memory/01-memory-decay-demo/)** | Persistent state — Compare stateless vs stateful agents, `agent.state` for preferences, `FileSessionManager` for cross-session persistence | 30 min | ![Intermediate](https://img.shields.io/badge/-Intermediate-yellow) |
| **02 - [Core Memory Pattern](stop-ai-agents-losing-memory/02-core-memory-demo/)** | Structured memory — Agent-managed read/write/update tools (MIRIX/MemGPT pattern), memory evolution, cross-session persistence | 30 min | ![Intermediate](https://img.shields.io/badge/-Intermediate-yellow) |
| **03 - [Memory Retrieval](stop-ai-agents-losing-memory/03-memory-retrieval-demo/)** | Smart retrieval — Dump-all vs keyword vs semantic search over 8 memory sections, 60-98% token savings | 25 min | ![Intermediate](https://img.shields.io/badge/-Intermediate-yellow) |

**[→ Explore memory loss prevention demos](stop-ai-agents-losing-memory/)**

---

## 🔧 Technologies Used

<details>

| 🔧 Technology | 🎯 Purpose | ⚡ Key Capabilities |
|---------------|------------|---------------------|
| **[Strands Agents](https://strandsagents.com)** | AI agent framework | Dynamic tool swapping, multi-agent orchestration, conversation memory, hooks system |
| **[Amazon Bedrock](https://aws.amazon.com/bedrock/)** | LLM access | Claude 3 Haiku/Sonnet for agent reasoning and tool calling |
| **[Neo4j](https://neo4j.com)** | Graph database | Relationship-aware queries, precise aggregations, multi-hop traversal |
| **[FAISS](https://github.com/facebookresearch/faiss)** | Vector search | Semantic similarity, tool filtering, efficient nearest neighbor search |
| **[SentenceTransformers](https://www.sbert.net/)** | Embeddings | Text embeddings for semantic tool selection and memory retrieval |

</details>

---

## Prerequisites

**Before You Begin:**
- Python 3.9+ installed locally
- LLM access: OpenAI (default), Amazon Bedrock, Anthropic, or Ollama
- `OPENAI_API_KEY` environment variable (for default setup)
- AWS CLI configured if using Amazon Bedrock (`aws configure`)
- Basic understanding of AI agents and tool calling

**Model Configuration:**
All demos use OpenAI with GPT-4o-mini by default. You can swap to any provider supported by Strands — see [Strands Model Providers](https://strandsagents.com/docs/user-guide/concepts/model-providers/) for configuration.

**AWS Credentials Setup (if using Amazon Bedrock):**
Follow the [AWS credentials configuration guide](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html?trk=87c4c426-cddf-4799-a299-273337552ad8&sc_channel=el) to configure your environment.

---

## 🚀 Quick Start Guide

### 1. **Clone Repository**
```bash
git clone https://github.com/aws-samples/sample-why-agents-fail
cd sample-why-agents-fail
```

### 2. **Start with Hallucinations**
```bash
cd stop-ai-agent-hallucinations
```

### 3. **Explore All Techniques**
Each demo folder contains detailed README files and working code examples.

---

## 💰 Cost Estimation

| 💰 Service | 💵 Approximate Cost | 📊 Usage Pattern | 🔗 Pricing Link |
|-------------|---------------------|------------------|------------------|
| OpenAI GPT-4o-mini | ~$0.15 per 1M input tokens | Agent reasoning and tool calling | [OpenAI Pricing](https://openai.com/pricing) |
| Amazon Bedrock (Claude) | ~$0.25 per 1M input tokens | Alternative LLM provider | [Bedrock Pricing](https://aws.amazon.com/bedrock/pricing/) |
| Neo4j (local) | Free | Graph database for demos | [Neo4j Pricing](https://neo4j.com/pricing/) |
| FAISS (local) | Free | Vector search library | [FAISS GitHub](https://github.com/facebookresearch/faiss) |
| SentenceTransformers | Free | Local embeddings | [SBERT Docs](https://www.sbert.net/) |

> 💡 All demos can run locally with minimal costs. OpenAI GPT-4o-mini is the most cost-effective option for testing.

---

## 📖 Additional Learning Resources

- [Strands Agents Documentation](https://strandsagents.com) - Framework documentation and model providers
- [Amazon Bedrock Documentation](https://docs.aws.amazon.com/bedrock?trk=87c4c426-cddf-4799-a299-273337552ad8&sc_channel=el) - LLM service guide and model access
- [Search for tools in your AgentCore gateway with a natural language query](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-using-mcp-semantic-search.html)
- [Neo4j Graph Database Guide](https://neo4j.com/docs/) - Graph database setup and Cypher queries



---

<div align="center">

**⭐ **[Star this repository](https://github.com/aws-samples/sample-why-agents-fail)**** • **📖 [Start Learning](stop-ai-agent-hallucinations/)**

</div>


---

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING](CONTRIBUTING.md) for more information.

---

## Security

If you discover a potential security issue in this project, notify AWS/Amazon Security via the [vulnerability reporting page](https://aws.amazon.com/security/vulnerability-reporting/). Please do **not** create a public GitHub issue.

---

## 📄 License

This library is licensed under the MIT-0 License. See the [LICENSE](LICENSE) file for details.


