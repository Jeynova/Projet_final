# 🏗️ Architecture Technique - Full Agentic Pipeline

## 📁 Structure de Fichiers

```
orchestrator/
├── agents/                     # Agents existants (light mode)
│   ├── __init__.py
│   ├── spec_extractor.py
│   └── ...
├── agents_full/               # 🆕 Agents full agentic
│   ├── __init__.py
│   ├── spec_agent.py         # SpecAgent avancé
│   ├── tech_selector_agent.py # TechSelector avec smolagents
│   ├── architect_agent.py    # Architecture patterns
│   ├── codegen_agent.py      # Code generation avancée
│   ├── memory_agent.py       # Système de mémoire
│   ├── validation_agent.py   # QA intelligent
│   └── orchestrator_agent.py # Meta-orchestrateur
├── graph.py                   # Pipeline light (existant)
├── graph_full.py             # 🆕 Pipeline full agentic
├── mode_selector.py          # 🆕 Sélecteur de mode
└── utils/
    ├── memory_store.py       # 🆕 Stockage mémoire
    ├── agent_communication.py # 🆕 Inter-agent comm
    └── metrics.py            # 🆕 Métriques comparatives
```

## 🔄 Pipeline Comparatif

### Mode Light (Existant)
```python
def light_pipeline(prompt: str) -> BuildState:
    state = {"prompt": prompt}
    state = spec_extractor(state)      # Simple LLM extraction
    state = planner(state)             # Heuristiques
    state = scaffolder(state)          # Templates
    state = codegen(state)             # Basic generation
    return state
```

### Mode Full (Nouveau)
```python
def full_pipeline(prompt: str) -> BuildState:
    state = {"prompt": prompt}
    
    # Phase 1: Intelligence
    state = memory_agent.query_context(state)
    state = spec_agent.deep_analysis(state)
    state = tech_selector_agent.smart_selection(state)
    
    # Phase 2: Architecture
    state = architect_agent.design_system(state)
    
    # Phase 3: Implementation
    state = codegen_agent.generate_with_context(state)
    
    # Phase 4: Validation
    state = validation_agent.comprehensive_qa(state)
    
    # Phase 5: Learning
    memory_agent.store_learnings(state)
    
    return state
```

## 🎮 Interface de Sélection

### CLI Enhancement
```python
# orchestrator/mode_selector.py
class ModeSelector:
    def select_mode(self, prompt: str, user_prefs: Dict) -> str:
        complexity = self.analyze_complexity(prompt)
        user_mode = user_prefs.get('preferred_mode', 'auto')
        
        if user_mode == 'auto':
            return 'full' if complexity > 0.7 else 'light'
        return user_mode
    
    def run_comparison(self, prompt: str) -> Dict:
        """Run both pipelines and compare results"""
        light_result = self.run_light_pipeline(prompt)
        full_result = self.run_full_pipeline(prompt)
        
        return {
            'light': light_result,
            'full': full_result,
            'comparison': self.compare_results(light_result, full_result)
        }
```

### Web UI Integration
```python
# apps/ui_flask/routes/mode_selection.py
@app.route('/api/generate', methods=['POST'])
def generate_project():
    data = request.get_json()
    prompt = data['prompt']
    mode = data.get('mode', 'auto')  # light, full, auto, compare
    
    if mode == 'compare':
        result = mode_selector.run_comparison(prompt)
    else:
        pipeline = select_pipeline(mode, prompt)
        result = pipeline.run(prompt)
    
    return jsonify(result)
```

## 🧠 Agents Spécialisés - Implémentation

### 1. MemoryAgent
```python
# orchestrator/agents_full/memory_agent.py
class MemoryAgent:
    def __init__(self):
        self.db = sqlite3.connect('memory.db')
        self.setup_tables()
    
    def query_context(self, state: BuildState) -> BuildState:
        """Enrichit le contexte avec la mémoire"""
        prompt = state['prompt']
        
        # Recherche de projets similaires
        similar_projects = self.find_similar(prompt)
        user_preferences = self.get_user_preferences()
        
        state['memory_context'] = {
            'similar_projects': similar_projects,
            'user_preferences': user_preferences,
            'recommended_stack': self.predict_stack(prompt)
        }
        return state
    
    def store_learnings(self, state: BuildState):
        """Sauvegarde les apprentissages"""
        # Stocke les décisions techniques réussies
        # Analyse les patterns de l'utilisateur
        # Met à jour les recommandations
        pass
```

### 2. TechSelectorAgent (avec smolagents)
```python
# orchestrator/agents_full/tech_selector_agent.py
from smolagents import CodeAgent, tool

class TechSelectorAgent:
    def __init__(self):
        self.agent = CodeAgent(tools=[self.analyze_stack_tool])
    
    @tool
    def analyze_stack_tool(self, prompt: str, context: Dict) -> Dict:
        """Outil d'analyse de stack technique"""
        # Logique d'analyse sophistiquée
        return {"recommended_stack": "...", "justification": "..."}
    
    def smart_selection(self, state: BuildState) -> BuildState:
        """Sélection intelligente avec justifications"""
        agent_prompt = f"""
        Analyse ce projet: {state['prompt']}
        Contexte mémoire: {state.get('memory_context', {})}
        
        Recommande une stack technique optimale avec justifications.
        """
        
        result = self.agent.run(agent_prompt)
        state['tech_selection'] = result
        return state
```

### 3. ValidationAgent
```python
# orchestrator/agents_full/validation_agent.py
class ValidationAgent:
    def comprehensive_qa(self, state: BuildState) -> BuildState:
        """QA multi-niveaux intelligent"""
        project_path = state['project_dir']
        
        # 1. Tests statiques
        static_results = self.run_static_analysis(project_path)
        
        # 2. Tests de sécurité
        security_results = self.security_scan(project_path)
        
        # 3. Tests de performance
        perf_results = self.performance_analysis(project_path)
        
        # 4. Analyse LLM
        llm_analysis = self.llm_code_review(project_path)
        
        state['validation'] = {
            'static': static_results,
            'security': security_results,
            'performance': perf_results,
            'llm_review': llm_analysis,
            'overall_score': self.calculate_score(...)
        }
        
        return state
```

## 📊 Système de Métriques

### Métriques Comparatives
```python
# orchestrator/utils/metrics.py
class MetricsCollector:
    def compare_pipelines(self, light_result: Dict, full_result: Dict) -> Dict:
        return {
            'performance': {
                'light_time': light_result['execution_time'],
                'full_time': full_result['execution_time'],
                'time_ratio': full_result['execution_time'] / light_result['execution_time']
            },
            'quality': {
                'light_score': self.calculate_quality_score(light_result),
                'full_score': self.calculate_quality_score(full_result),
                'improvement': ...
            },
            'cost': {
                'light_tokens': light_result['llm_tokens'],
                'full_tokens': full_result['llm_tokens'],
                'cost_ratio': ...
            },
            'features': {
                'light_features': len(light_result.get('features', [])),
                'full_features': len(full_result.get('features', [])),
                'feature_depth': ...
            }
        }
```

## 🎯 Plan d'Implémentation Prioritaire

### Sprint 1 (Cette semaine)
1. ✅ README et documentation
2. 🔄 Structure de fichiers agents_full/
3. 🔄 mode_selector.py basique
4. 🔄 MemoryAgent v1 (SQLite simple)

### Sprint 2 (Semaine suivante)
1. TechSelectorAgent avec smolagents
2. ValidationAgent basique
3. Interface CLI --mode=full|light|compare
4. Premiers tests A/B

### Sprint 3 (Semaine 3)
1. ArchitectAgent patterns avancés
2. CodegenAgent contextuel
3. Dashboard web monitoring
4. Métriques détaillées

## 🧪 Tests et Validation

### Protocole de Test
```python
# tests/test_mode_comparison.py
def test_mode_comparison():
    test_prompts = [
        "Simple CRUD API",
        "E-commerce platform with microservices", 
        "Real-time chat application",
        "ML pipeline with data processing"
    ]
    
    for prompt in test_prompts:
        light_result = run_light_mode(prompt)
        full_result = run_full_mode(prompt)
        
        metrics = compare_results(light_result, full_result)
        
        assert metrics['quality']['full_score'] >= metrics['quality']['light_score']
        assert metrics['features']['full_features'] >= metrics['features']['light_features']
```

---

## 🚀 Commandes de Développement

```bash
# Créer la structure
mkdir -p orchestrator/agents_full orchestrator/utils

# Installer dépendances supplémentaires
pip install smolagents chromadb sqlite-utils scikit-learn

# Tests
python -m pytest tests/test_mode_comparison.py -v

# Run comparison
python -m orchestrator.mode_selector --prompt "E-commerce API" --compare
```

**🎯 Objectif : Pipeline agentique parallèle qui prouve sa supériorité qualitative tout en gardant la rapidité du mode light disponible.**
