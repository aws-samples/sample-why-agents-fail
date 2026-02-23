## 🚀 Stop AI Agent Hallucinations: 4 Essential Techniques

[![GitHub stars](https://img.shields.io/github/stars/your-org/DevEx-Agent-Hallucinations.svg?style=for-the-badge&logo=github&color=yellow)](https://github.com/your-org/DevEx-Agent-Hallucinations/stargazers) [![License](https://img.shields.io/badge/License-MIT--0-blue.svg?style=for-the-badge)](LICENSE) [![Python](https://img.shields.io/badge/Python-3.9+-green.svg?style=for-the-badge&logo=python)](https://python.org) [![AWS](https://img.shields.io/badge/AWS-Bedrock-orange.svg?style=for-the-badge&logo=amazon-aws)](https://aws.amazon.com/bedrock/) [![Strands](https://img.shields.io/badge/🧬-Strands_Agents-blue.svg?style=for-the-badge)](https://strandsagents.com)

*Research-backed techniques to stop AI agent hallucinations: Graph-RAG for precise data retrieval, semantic tool selection for accurate tool choice, neurosymbolic guardrails for rule enforcement, and multi-agent validation for error detection.*

⭐ Star this repository

---

## 📓 Hallucination Prevention Demos

| 📓 Demo | 🎯 Focus & Key Learning | ⏱️ Time | 📊 Level |
|---------|------------------------|----------|----------|
| **01 - [Graph-RAG vs Traditional RAG](01-faq-graphrag-demo/)** | Structured data retrieval - Compare RAG vs Graph-RAG on 300 hotel FAQs, Neo4j knowledge graph with auto entity extraction, eliminate hallucinations | 30 min | ![Beginner](https://img.shields.io/badge/-Beginner-brightgreen) |
| **02 - [Semantic Tool Selection with FAISS](02-semantic-tools-demo/)** | Intelligent tool filtering - Filter 31 tools to top 3 relevant, reduce errors by 75% and token costs by 89%, dynamic tool swapping | 45 min | ![Intermediate](https://img.shields.io/badge/-Intermediate-yellow) |
| **03 - [Multi-Agent Validation Pattern](03-multiagent-demo/)** | Cross-validation workflows - Executor → Validator → Critic pattern catches hallucinations, Strands Swarm orchestration | 30 min | ![Intermediate](https://img.shields.io/badge/-Intermediate-yellow) |
| **04 - [Neurosymbolic Rule Enforcement](04-neurosymbolic-demo/)** | Symbolic validation - Compare prompt engineering vs symbolic rules, 100% business rule compliance, LLM cannot bypass | 20 min | ![Advanced](https://img.shields.io/badge/-Advanced-red) |

---

## 🔧 Technologies Used

<details>

| 🔧 Technology | 🎯 Purpose | ⚡ Key Capabilities |
|---------------|------------|---------------------|
| **[Strands Agents](https://strandsagents.com)** | AI agent framework | Dynamic tool swapping, multi-agent orchestration, conversation memory |
| **[Amazon Bedrock](https://aws.amazon.com/bedrock/)** | LLM access | Claude 3 Haiku for agent reasoning and tool calling |
| **[Neo4j](https://neo4j.com)** | Graph database | Relationship-aware queries, precise aggregations, multi-hop traversal |
| **[FAISS](https://github.com/facebookresearch/faiss)** | Vector search | Semantic similarity, tool filtering, efficient nearest neighbor search |
| **[SentenceTransformers](https://www.sbert.net/)** | Embeddings | Text embeddings for semantic tool selection |

</details>

---


## 🎯 Prerequisites

**Before You Begin:**
- Python 3.9+ installed locally
- LLM access: OpenAI (default), AWS Bedrock, Anthropic, or Ollama
- `OPENAI_API_KEY` environment variable (for default setup)
- AWS CLI configured if using Bedrock (`aws configure`)
- Basic understanding of AI agents and tool calling

**Model Configuration:**
All demos use OpenAI with GPT-4o-mini by default. You can swap to any provider supported by Strands — see [Strands Model Providers](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/model-providers/) for configuration.

**AWS Credentials Setup (if using Bedrock):**
Follow the [AWS credentials configuration guide](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html) to configure your environment.

---

## 🚀 Quick Start Guide

### 1. **Clone Repository**
```bash
git clone https://github.com/your-org/DevEx-Agent-Hallucinations.git
cd 01-faq-graphrag-demo
```

### 2. **Choose a Demo** (Start with Graph-RAG)
```bash
cd 01-faq-graphrag-demo

# Install dependencies
uv venv && uv pip install -r requirements.txt

# Extract data
unzip hotel-faqs.zip -d data/
```

### 3. **Run Demo**
```bash
# Build data stores first
uv run load_vector_data.py  # FAISS index
uv run build_graph.py       # Neo4j knowledge graph

# Run comparison
uv run travel_agent_demo.py
```

### 4. **Explore Other Techniques**
```bash
cd ../02-semantic-tools-demo  # Semantic tool selection
cd ../03-multiagent-demo      # Multi-agent validation
cd ../04-neurosymbolic-demo   # Neurosymbolic rules
```

---

## 📝 Key Findings

1. **Graph-RAG eliminates statistical hallucinations** - Structured knowledge graph provides precise answers instead of LLM inference 
2. **Semantic tool selection detects hallucinations up to 86.4%** - Research shows filtering tools before agent sees them significantly reduces errors ([Internal Representations paper](https://arxiv.org/abs/2601.05214))
3. **Token costs reduced by 89%** - Filtering 31 tools to top 3 reduces tokens from 4,500 to 500 per query (demo results)
4. **Neurosymbolic rules enforce 100% compliance** - Symbolic validation at tool level cannot be bypassed by prompt engineering (demo results)
5. **Multi-agent validation catches hallucinations** - Cross-validation through specialized agent roles detects errors before reaching users (demo results)

---

## 📚 Research Background

Based on recent papers:
- [MetaRAG: Metamorphic Testing for Hallucination Detection](https://arxiv.org/pdf/2509.09360)
- [Internal Representations as Indicators of Hallucinations in Agent Tool Selection](https://arxiv.org/abs/2601.05214) 
- [Teaming LLMs to Detect and Mitigate Hallucinations](https://arxiv.org/pdf/2510.19507) 
- [RAG-KG-IL: Multi-Agent Hybrid Framework](https://arxiv.org/pdf/2503.13514) 

---

## 📖 Additional Learning Resources

- [Complete Blog Post](blog-series/blog-unified-hallucinations.md) - Detailed guide with all 4 techniques and code examples
- [Strands Agents Documentation](https://strandsagents.com) - Framework documentation and model providers
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/) - LLM service guide and model access
- [Neo4j Graph Database Guide](https://neo4j.com/docs/) - Graph database setup and Cypher queries

---

<div align="center">

**⭐ Star this repository** • **📖 [Start Learning](01-faq-graphrag-demo/)**

</div>

---

## 🔍 Troubleshooting

**OpenTelemetry warnings**: Ignore "Failed to detach context" warnings - they don't affect functionality

**AWS credentials**: Ensure credentials are configured with Bedrock access and appropriate permissions

**Model alternatives**: All demos work with OpenAI, Anthropic, or Ollama - see [Strands Model Providers](https://strandsagents.com/latest/documentation/docs/user-guide/concepts/model-providers/)

**Neo4j setup**: Graph-RAG demo requires Neo4j database. See [01-faq-graphrag-demo/README.md](01-faq-graphrag-demo/README.md) for setup instructions

---

## 📄 License

This library is licensed under the MIT-0 License. See the [LICENSE](LICENSE) file for details.
