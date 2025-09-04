#!/usr/bin/env python3
"""
🏗️ ARCHITECTURE AGENT
Intelligent architecture design
"""

from typing import Dict, Any

from core.base import LLMBackedMixin, track_llm_call


# ──────────────────────────────────────────────────────────────────────────────
# 🏗️ ARCHITECTURE AGENT
# ──────────────────────────────────────────────────────────────────────────────
class ArchitectureAgent(LLMBackedMixin):
    id = "architecture"
    def can_run(self, state: Dict[str, Any]) -> bool:
        # Don't run if quality goal has been reached
        if state.get('goal_reached', False):
            return False
            
        return 'architecture' not in state and 'tech_stack' in state
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        track_llm_call("🏗️ ArchitectureAgent", "intelligent architecture design")
        prompt = state.get('prompt',''); tech_stack = state.get('tech_stack',[]); complexity = state.get('complexity','moderate')
        
        # Detect project type for targeted architecture
        project_type = self.detect_project_type(prompt, tech_stack)
        
        # INTELLIGENT LLM PROMPT focused on CONTEXT-AWARE analysis
        system_prompt = f"""You are a SENIOR SOFTWARE ARCHITECT with 10+ years of experience designing production systems.

CRITICAL ANALYSIS PROCESS:
1. DEEPLY ANALYZE the project requirements and scope
2. DETERMINE the real complexity level based on features needed
3. DESIGN comprehensive architecture for PRODUCTION deployment
4. AVOID over-engineering simple projects AND avoid under-engineering complex ones
5. CONSIDER scalability, maintainability, security, and operational requirements

PROJECT COMPLEXITY ASSESSMENT:
- SIMPLE (5-12 files): Basic CRUD, single user type, minimal business logic
  Example: "weather API", "simple calculator", "basic blog"
  
- MODERATE (15-25 files): Multiple entities, authentication, user roles, business rules
  Example: "task management", "inventory system", "team collaboration tool"
  
- COMPLEX (25-50+ files): Multiple user types, payments, admin panels, integrations, microservices
  Example: "e-commerce platform", "social network", "enterprise SaaS", "marketplace"

PRODUCTION ARCHITECTURE REQUIREMENTS:
- Complete authentication and authorization systems
- Proper database design with relationships and constraints  
- Comprehensive API layer with validation and error handling
- Security middleware and best practices
- Monitoring, logging, and observability
- Docker containerization and deployment configs
- Testing infrastructure and CI/CD
- Documentation and developer experience

For COMPLEX projects, include:
- Admin panels and management interfaces
- Payment processing and billing systems
- Real-time features (WebSockets, notifications)
- File upload and media management
- Email systems and notifications
- Advanced security (2FA, audit logs)
- Performance optimization (caching, CDN)
- Multiple deployment environments

Return COMPREHENSIVE architecture analysis:
{{
  "project_structure": {{"folder/": "detailed_purpose_and_contents"}},
  "required_files": ["ALL files needed for production deployment"],
  "key_components": ["essential_production_components"],
  "data_flow": "detailed system data flow and interactions",
  "scalability_approach": "production scaling strategy",
  "security_architecture": "comprehensive security design",
  "deployment_strategy": "production deployment approach", 
  "complexity_justification": "WHY this architecture level is appropriate"
}}

THINK LIKE A SENIOR ARCHITECT: What would you actually build for this project in production?"""

        # Handle both old format (list) and new format (dict) for tech_stack
        print(f"🔍 DEBUG ArchitectureAgent: tech_stack type = {type(tech_stack)}")
        print(f"🔍 DEBUG ArchitectureAgent: tech_stack = {tech_stack}")
        
        if isinstance(tech_stack, dict):
            # New format from optimized team debate
            backend_info = tech_stack.get('backend', {})
            frontend_info = tech_stack.get('frontend', {})  
            database_info = tech_stack.get('database', {})
            
            backend = {'name': backend_info.get('name', 'Node.js'), 'reasoning': backend_info.get('reasoning', '')}
            frontend = {'name': frontend_info.get('name', 'React'), 'reasoning': frontend_info.get('reasoning', '')}
            database = {'name': database_info.get('name', 'MongoDB'), 'reasoning': database_info.get('reasoning', '')}
        elif isinstance(tech_stack, list):
            # Old format (list of dicts with role)
            backend = next((t for t in tech_stack if isinstance(t, dict) and t.get('role')=='backend'), {'name': 'Node.js', 'reasoning': ''})
            frontend = next((t for t in tech_stack if isinstance(t, dict) and t.get('role')=='frontend'), {'name': 'React', 'reasoning': ''})
            database = next((t for t in tech_stack if isinstance(t, dict) and t.get('role')=='database'), {'name': 'MongoDB', 'reasoning': ''})
        else:
            # Fallback for unexpected format
            print(f"⚠️ Unexpected tech_stack format: {type(tech_stack)}, using defaults")
            backend = {'name': 'Node.js', 'reasoning': 'Default backend choice'}
            frontend = {'name': 'React', 'reasoning': 'Default frontend choice'}
            database = {'name': 'MongoDB', 'reasoning': 'Default database choice'}
        
        user_prompt = f"""Project: {prompt}
Project Type: {project_type}
Complexity: {complexity}

Technology Stack:
- Backend: {backend.get('name', 'Node.js')} - {backend.get('reasoning', '')}
- Frontend: {frontend.get('name', 'React')} - {frontend.get('reasoning', '')} 
- Database: {database.get('name', 'MongoDB')} - {database.get('reasoning', '')}

Analyze this specific project and design the most appropriate architecture.
Consider:
- What are the core features needed?
- How complex is the data model?
- What user interactions are required?
- How much configuration/deployment complexity is justified?
- What testing strategy makes sense for this project?

Design EXACTLY what this project needs."""
        
        # Use comprehensive fallback as baseline
        fallback = self.get_architecture_template(project_type, tech_stack)
        
        result = self.llm_json(system_prompt, user_prompt, fallback, challenge_with_models=False)
        
        # CRITICAL FIX: Clean up required_files to remove descriptions mixed with file paths
        required_files = result.get('required_files', [])
        clean_files = []
        
        for item in required_files:
            # Keep only items that look like actual file paths
            if ('/' in item or '.' in item) and not item.startswith(' ') and len(item.split()) <= 3:
                # This looks like a file path: has / or ., not indented, not a long sentence
                clean_files.append(item)
            # Skip items that look like descriptions: sentences, no file extension, etc.
        
        result['required_files'] = clean_files
        print(f"🧹 CLEANED: {len(required_files)} raw items → {len(clean_files)} actual files")
        
        # Let ValidationAgent and team debate decide if architecture is appropriate
        # No arbitrary quality checks here - trust the agent network
        
        print("\n🏗️ INTELLIGENT ARCHITECTURE:")
        
        # Display file structure
        required_files = result.get('required_files', [])
        if required_files:
            print(f"   📄 Required Files ({len(required_files)}):")
            for file in required_files[:5]:
                print(f"      • {file}")
            if len(required_files) > 5:
                print(f"      ... and {len(required_files) - 5} more")
        
        # Display complexity justification if available
        complexity_justification = result.get('complexity_justification', '')
        if complexity_justification:
            print(f"   🎯 Architecture rationale: {complexity_justification[:100]}...")
        
        # Display folder structure  
        for k,v in list(result.get('project_structure',{}).items())[:3]:
            print(f"   📁 {k}: {v}")
        comps = result.get('key_components',[]); 
        if comps: print(f"   🔧 Components: {', '.join(comps[:3])}")
        return {'architecture': result}

    def detect_project_type(self, prompt, tech_stack):
        """Detect project type from prompt and tech stack"""
        prompt_lower = prompt.lower()
        
        if any(word in prompt_lower for word in ['blog', 'post', 'article', 'cms', 'content']):
            return 'blog'
        elif any(word in prompt_lower for word in ['ecommerce', 'shop', 'store', 'product', 'cart']):
            return 'ecommerce'  
        elif any(word in prompt_lower for word in ['task', 'todo', 'project management', 'kanban']):
            return 'task_management'
        elif any(word in prompt_lower for word in ['social', 'chat', 'message', 'feed']):
            return 'social'
        elif any(word in prompt_lower for word in ['portfolio', 'resume', 'personal']):
            return 'portfolio'
        elif any(word in prompt_lower for word in ['api', 'rest', 'service', 'microservice']):
            return 'api'
        elif any(word in prompt_lower for word in ['dashboard', 'analytics', 'admin']):
            return 'dashboard'
        else:
            return 'web_app'

    def get_architecture_template(self, project_type, tech_stack):
        """Get architecture template based on project type"""
        
        # Determine backend tech - handle both dict and list formats
        backend_tech = 'node'
        
        if isinstance(tech_stack, dict):
            # New dictionary format
            backend_info = tech_stack.get('backend', {})
            if isinstance(backend_info, dict):
                name = backend_info.get('name', '').lower()
            else:
                name = str(backend_info).lower()
        elif isinstance(tech_stack, list):
            # Old list format
            for tech in tech_stack:
                if isinstance(tech, dict) and tech.get('role') == 'backend':
                    name = tech.get('name', '').lower()
                    break
            else:
                name = 'node'
        else:
            name = 'node'
            
        # Determine backend technology
        if 'python' in name or 'django' in name or 'flask' in name:
            backend_tech = 'python'
        elif 'node' in name or 'express' in name or 'javascript' in name:
            backend_tech = 'node'
        
        if project_type == 'blog':
            if backend_tech == 'python':
                return {
                    "project_structure": {
                        "backend/": "Django/Flask backend application", 
                        "frontend/": "React frontend application",
                        "database/": "Database migrations and seeds",
                        "config/": "Configuration files",
                        "tests/": "Test suites",
                        "docs/": "Documentation"
                    },
                    "required_files": [
                        "backend/app.py", "backend/models.py", "backend/views.py", "backend/urls.py",
                        "backend/requirements.txt", "backend/settings.py", 
                        "frontend/src/App.js", "frontend/src/components/PostList.js", 
                        "frontend/src/components/PostForm.js", "frontend/src/pages/Home.js",
                        "frontend/package.json", "docker-compose.yml", ".env.example", "README.md"
                    ],
                    "key_components": ["User Authentication", "Post Management", "Comment System", "Admin Panel"],
                    "data_flow": "Frontend → API → Database → Response → UI Update",
                    "scalability_approach": "Horizontal scaling with load balancer",
                    "entry_points": ["backend/app.py", "frontend/src/App.js"]
                }
            else:  # Node.js
                return {
                    "project_structure": {
                        "backend/": "Express.js backend API",
                        "frontend/": "React frontend application", 
                        "config/": "Configuration files",
                        "models/": "Database models",
                        "routes/": "API route handlers",
                        "middleware/": "Custom middleware",
                        "tests/": "Test suites",
                        "public/": "Static assets"
                    },
                    "required_files": [
                        "backend/app.js", "backend/package.json", 
                        "backend/models/User.js", "backend/models/Post.js", "backend/models/Comment.js",
                        "backend/routes/auth.js", "backend/routes/posts.js", "backend/routes/users.js",
                        "backend/middleware/auth.js", "backend/config/database.js",
                        "frontend/src/App.js", "frontend/src/components/PostList.js",
                        "frontend/src/components/PostForm.js", "frontend/src/components/Auth.js", 
                        "frontend/package.json", "docker-compose.yml", ".env.example", "README.md"
                    ],
                    "key_components": ["User Authentication", "Post CRUD", "Comment System", "API Gateway"],
                    "data_flow": "React → Express API → MongoDB → JSON Response → UI Render",
                    "scalability_approach": "Microservices with Docker containers",
                    "file_dependencies": {
                        "backend/app.js": ["express", "mongoose", "cors", "helmet"],
                        "frontend/src/App.js": ["react", "axios", "react-router-dom"]
                    },
                    "entry_points": ["backend/app.js", "frontend/src/index.js"]
                }
        
        elif project_type == 'social':
            return {
                "project_structure": {
                    "backend/": "Express.js backend API",
                    "frontend/": "React frontend application", 
                    "config/": "Configuration files",
                    "models/": "Database models for users, posts, follows",
                    "routes/": "API route handlers",
                    "middleware/": "Auth and validation middleware",
                    "uploads/": "User uploaded content",
                    "tests/": "Test suites"
                },
                "required_files": [
                    "backend/app.js", "backend/package.json",
                    "backend/models/User.js", "backend/models/Post.js", "backend/models/Follow.js",
                    "backend/models/Like.js", "backend/models/Comment.js",
                    "backend/routes/auth.js", "backend/routes/posts.js", "backend/routes/users.js",
                    "backend/routes/social.js", "backend/middleware/auth.js", "backend/config/database.js",
                    "frontend/src/App.js", "frontend/src/components/Feed.js", "frontend/src/components/Profile.js",
                    "frontend/src/components/PostCard.js", "frontend/src/components/UserCard.js",
                    "frontend/package.json", "docker-compose.yml", ".env.example", "README.md"
                ],
                "key_components": ["User Profiles", "Social Feed", "Following System", "Post Management", "Real-time Updates"],
                "data_flow": "User Action → API → Database → WebSocket → Real-time UI Update"
            }
        
        elif project_type == 'ecommerce':
            return {
                "project_structure": {
                    "backend/": "Express.js backend API",
                    "frontend/": "React frontend application", 
                    "config/": "Configuration files",
                    "models/": "Database models for products, orders, users",
                    "routes/": "API route handlers",
                    "middleware/": "Auth and validation middleware",
                    "services/": "Business logic services",
                    "tests/": "Test suites"
                },
                "required_files": [
                    "backend/app.js", "backend/package.json",
                    "backend/models/User.js", "backend/models/Product.js", "backend/models/Order.js",
                    "backend/models/Cart.js", "backend/models/Category.js",
                    "backend/routes/auth.js", "backend/routes/products.js", "backend/routes/orders.js",
                    "backend/routes/cart.js", "backend/services/paymentService.js", "backend/config/database.js",
                    "frontend/src/App.js", "frontend/src/components/ProductList.js", "frontend/src/components/Cart.js",
                    "frontend/src/components/Checkout.js", "frontend/src/pages/ProductDetail.js",
                    "frontend/package.json", "docker-compose.yml", ".env.example", "README.md"
                ],
                "key_components": ["Product Catalog", "Shopping Cart", "Order Management", "Payment Processing", "User Accounts"],
                "data_flow": "Browse → Add to Cart → Checkout → Payment → Order Processing → Fulfillment"
            }
        
        elif project_type == 'task_management':
            return {
                "project_structure": {
                    "backend/": "Express.js backend API",
                    "frontend/": "React frontend application", 
                    "config/": "Configuration files",
                    "models/": "Database models for tasks, projects, users",
                    "routes/": "API route handlers",
                    "middleware/": "Auth and validation middleware",
                    "services/": "Business logic services",
                    "tests/": "Test suites"
                },
                "required_files": [
                    "backend/app.js", "backend/package.json",
                    "backend/models/User.js", "backend/models/Task.js", "backend/models/Project.js",
                    "backend/models/Team.js", "backend/models/Comment.js",
                    "backend/routes/auth.js", "backend/routes/tasks.js", "backend/routes/projects.js",
                    "backend/routes/teams.js", "backend/middleware/auth.js", "backend/config/database.js",
                    "frontend/src/App.js", "frontend/src/components/TaskBoard.js", "frontend/src/components/TaskCard.js",
                    "frontend/src/components/ProjectList.js", "frontend/src/pages/Dashboard.js",
                    "frontend/package.json", "docker-compose.yml", ".env.example", "README.md"
                ],
                "key_components": ["Task Management", "Project Organization", "Team Collaboration", "Progress Tracking", "Notifications"],
                "data_flow": "Create Task → Assign → Track Progress → Update Status → Notify Team"
            }
        
        # Default fallback - make it comprehensive too
        return {
            "project_structure": {
                "backend/": "Backend application code",
                "frontend/": "Frontend application code", 
                "config/": "Configuration files",
                "models/": "Database models",
                "routes/": "API route handlers",
                "tests/": "Test suites",
                "public/": "Static assets"
            },
            "required_files": [
                "backend/app.js", "backend/package.json",
                "backend/models/User.js", "backend/models/Product.js", "backend/models/Order.js",
                "backend/routes/auth.js", "backend/routes/api.js", "backend/routes/users.js",
                "backend/config/database.js", "backend/middleware/auth.js",
                "frontend/src/App.js", "frontend/src/components/Dashboard.js",
                "frontend/src/components/UserProfile.js", "frontend/src/pages/Home.js",
                "frontend/package.json", "docker-compose.yml", ".env.example", "README.md"
            ],
            "key_components": ["User Management", "API Gateway", "Database Layer", "Frontend UI"],
            "data_flow": "Client → API → Database → Response → UI Update",
            "scalability_approach": "Horizontal scaling with load balancer and microservices"
        }
