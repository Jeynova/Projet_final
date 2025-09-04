# 🚀 AgentForge - Clean Agentic System

## 📁 New Clean Structure

```
AgentForge/
├── agentic/                          # 🎯 NEW: Clean agentic system
│   ├── __init__.py
│   ├── simple_agentic_graph.py       # Main pipeline orchestration
│   ├── agents/
│   │   ├── __init__.py
│   │   └── base_agent.py             # Agent base classes
│   ├── memory/
│   │   ├── __init__.py
│   │   └── memory_agent.py           # RAG memory system
│   └── webapp/
│       └── app_agentic.py            # Flask web interface
├── orchestrator/                     # 🔒 OLD: Deterministic approach
│   ├── README.md                     # Explains why it's archived
│   └── ... (old template-based files)
├── test_clean_agentic.py            # Test script for new system
└── ... (other existing files)
```

## ✅ What You Need Now

**Only 2 files matter:**

1. **`agentic/simple_agentic_graph.py`** - CLI/test version
2. **`agentic/webapp/app_agentic.py`** - Web interface

## 🚀 Quick Start

### CLI Usage
```bash
# Set environment variable
$env:AGENTFORGE_LLM = "ollama"

# Run directly
python agentic/simple_agentic_graph.py

# Or run test
python test_clean_agentic.py
```

### Web Interface
```bash
# Set environment variable
$env:AGENTFORGE_LLM = "ollama"

# Start web server
python agentic/webapp/app_agentic.py

# Open browser
# http://localhost:5001
```

## 🎯 Key Improvements

### ✅ Clean Architecture
- **Modular design** - Each component in its own file
- **Clear separation** - Agents, memory, webapp separate
- **No code duplication** - Reusable components
- **Easy to extend** - Add new agent types easily

### ✅ Working Features
- **4 specialized agents** (Dev, Arch, QA + Memory)
- **Democratic decision making** - Agents vote on tech choices  
- **Peer review system** - Agents review each other's code
- **RAG memory** - Learns from successful patterns
- **Real-time web monitoring** - Live WebSocket updates
- **ZIP download** - Complete project packages

### ✅ Honest Documentation
- **No over-promises** - Only documents what works
- **Clear requirements** - AGENTFORGE_LLM=ollama needed
- **Realistic features** - V1 vs V2 roadmap separation

## 🔧 Environment Setup

**Critical:** The system needs this environment variable:

```powershell
# Windows PowerShell
$env:AGENTFORGE_LLM = "ollama"

# Then run either:
python agentic/simple_agentic_graph.py           # CLI
python agentic/webapp/app_agentic.py             # Web
```

Without this, system runs in "mock" mode (no real AI).

## 📊 Comparison: Old vs New

| Aspect | Old (`orchestrator/`) | New (`agentic/`) |
|--------|----------------------|------------------|
| **Approach** | Template-based, deterministic | AI agents, collaborative |
| **Flexibility** | Rigid templates | Adaptive to context |
| **Learning** | None | RAG memory system |
| **Collaboration** | None | Agents vote & review |
| **Maintenance** | High (many templates) | Low (self-improving) |
| **Code Quality** | Fixed patterns | Peer-reviewed |

## 🎯 Next Steps

1. **Test the new system:**
   ```bash
   python test_clean_agentic.py
   ```

2. **Use for real projects:**
   - CLI: `python agentic/simple_agentic_graph.py`  
   - Web: `python agentic/webapp/app_agentic.py`

3. **Old system archived:**
   - `orchestrator/` folder documented as "first attempt"
   - Still there for reference and learning
   - README explains evolution

## 💡 Benefits of This Refactor

- **Cleaner codebase** - Easy to understand and modify
- **Separation of concerns** - Each component has clear role  
- **Better testability** - Can test individual components
- **Easier deployment** - Clear dependencies and structure
- **Future-proof** - Easy to add new features
- **Team-friendly** - New developers can understand quickly

---

**Ready to use!** 🎉

The new clean system maintains all the working functionality while being much more maintainable and understandable.
