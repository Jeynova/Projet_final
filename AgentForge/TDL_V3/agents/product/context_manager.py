"""
Context Manager for Progressive Code Generation

Handles context assembly, file summaries, and dependency management
for progressive file-by-file code generation.
"""

import re
from typing import Dict, List, Any, Optional, Tuple


class ContextManager:
    """Manages context building and file relationships for progressive generation"""
    
    def __init__(self):
        self.file_summaries = {}
        self.step_summaries = []
        self.max_context_size = 8000  # Characters limit for context
        
    def summarize_file(self, filename: str, content: str) -> Dict[str, Any]:
        """Create a concise summary of a generated file"""
        if not content or not isinstance(content, str):
            return {
                "filename": filename,
                "lines": 0,
                "summary": "Empty file",
                "exports": [],
                "imports": [],
                "main_components": []
            }
        
        lines = content.split('\n')
        line_count = len(lines)
        
        # Extract imports
        imports = []
        for line in lines[:20]:  # Check first 20 lines
            if line.strip().startswith(('import ', 'from ', 'const ', 'require(')):
                imports.append(line.strip()[:80])  # Truncate long imports
        
        # Extract exports and main components
        exports = []
        main_components = []
        
        # Look for class definitions
        class_matches = re.findall(r'class\s+(\w+)', content, re.IGNORECASE)
        main_components.extend([f"class {cls}" for cls in class_matches[:5]])
        
        # Look for function definitions
        func_matches = re.findall(r'(?:function\s+(\w+)|const\s+(\w+)\s*=|export\s+(?:const|function)\s+(\w+))', content)
        for match in func_matches[:5]:
            func_name = next(name for name in match if name)
            if func_name:
                main_components.append(f"function {func_name}")
        
        # Look for exports
        export_matches = re.findall(r'export\s+(?:default\s+)?(?:class\s+)?(?:function\s+)?(\w+)', content)
        exports.extend(export_matches[:5])
        
        # Create summary description
        if line_count < 10:
            summary = "Minimal implementation"
        elif line_count < 50:
            summary = "Basic implementation with core functionality"
        elif line_count < 150:
            summary = "Standard implementation with good structure"
        else:
            summary = "Comprehensive implementation with full features"
            
        return {
            "filename": filename,
            "lines": line_count,
            "summary": summary,
            "exports": exports[:3],  # Limit to avoid bloat
            "imports": imports[:3],
            "main_components": main_components[:3]
        }
    
    def get_file_dependencies(self, filename: str, file_tree: List[str]) -> List[str]:
        """Determine which files the current file likely depends on"""
        dependencies = []
        
        # Extract directory and base name
        file_dir = '/'.join(filename.split('/')[:-1]) if '/' in filename else ''
        file_base = filename.split('/')[-1].split('.')[0]
        
        # Logic for determining dependencies based on file type and location
        file_ext = filename.split('.')[-1].lower()
        
        if file_ext in ['ts', 'js']:
            # For TypeScript/JavaScript files
            if 'controller' in filename.lower():
                # Controllers depend on services and models
                dependencies.extend([f for f in file_tree if 'service' in f or 'model' in f])
            elif 'service' in filename.lower():
                # Services depend on models and utilities
                dependencies.extend([f for f in file_tree if 'model' in f or 'util' in f])
            elif 'component' in filename.lower():
                # Components depend on services and other components
                dependencies.extend([f for f in file_tree if 'service' in f or 'hook' in f])
        
        elif file_ext in ['tsx', 'jsx']:
            # For React files
            dependencies.extend([f for f in file_tree if 'service' in f or 'hook' in f or 'component' in f])
        
        # Add files from same directory
        same_dir_files = [f for f in file_tree if f.startswith(file_dir) and f != filename]
        dependencies.extend(same_dir_files[:3])  # Limit to avoid bloat
        
        return list(set(dependencies))[:5]  # Remove duplicates and limit
    
    def build_context_for_file(self, target_file: str, original_prompt: str, 
                             file_tree: List[str], generated_files: Dict[str, str],
                             tech_stack: Dict[str, Any], architecture: Dict[str, Any],
                             step_name: str) -> Dict[str, Any]:
        """
        Build comprehensive context for generating a specific file
        """
        context = {
            "target_file": target_file,
            "original_prompt": original_prompt,
            "file_tree": file_tree,
            "tech_stack": tech_stack,
            "architecture": architecture,
            "step_name": step_name,
            "file_summaries": {},
            "related_files": {},
            "step_context": "",
            "dependencies": []
        }
        
        # Get dependencies for this file
        dependencies = self.get_file_dependencies(target_file, file_tree)
        context["dependencies"] = dependencies
        
        # Add summaries of all generated files (lightweight)
        for filename, content in generated_files.items():
            if isinstance(content, str):  # Safety check
                summary = self.summarize_file(filename, content)
                context["file_summaries"][filename] = summary
        
        # Add full code of most relevant files (if space allows)
        relevant_files = {}
        used_chars = len(str(context))
        
        # Prioritize dependencies first
        for dep_file in dependencies:
            if dep_file in generated_files and used_chars < self.max_context_size:
                dep_content = generated_files[dep_file]
                if isinstance(dep_content, str) and len(dep_content) < 2000:  # Only include reasonable-sized files
                    relevant_files[dep_file] = dep_content
                    used_chars += len(dep_content)
        
        context["related_files"] = relevant_files
        
        # Add step context from previous steps
        if self.step_summaries:
            latest_step = self.step_summaries[-1] if self.step_summaries else {}
            if isinstance(latest_step, dict):  # Safety check
                context["step_context"] = latest_step.get("summary", "")
        
        return context
    
    def format_context_for_llm(self, context: Dict[str, Any]) -> str:
        """Format context into a prompt-friendly string"""
        
        prompt_parts = []
        
        # Original requirements
        prompt_parts.append(f"PROJECT REQUIREMENTS:\n{context['original_prompt']}\n")
        
        # Current file and step
        prompt_parts.append(f"CURRENT TASK: Generate {context['target_file']} for {context['step_name']}\n")
        
        # Architecture context
        arch = context.get('architecture', {})
        if isinstance(arch, dict) and arch.get('rationale'):
            prompt_parts.append(f"ARCHITECTURE: {arch['rationale']}\n")
        
        # Technology stack
        tech = context.get('tech_stack', {})
        if isinstance(tech, dict):
            backend = tech.get('backend', {})
            frontend = tech.get('frontend', {})
            if isinstance(backend, dict):
                prompt_parts.append(f"BACKEND: {backend.get('name', 'Node.js')}\n")
            if isinstance(frontend, dict):
                prompt_parts.append(f"FRONTEND: {frontend.get('name', 'React')}\n")
        
        # File tree structure
        file_tree = context.get('file_tree', [])
        if file_tree:
            prompt_parts.append(f"PROJECT STRUCTURE:\n")
            for file in file_tree[:15]:  # Limit to avoid bloat
                prompt_parts.append(f"  - {file}\n")
            prompt_parts.append("\n")
        
        # Related files with full code
        related_files = context.get('related_files', {})
        if related_files:
            prompt_parts.append("RELATED FILES (for reference):\n")
            for filename, content in related_files.items():
                if isinstance(content, str):
                    preview = content[:300] + "..." if len(content) > 300 else content
                    prompt_parts.append(f"\n--- {filename} ---\n{preview}\n")
        
        # File summaries
        summaries = context.get('file_summaries', {})
        if summaries:
            prompt_parts.append("\nEXISTING FILES SUMMARY:\n")
            for filename, summary in list(summaries.items())[:10]:  # Limit
                if isinstance(summary, dict):
                    prompt_parts.append(f"  {filename}: {summary.get('summary', 'No summary')} ({summary.get('lines', 0)} lines)\n")
        
        # Step context
        step_context = context.get('step_context', '')
        if step_context:
            prompt_parts.append(f"\nPREVIOUS STEP CONTEXT:\n{step_context}\n")
        
        return "".join(prompt_parts)
    
    def add_step_summary(self, step_name: str, generated_files: Dict[str, str], 
                        validation_results: Dict[str, Any]) -> Dict[str, Any]:
        """Create and store a summary of a completed step"""
        
        step_summary = {
            "step_name": step_name,
            "files_count": len(generated_files),
            "total_lines": 0,
            "files_generated": [],
            "validation_score": validation_results.get('score', 0),
            "summary": "",
            "key_features": []
        }
        
        # Analyze generated files
        for filename, content in generated_files.items():
            if isinstance(content, str):
                lines = len(content.split('\n'))
                step_summary["total_lines"] += lines
                step_summary["files_generated"].append({
                    "name": filename,
                    "lines": lines
                })
        
        # Create summary text
        if step_summary["files_count"] > 0:
            avg_lines = step_summary["total_lines"] / step_summary["files_count"]
            step_summary["summary"] = f"{step_name} completed with {step_summary['files_count']} files, average {avg_lines:.0f} lines per file, validation score {step_summary['validation_score']}/10"
        else:
            step_summary["summary"] = f"{step_name} completed but no files generated"
        
        # Extract key features based on step type
        if "frontend" in step_name.lower():
            step_summary["key_features"] = ["React components", "User interface", "State management"]
        elif "backend" in step_name.lower():
            step_summary["key_features"] = ["API endpoints", "Business logic", "Data validation"]
        elif "database" in step_name.lower():
            step_summary["key_features"] = ["Database schema", "Models", "Relationships"]
        
        self.step_summaries.append(step_summary)
        return step_summary
    
    def get_context_size_estimate(self, context: Dict[str, Any]) -> int:
        """Estimate the size of context in characters"""
        return len(str(context))
