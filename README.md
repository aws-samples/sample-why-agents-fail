# 🤖 Why AI Agents Fail (And How to Fix Them)


[![GitHub stars](https://img.shields.io/github/stars/build-on-aws/why-agents-fail.svg?style=for-the-badge&logo=github&color=yellow)](https://github.com/build-on-aws/why-agents-fail/stargazers) [![License](https://img.shields.io/badge/License-MIT--0-blue.svg?style=for-the-badge)](LICENSE) [![Python](https://img.shields.io/badge/Python-3.9+-green.svg?style=for-the-badge&logo=python)](https://python.org) [![AWS](https://img.shields.io/badge/AWS-Bedrock-orange.svg?style=for-the-badge&logo=amazon-aws)](https://aws.amazon.com/bedrock/) [![Strands](https://img.shields.io/badge/🧬-Strands_Agents-blue.svg?style=for-the-badge)](https://strandsagents.com)


*Research-backed solutions to the three critical failure modes that break AI agents in production: hallucinations, timeouts, and memory loss.*

⭐ Star this repository

---

## 🎯 Learning Path: Understand → Prevent → Scale

This repository demonstrates research-backed techniques for preventing AI agent failures with working code examples.

| 🚨 Failure Mode | 💡 Solution Approach | 📊 Projects | ⏱️ Total Time |
|----------------|---------------------|-------------|---------------|
| **[Hallucinations](#-stop-ai-agent-hallucinations)** | Detection and mitigation through 4 techniques | 4 demos | 2 hours |
| **Timeouts** | Context management and async patterns | Coming soon | - |
| **Memory Loss** | Persistent memory and context retrieval | Coming soon | - |

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

## Why Your Agent Times Out

*(Coming soon)*

---

## Your Agent Doesn't Remember You

*(Coming soon)*

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
- LLM access: OpenAI (default), AWS Bedrock, Anthropic, or Ollama
- `OPENAI_API_KEY` environment variable (for default setup)
- AWS CLI configured if using Bedrock (`aws configure`)
- Basic understanding of AI agents and tool calling

**Model Configuration:**
All demos use OpenAI with GPT-4o-mini by default. You can swap to any provider supported by Strands — see [Strands Model Providers](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/model-providers/) for configuration.

**AWS Credentials Setup (if using Bedrock):**
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
| Neo4j (local) | Free | Graph database for demos | [Neo4j Community](https://neo4j.com/download/) |
| FAISS (local) | Free | Vector search library | Open source |
| SentenceTransformers | Free | Local embeddings | Open source |

> 💡 All demos can run locally with minimal costs. OpenAI GPT-4o-mini is the most cost-effective option for testing.

---

## 📖 Additional Learning Resources

- [Strands Agents Documentation](https://strandsagents.com) - Framework documentation and model providers
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock?trk=87c4c426-cddf-4799-a299-273337552ad8&sc_channel=el) - LLM service guide and model access
- [Neo4j Graph Database Guide](https://neo4j.com/docs/) - Graph database setup and Cypher queries


---

<div align="center">

**⭐ Star this repository** • **📖 [Start Learning](stop-ai-agent-hallucinations/)**

</div>


---

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

---

## 📄 License

This library is licensed under the MIT-0 License. See the [LICENSE](LICENSE) file for details.


