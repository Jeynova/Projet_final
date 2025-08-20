"""
Pipeline simple sans LangGraph pour test rapide
"""

from .agents_simple import spec_extractor, planner, scaffolder, codegen, eval_agent

def build_app():
    """Retourne une fonction qui simule le comportement de LangGraph"""
    
    def invoke(state):
        """Exécute le pipeline séquentiellement"""
        # Initialize logs
        if "logs" not in state:
            state["logs"] = []
            
        try:
            # Sequential execution
            state = spec_extractor(state)
            state = planner(state)
            state = scaffolder(state)
            state = codegen(state)
            state = eval_agent(state)
            
            # Set final status
            if "status" not in state:
                state["status"] = "completed"
                
            return state
            
        except Exception as e:
            state["status"] = "error"
            state["logs"].append(f"❌ Erreur: {str(e)}")
            return state
    
    # Return object with invoke method
    class SimpleGraph:
        def invoke(self, state):
            return invoke(state)
    
    return SimpleGraph()
