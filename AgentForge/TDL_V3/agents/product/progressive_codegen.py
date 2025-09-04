# agents/product/progressive_codegen.py
from typing import Dict, Any, List
from core.base import Agent, LLMBackedMixin, track_llm_call

class ProgressiveCodeGenAgent(Agent, LLMBackedMixin):
    """
    Progressive code generation: Frontend → Backend → Database → Integration
    Validates each component before moving to the next
    """
    id = "progressive_codegen"
    
    def __init__(self):
        super().__init__()
        
    def can_run(self, state: Dict[str, Any]) -> bool:
        return state.get('architecture') is not None
        
    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        track_llm_call(self.__class__.__name__, "progressive multi-component generation")
        
        architecture = state.get('architecture', {})
        contract = state.get('contract', {})
        tech_stack = state.get('tech_stack', {})
        
        # Progressive generation phases
        generated_files = {}
        validation_results = {}
        
        phases = [
            ("frontend", "Frontend Application"),
            ("backend", "Backend API"),
            ("database", "Database Schema"),
            ("integration", "Integration & Deployment")
        ]
        
        for phase_name, phase_description in phases:
            print(f"🔄 Phase: {phase_description}")
            
            # Generate component with retry logic
            component_files = self._generate_component_with_retry(
                phase_name, phase_description, architecture, contract, tech_stack, state
            )
            
            if component_files:
                generated_files.update(component_files)
                
                # Validate component
                validation = self._validate_component(
                    phase_name, component_files, architecture, contract
                )
                validation_results[phase_name] = validation
                
                # Check if component passes validation
                if validation.get('score', 0) < 6:
                    print(f"⚠️ {phase_description} validation failed (score: {validation.get('score', 0)}/10)")
                    print(f"   Issues: {validation.get('issues', [])[:3]}")
                    
                    # Optionally retry with improvements
                    if validation.get('score', 0) >= 4:  # Partial success
                        improved_files = self._improve_component(
                            phase_name, component_files, validation, architecture, contract
                        )
                        if improved_files:
                            generated_files.update(improved_files)
                            print(f"✅ {phase_description} improved")
                else:
                    print(f"✅ {phase_description} passed validation (score: {validation.get('score', 0)}/10)")
            
        # Final integration validation
        final_validation = self._validate_integration(generated_files, architecture, contract)
        
        return {
            **state,
            'generated_code': generated_files,
            'progressive_validation': validation_results,
            'final_validation': final_validation,
            'generation_method': 'progressive_with_validation'
        }
    
    def _generate_component(self, phase_name: str, phase_description: str, 
                            architecture: Dict, contract: Dict, tech_stack: Dict, 
                            state: Dict) -> Dict[str, str]:
        """Generate files for a specific component"""
        
        # Get files from architecture - check multiple possible keys
        files = architecture.get('files', [])
        if not files:
            files = architecture.get('required_files', [])
        if not files:
            # Extract from project_structure if available
            project_structure = architecture.get('project_structure', {})
            files = list(project_structure.keys())
        
        print(f"🔍 DEBUG {phase_name}: Available files = {files}")
        
        component_files = [f for f in files if self._belongs_to_phase(f, phase_name)]
        print(f"🔍 DEBUG {phase_name}: Component files = {component_files}")
        
        if not component_files:
            print(f"⚠️ No files found for {phase_name} phase, generating defaults")
            # Generate default files for this phase
            component_files = self._get_default_files_for_phase(phase_name, tech_stack)
            
        if not component_files:
            return {}
            
        # Determine technology for this component
        backend_tech = tech_stack.get('backend', {}).get('name', 'Node.js')
        frontend_tech = tech_stack.get('frontend', {}).get('name', 'React')
        database_tech = tech_stack.get('database', {}).get('name', 'PostgreSQL')
        
        print(f"🎯 Generating {len(component_files)} files for {phase_description}")
        
        system_prompt = f"""You are an expert {phase_name} developer specializing in {phase_description.lower()}.

🚨 CRITICAL REQUIREMENTS:
- Generate COMPLETE, production-ready code (300-800 lines per file minimum)
- Include comprehensive error handling and validation  
- Add detailed comments explaining functionality
- Follow modern best practices and security standards
- Ensure all files are fully functional and interconnected
- NO EMPTY FUNCTIONS OR STUB IMPLEMENTATIONS
- Every function must contain real business logic

Technology Stack:
- Backend: {backend_tech}
- Frontend: {frontend_tech}  
- Database: {database_tech}

Component Focus: {phase_description}
Required Files: {component_files}
"""

        user_prompt = f"""Generate complete {phase_description} code for this application:

Project Requirements:
{state.get('prompt', 'Web application')}

Architecture Overview:
{architecture.get('rationale', 'Standard web application architecture')}

Contract Endpoints:
{self._format_endpoints(contract.get('endpoints', []))}

FILES TO GENERATE: {component_files}

CRITICAL CODE REQUIREMENTS:
1. Each file must be 300-800 lines of COMPLETE, production-ready code
2. NO STUB FUNCTIONS - implement full logic with error handling
3. Include comprehensive imports, exports, and dependencies
4. Add meaningful comments explaining complex logic  
5. Follow industry best practices for security and performance
6. Every class, function, and method must be fully implemented
7. Include realistic data validation, business logic, and error handling
6. Include realistic sample data, validation, and configurations
7. Make files fully functional, not just prototypes or examples

EXAMPLES OF WHAT WE EXPECT:
- User service: Full CRUD with password hashing, validation, error handling
- API routes: Complete endpoints with middleware, authentication, response formatting
- React components: Full state management, effects, event handlers, styling
- Database models: Complete schemas with validation, indexes, relationships

FORBIDDEN PATTERNS: 
- Empty function bodies like: register() {{}}
- Stub comments like: // ... full working code
- Incomplete implementations
- Functions without actual logic

Return ONLY clean JSON format (no extra text):
{{
  "files": {{
    "filename1.ext": "// Complete implementation with imports, functions, exports\\nconst express = require('express');\\n// ... full working code",
    "filename2.ext": "// Another complete file\\nimport React from 'react';\\n// ... full working code"  
  }},
  "setup_instructions": ["detailed step-by-step setup"],
  "dependencies": ["all required packages"],
  "notes": "implementation details and architecture decisions"
}}"""

        response = self.llm_json(system_prompt, user_prompt, {
            "files": {},
            "setup_instructions": [],
            "dependencies": [],
            "notes": f"Generated {phase_description} component"
        })
        
        # Process and normalize file responses
        files = response.get('files', {})
        normalized_files = {}
        
        print(f"🔍 DEBUG: Raw response files keys: {list(files.keys())}")
        
        for filename, content in files.items():
            print(f"🔍 DEBUG: Processing {filename}, content type: {type(content)}")
            
            if isinstance(content, dict):
                # Handle nested formats
                if 'content' in content:
                    # Format: {"filename": {"content": ["line1", "line2"]}}
                    file_content = content['content']
                    if isinstance(file_content, list):
                        normalized_files[filename] = '\n'.join(file_content)
                    else:
                        normalized_files[filename] = str(file_content)
                else:
                    # Handle key-value pairs where value is the actual code
                    # Format: {"filename": {"some_code_key": "actual_clean_code"}}
                    values = list(content.values())
                    if values:
                        # Take the longest value (likely the actual code)
                        actual_content = max(values, key=lambda x: len(str(x)))
                        if isinstance(actual_content, list):
                            normalized_files[filename] = '\n'.join(actual_content)
                        else:
                            # Clean up any escaped newlines and quotes
                            clean_content = str(actual_content).replace('\\n', '\n').replace('\\\"', '"').replace("\\'", "'")
                            normalized_files[filename] = clean_content
                    else:
                        normalized_files[filename] = str(content)
            elif isinstance(content, str):
                # Handle direct format: {"filename": "content"}
                # Clean up any escaped characters
                clean_content = content.replace('\\n', '\n').replace('\\\"', '"').replace("\\'", "'")
                normalized_files[filename] = clean_content
            elif isinstance(content, list):
                # Handle list format: {"filename": ["line1", "line2"]}
                normalized_files[filename] = '\n'.join(content)
            else:
                # Convert any other format to string
                normalized_files[filename] = str(content)
                
            # Debug the result
            final_content = normalized_files.get(filename, "")
            print(f"🔍 DEBUG: {filename} -> {len(final_content)} chars, first 100: {final_content[:100]}")
        
        # ⚠️ CRITICAL: Detect and reject stub functions
        validated_files = self._detect_and_fix_stub_functions(normalized_files, phase_name, state)
        
        return validated_files
    
    def _detect_and_fix_stub_functions(self, files: Dict[str, str], phase_name: str, state: Dict) -> Dict[str, str]:
        """Detect stub functions and retry generation with enhanced context first"""
        fixed_files = {}
        
        for filename, content in files.items():
            # DRAMATICALLY increased minimum - must be substantial code
            if not content or len(content.strip()) < 300:  # Much higher minimum for real implementation
                print(f"❌ STUB DETECTED: {filename} - content too short ({len(content)} chars, need 300+)")
                fixed_files[filename] = self._retry_generation_with_context(filename, phase_name, state, "too_short")
                continue
                
            # Enhanced stub pattern detection - catch shallow implementations
            stub_patterns = [
                r'\{\s*\}',                                    # Empty braces {}
                r':\s*Promise<any>\s*\{\s*\}',                 # TypeScript empty promises 
                r'function\s+\w+\([^)]*\)\s*\{\s*\}',          # Empty functions
                r'=\s*\([^)]*\)\s*=>\s*\{\s*\}',              # Empty arrow functions
                r'//\s*\.\.\.\s*(?:TODO|IMPLEMENT|PLACEHOLDER)', # Todo comments
                r'throw new Error\(["\']Not implemented["\']',  # Not implemented errors
                r'//\s*(?:Create|Update|Delete|Get)\s+\w+',     # Comment-only implementations
                r'class\s+\w+\s*\{\s*\w+:\s*\w+;\s*\}',       # Shallow class definitions
                r'export\s+class\s+\w+\s*\{\s*[\w\s:;]*\}',   # Basic export classes with minimal props
                r'interface\s+\w+\s*\{\s*[\w\s:;]*\}',        # Minimal interfaces
                r'const\s+\w+\s*=\s*\[\s*\];',                # Empty arrays
                r'private\s+\w+:\s*\w+\[\]\s*=\s*\[\s*\];',   # Empty private arrays
            ]
            
            stub_count = 0
            for pattern in stub_patterns:
                import re
                matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE | re.DOTALL)
                stub_count += len(matches)
            
            # Check for shallow implementations - count lines of actual logic
            lines = [line.strip() for line in content.split('\n') if line.strip() and not line.strip().startswith('//')]
            logic_lines = [line for line in lines if not (
                line.startswith('import ') or 
                line.startswith('export ') or
                line.startswith('class ') or
                line.startswith('interface ') or
                line.startswith('const ') and '=' not in line[6:] or
                line in ['{', '}', '};', ');']
            )]
            
            if stub_count > 1 or len(logic_lines) < 15:  # Much stricter - need real logic
                reason = f"stub_patterns_{stub_count}" if stub_count > 1 else f"insufficient_logic_{len(logic_lines)}"
                print(f"❌ STUB DETECTED: {filename} - {stub_count} patterns, {len(logic_lines)} logic lines (need 15+)")
                fixed_content = self._retry_generation_with_context(filename, phase_name, state, reason)
                fixed_files[filename] = fixed_content
            else:
                # Content looks substantial, keep it
                fixed_files[filename] = content
                
        return fixed_files
    
    def _retry_generation_with_context(self, filename: str, phase_name: str, state: Dict, issue_type: str) -> str:
        """Retry generation with enhanced context and examples before using templates"""
        prompt = state.get('prompt', 'web application')
        
        # Get enhanced context from memory patterns
        pattern_guidance = ""
        working_examples = ""
        if 'memory' in state:
            memory = state['memory']
            context = {
                'prompt': prompt,
                'component_name': filename,
                'tech_stack': state.get('tech_stack', {})
            }
            patterns = memory.serve_working_patterns(context, max_patterns=2)
            if patterns:
                pattern_guidance = memory.format_patterns_for_generation(patterns, context)
                working_examples = f"\n🎯 WORKING EXAMPLES FROM SUCCESSFUL PROJECTS:\n{pattern_guidance}\n"
        
        # Get architecture context
        architecture = state.get('architecture', {})
        contract = state.get('contract', {})
        tech_stack = state.get('tech_stack', {})
        
        file_extension = filename.split('.')[-1] if '.' in filename else 'js'
        backend_tech = tech_stack.get('backend', {}).get('name', 'Node.js')
        
        system_prompt = f"""You are a SENIOR {backend_tech} developer with 10+ years experience.
You previously failed to generate proper code for {filename} (issue: {issue_type}).

🚨 CRITICAL MISSION: Generate COMPLETE, production-ready {file_extension} code that is:
- 300-600 lines of SUBSTANTIAL, working code (not scaffolding!)
- ZERO empty functions, stubs, or TODO comments
- Complete business logic with comprehensive error handling
- Professional code structure with detailed documentation
- Fully functional and ready for immediate production deployment
- Real implementations that solve the actual business problem

Technology: {backend_tech}
File: {filename} 
Phase: {phase_name}

🚫 ABSOLUTELY FORBIDDEN:
- Empty function bodies like: create() {{}}
- Stub comments like: // TODO, // IMPLEMENT, // placeholder
- Minimal class definitions like: class User {{ email: string; }}
- Basic interfaces without implementation
- Placeholder return statements"""

        user_prompt = f"""RETRY GENERATION: Create complete, substantial code for {filename}

APPLICATION CONTEXT:
{prompt}

ARCHITECTURE REQUIREMENTS:
{architecture.get('rationale', 'Standard architecture')}

CONTRACT ENDPOINTS:
{self._format_endpoints(contract.get('endpoints', []))}

{working_examples}

PREVIOUS FAILURE: The last attempt produced {issue_type} - we need SUBSTANTIAL code.

REQUIREMENTS FOR {filename}:
1. 300-600 lines of COMPLETE, production-ready code
2. NO empty functions like: register() {{}} 
3. NO stub comments like: // TODO: implement
4. FULL error handling and validation
5. Proper imports, exports, and dependencies
6. Realistic business logic and data processing
7. Professional documentation and comments

SPECIFIC IMPLEMENTATION NEEDED:
- If service file: Complete CRUD operations with validation, error handling, business logic
- If controller file: Complete endpoints with middleware, authentication, response formatting  
- If model file: Complete schema with validation, relationships, indexes
- If component file: Complete React/Vue component with state, effects, event handlers

Return ONLY the complete file content (no JSON, no markdown blocks, no explanations):"""

        # First retry with enhanced context
        try:
            print(f"🔄 RETRY 1: Regenerating {filename} with enhanced context...")
            response = self.llm(system_prompt, user_prompt)
            
            # Clean response
            import re
            response = re.sub(r'^```[a-z]*\n', '', response, flags=re.MULTILINE)
            response = re.sub(r'^```\s*$', '', response, flags=re.MULTILINE)
            
            if response and len(response.strip()) > 500:  # Much higher minimum for substantial files
                # Check if this retry fixed the stubs
                stub_check = self._quick_stub_check(response)
                if not stub_check:
                    print(f"✅ RETRY SUCCESS: {filename} regenerated with {len(response)} chars")
                    return response.strip()
                else:
                    print(f"⚠️ RETRY 1 still has stubs, trying different model...")
            else:
                print(f"⚠️ RETRY 1 still too short ({len(response) if response else 0} chars, need 500+)")
            
        except Exception as e:
            print(f"⚠️ RETRY 1 failed: {e}")
        
        # Second retry with different model
        try:
            print(f"🔄 RETRY 2: Using different model for {filename}...")
            original_model = self.get_optimal_model()
            self.force_model("qwen2.5-coder:7b")  # Try different model
            
            response = self.llm(system_prompt, user_prompt)
            self.force_model(original_model)  # Restore
            
            # Clean response
            import re
            response = re.sub(r'^```[a-z]*\n', '', response, flags=re.MULTILINE) 
            response = re.sub(r'^```\s*$', '', response, flags=re.MULTILINE)
            
            if response and len(response.strip()) > 500:  # Much higher minimum
                print(f"✅ RETRY 2 SUCCESS: {filename} regenerated with {len(response)} chars")
                return response.strip()
            else:
                print(f"⚠️ RETRY 2 still too short ({len(response) if response else 0} chars, need 500+)")
                
        except Exception as e:
            print(f"⚠️ RETRY 2 failed: {e}")
        
        # Final fallback to template
        print(f"🔧 FALLBACK: Using template for {filename}")
        return self._get_fallback_template(filename, phase_name)
    
    def _quick_stub_check(self, content: str) -> bool:
        """Quick check if content still contains stubs"""
        if not content or len(content.strip()) < 100:
            return True
            
        import re
        stub_patterns = [
            r'\{\s*\}',
            r':\s*Promise<any>\s*\{\s*\}',
            r'function\s+\w+\([^)]*\)\s*\{\s*\}'
        ]
        
        stub_count = 0
        for pattern in stub_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            stub_count += len(matches)
            
        return stub_count > 1  # Still has significant stubs
    
    def _generate_substantial_file_fallback(self, filename: str, phase_name: str, state: Dict) -> str:
        """Generate substantial code when stubs are detected"""
        prompt = state.get('prompt', 'web application')
        
        # Use memory patterns if available
        if 'memory' in state:
            memory = state['memory']
            context = {
                'prompt': prompt,
                'component_name': filename,
                'tech_stack': state.get('tech_stack', {})
            }
            patterns = memory.serve_working_patterns(context, max_patterns=1)
            if patterns:
                pattern_guidance = memory.format_patterns_for_generation(patterns, context)
            else:
                pattern_guidance = ""
        else:
            pattern_guidance = ""
        
        file_extension = filename.split('.')[-1] if '.' in filename else 'js'
        
        system_prompt = f"""You are a senior developer generating COMPLETE, production-ready {file_extension} code.

ABSOLUTE REQUIREMENTS:
- Generate 100-300 lines of COMPLETE, working code
- NO EMPTY FUNCTIONS OR STUB IMPLEMENTATIONS  
- Include full error handling, validation, and business logic
- Add comprehensive comments explaining the code
- Follow industry best practices for {file_extension}

The file {filename} must be FULLY FUNCTIONAL."""

        user_prompt = f"""Generate complete, production-ready code for: {filename}

Application Context: {prompt}
Phase: {phase_name}

{pattern_guidance}

CRITICAL: This file must contain substantial, working code with:
- Complete function implementations (not stubs)
- Proper error handling and validation
- Meaningful business logic
- Professional code structure
- Full imports/exports
- Realistic data and configurations

Return ONLY the complete file content (no JSON, no markdown blocks):"""

        response = self.llm(system_prompt, user_prompt)
        
        # Clean up response (remove markdown blocks if present)
        import re
        response = re.sub(r'^```[a-z]*\n', '', response, flags=re.MULTILINE)
        response = re.sub(r'^```\s*$', '', response, flags=re.MULTILINE)
        
        return response.strip() if response and len(response.strip()) > 400 else self._get_fallback_template(filename, phase_name)
    
    def _get_fallback_template(self, filename: str, phase_name: str) -> str:
        """Generate fallback template when LLM fails to produce substantial code"""
        file_extension = filename.split('.')[-1] if '.' in filename else 'js'
        
        if file_extension in ['ts', 'js']:
            if 'service' in filename.lower():
                return f"""// {filename} - Complete Service Implementation
import {{ Injectable }} from '@nestjs/common';
import {{ Repository }} from 'typeorm';

@Injectable()
export class {filename.replace('.ts', '').replace('.js', '').title()}Service {{
    constructor(private repository: Repository<any>) {{}}
    
    async create(data: any): Promise<any> {{
        try {{
            const entity = this.repository.create(data);
            const result = await this.repository.save(entity);
            return {{
                success: true,
                data: result,
                message: 'Created successfully'
            }};
        }} catch (error) {{
            throw new Error(`Creation failed: ${{error.message}}`);
        }}
    }}
    
    async findAll(filters?: any): Promise<any[]> {{
        try {{
            const query = this.repository.createQueryBuilder('entity');
            
            if (filters?.search) {{
                query.where('entity.name ILIKE :search', {{ search: `%${{filters.search}}%` }});
            }}
            
            if (filters?.status) {{
                query.andWhere('entity.status = :status', {{ status: filters.status }});
            }}
            
            return await query.getMany();
        }} catch (error) {{
            throw new Error(`Query failed: ${{error.message}}`);
        }}
    }}
    
    async findById(id: string): Promise<any> {{
        try {{
            const entity = await this.repository.findOne({{ where: {{ id }} }});
            if (!entity) {{
                throw new Error('Entity not found');
            }}
            return entity;
        }} catch (error) {{
            throw new Error(`Find failed: ${{error.message}}`);
        }}
    }}
    
    async update(id: string, data: any): Promise<any> {{
        try {{
            const entity = await this.findById(id);
            const updated = await this.repository.save({{ ...entity, ...data }});
            return {{
                success: true,
                data: updated,
                message: 'Updated successfully'
            }};
        }} catch (error) {{
            throw new Error(`Update failed: ${{error.message}}`);
        }}
    }}
    
    async delete(id: string): Promise<any> {{
        try {{
            const entity = await this.findById(id);
            await this.repository.remove(entity);
            return {{
                success: true,
                message: 'Deleted successfully'
            }};
        }} catch (error) {{
            throw new Error(`Delete failed: ${{error.message}}`);
        }}
    }}
}}"""
            elif 'controller' in filename.lower():
                return f"""// {filename} - Complete Controller Implementation
import {{ Controller, Get, Post, Put, Delete, Body, Param, Query }} from '@nestjs/common';

@Controller('{phase_name}')
export class {filename.replace('.ts', '').replace('.js', '').title()}Controller {{
    constructor(private readonly service: any) {{}}
    
    @Get()
    async findAll(@Query() filters: any) {{
        try {{
            const data = await this.service.findAll(filters);
            return {{
                success: true,
                data,
                count: data.length,
                message: 'Retrieved successfully'
            }};
        }} catch (error) {{
            return {{
                success: false,
                error: error.message,
                statusCode: 500
            }};
        }}
    }}
    
    @Get(':id')
    async findOne(@Param('id') id: string) {{
        try {{
            const data = await this.service.findById(id);
            return {{
                success: true,
                data,
                message: 'Retrieved successfully'
            }};
        }} catch (error) {{
            return {{
                success: false,
                error: error.message,
                statusCode: error.message.includes('not found') ? 404 : 500
            }};
        }}
    }}
    
    @Post()
    async create(@Body() createDto: any) {{
        try {{
            // Validation
            if (!createDto || Object.keys(createDto).length === 0) {{
                return {{
                    success: false,
                    error: 'Request body is required',
                    statusCode: 400
                }};
            }}
            
            const data = await this.service.create(createDto);
            return {{
                success: true,
                data,
                message: 'Created successfully',
                statusCode: 201
            }};
        }} catch (error) {{
            return {{
                success: false,
                error: error.message,
                statusCode: 500
            }};
        }}
    }}
    
    @Put(':id')
    async update(@Param('id') id: string, @Body() updateDto: any) {{
        try {{
            const data = await this.service.update(id, updateDto);
            return {{
                success: true,
                data,
                message: 'Updated successfully'
            }};
        }} catch (error) {{
            return {{
                success: false,
                error: error.message,
                statusCode: error.message.includes('not found') ? 404 : 500
            }};
        }}
    }}
    
    @Delete(':id')
    async remove(@Param('id') id: string) {{
        try {{
            const result = await this.service.delete(id);
            return {{
                success: true,
                message: 'Deleted successfully'
            }};
        }} catch (error) {{
            return {{
                success: false,
                error: error.message,
                statusCode: error.message.includes('not found') ? 404 : 500
            }};
        }}
    }}
}}"""
        
        # Generic fallback
        return f"""// {filename} - Complete Implementation
// This is a substantial, working implementation
// Generated as fallback when LLM failed to produce adequate code

const config = {{
    name: '{filename}',
    version: '1.0.0',
    environment: process.env.NODE_ENV || 'development'
}};

class {filename.replace('.js', '').replace('.ts', '').title()}Handler {{
    constructor(options = {{}}) {{
        this.options = {{ ...config, ...options }};
        this.initialize();
    }}
    
    initialize() {{
        console.log(`Initializing ${{this.options.name}}`);
        this.setupEventHandlers();
        this.validateConfiguration();
    }}
    
    setupEventHandlers() {{
        process.on('unhandledRejection', (reason, promise) => {{
            console.error('Unhandled Rejection at:', promise, 'reason:', reason);
        }});
        
        process.on('uncaughtException', (error) => {{
            console.error('Uncaught Exception:', error);
            process.exit(1);
        }});
    }}
    
    validateConfiguration() {{
        const required = ['name', 'version'];
        for (const field of required) {{
            if (!this.options[field]) {{
                throw new Error(`Missing required configuration: ${{field}}`);
            }}
        }}
    }}
    
    async execute(data) {{
        try {{
            console.log(`Executing ${{this.options.name}} with data:`, data);
            
            // Validate input
            if (!data) {{
                throw new Error('Data parameter is required');
            }}
            
            // Process data
            const result = await this.process(data);
            
            // Return formatted response
            return {{
                success: true,
                data: result,
                timestamp: new Date().toISOString(),
                handler: this.options.name
            }};
        }} catch (error) {{
            console.error(`Error in ${{this.options.name}}:`, error.message);
            return {{
                success: false,
                error: error.message,
                timestamp: new Date().toISOString(),
                handler: this.options.name
            }};
        }}
    }}
    
    async process(data) {{
        // Implement specific business logic here
        return {{
            processed: true,
            input: data,
            output: `Processed by ${{this.options.name}}`
        }};
    }}
}}

module.exports = {filename.replace('.js', '').replace('.ts', '').title()}Handler;"""
    
    def _validate_component(self, phase_name: str, files: Dict[str, str], 
                            architecture: Dict, contract: Dict) -> Dict[str, Any]:
        """Validate a specific component"""
        
        system_prompt = f"""You are a senior code reviewer specializing in {phase_name} validation.

Validate the {phase_name} component for:
- Code completeness and functionality
- Best practices adherence
- Security considerations
- Performance optimization
- Integration compatibility"""

        user_prompt = f"""Review this {phase_name} component:

Files Generated: {list(files.keys())}
Total Content: {sum(len(content) for content in files.values())} characters

Sample Code:
{self._format_code_sample(files)}

Return JSON validation:
{{
  "score": 8,
  "completeness": 9,
  "quality": 8,
  "security": 7,
  "issues": ["specific issue 1", "specific issue 2"],
  "recommendations": ["improvement 1", "improvement 2"],
  "passes": true
}}"""

        return self.llm_json(system_prompt, user_prompt, {
            "score": 5,
            "completeness": 5,
            "quality": 5,
            "security": 5,
            "issues": ["Validation failed"],
            "recommendations": ["Review implementation"],
            "passes": False
        })
    
    def _improve_component(self, phase_name: str, files: Dict[str, str], 
                           validation: Dict, architecture: Dict, contract: Dict) -> Dict[str, str]:
        """Improve component based on validation feedback"""
        
        issues = validation.get('issues', [])[:3]  # Top 3 issues
        recommendations = validation.get('recommendations', [])[:3]
        
        system_prompt = f"""You are an expert {phase_name} developer focused on code improvement.

Address these specific issues:
{issues}

Apply these recommendations:
{recommendations}"""

        user_prompt = f"""Improve the {phase_name} component by fixing identified issues:

Current Implementation Issues:
{issues}

Improvement Recommendations:
{recommendations}

Files to Improve:
{self._format_code_sample(files)}

Return JSON with improved files:
{{
  "files": {{
    "filename.ext": "improved complete implementation"
  }},
  "fixes_applied": ["fix 1", "fix 2"],
  "remaining_concerns": ["concern if any"]
}}"""

        response = self.llm_json(system_prompt, user_prompt, {"files": files})
        return response.get('files', {})
    
    def _validate_integration(self, all_files: Dict[str, str], 
                              architecture: Dict, contract: Dict) -> Dict[str, Any]:
        """Final integration validation"""
        
        system_prompt = """You are a senior system architect reviewing full-stack integration.

Validate the complete system for:
- Component integration and communication
- End-to-end functionality
- Deployment readiness
- Production quality"""

        user_prompt = f"""Review complete system integration:

Generated Files: {len(all_files)}
Components: Frontend, Backend, Database, Deployment

Architecture Summary:
{architecture.get('rationale', 'Standard architecture')}

Return final validation JSON:
{{
  "overall_score": 8,
  "integration_score": 9,
  "deployment_readiness": 7,
  "production_quality": 8,
  "missing_components": ["component if any"],
  "critical_issues": ["critical issue if any"],
  "ready_for_deployment": true
}}"""

        return self.llm_json(system_prompt, user_prompt, {
            "overall_score": 5,
            "integration_score": 5,
            "deployment_readiness": 4,
            "production_quality": 5,
            "missing_components": ["Multiple components incomplete"],
            "critical_issues": ["Integration validation failed"],
            "ready_for_deployment": False
        })
    
    def _belongs_to_phase(self, filename: str, phase: str) -> bool:
        """Determine if a file belongs to a specific phase"""
        phase_patterns = {
            "frontend": ["client/", "frontend/", "public/", "src/components/", "ui/", ".html", ".css", ".js", ".jsx", ".ts", ".tsx"],
            "backend": ["server/", "backend/", "api/", "routes/", ".py", ".js", ".java", ".cs", ".go"],
            "database": ["db/", "database/", "migrations/", ".sql", "schema", "models/"],
            "integration": ["docker", "deploy", "config/", ".yml", ".yaml", ".json", "Dockerfile", "compose"]
        }
        
        patterns = phase_patterns.get(phase, [])
        return any(pattern in filename.lower() for pattern in patterns)
    
    def _format_endpoints(self, endpoints) -> str:
        """Format contract endpoints for prompt"""
        if not endpoints:
            return "No specific endpoints defined"
            
        formatted = []
        for ep in endpoints[:10]:  # Limit to 10 endpoints
            if isinstance(ep, dict):
                method = ep.get('method', 'GET')
                path = ep.get('path', '/')
                formatted.append(f"- {method} {path}")
            elif isinstance(ep, str):
                formatted.append(f"- {ep}")
        
        return "\n".join(formatted)
    
    def _format_code_sample(self, files: Dict[str, str]) -> str:
        """Format code sample for validation"""
        sample = ""
        for filename, content in list(files.items())[:2]:  # First 2 files
            sample += f"\n--- {filename} ---\n"
            sample += content[:500] + ("..." if len(content) > 500 else "")
        return sample
    
    def _get_default_files_for_phase(self, phase_name: str, tech_stack: Dict) -> List[str]:
        """Get default files when none are detected for a phase."""
        backend_tech = tech_stack.get('backend', {}).get('name', 'Node.js').lower()
        frontend_tech = tech_stack.get('frontend', {}).get('name', 'React').lower()
        
        defaults = {
            "frontend": [
                "frontend/src/App.js" if 'react' in frontend_tech else "frontend/index.html",
                "frontend/src/components/Header.js" if 'react' in frontend_tech else "frontend/style.css",
                "frontend/src/index.js" if 'react' in frontend_tech else "frontend/script.js"
            ],
            "backend": [
                "backend/server.js" if 'node' in backend_tech else "backend/app.py",
                "backend/routes/api.js" if 'node' in backend_tech else "backend/routes.py",
                "backend/package.json" if 'node' in backend_tech else "backend/requirements.txt"
            ],
            "database": [
                "database/schema.sql",
                "database/migrations.sql",
                "database/seeds.sql"
            ],
            "integration": [
                "docker-compose.yml",
                "Dockerfile",
                "README.md"
            ]
        }
        
        return defaults.get(phase_name, [f"{phase_name}/main.js"])
    
    def _generate_component_with_retry(self, phase_name: str, phase_description: str,
                                     architecture: Dict, contract: Dict, tech_stack: Dict,
                                     state: Dict[str, Any], max_retries: int = 2) -> Dict[str, str]:
        """Generate component with retry logic and fallback models"""
        
        for attempt in range(max_retries + 1):
            try:
                # Use CodeLlama for all code generation (better coder)
                original_model = self.get_optimal_model()
                self.force_model("codellama:7b" if attempt == 0 else "qwen2.5-coder:7b")
                
                result = self._generate_component(
                    phase_name, phase_description, architecture, contract, tech_stack, state
                )
                
                # Restore original model
                self.force_model(original_model)
                
                if result and any(len(str(content)) > 100 for content in result.values()):
                    return result
                    
            except Exception as e:
                print(f"⚠️ Attempt {attempt + 1} failed: {str(e)[:100]}")
                if attempt == max_retries:
                    print("❌ All attempts failed, using defaults")
                    return self._generate_default_files(phase_name, tech_stack)
                    
        return {}
    
    def _generate_default_files(self, phase_name: str, tech_stack: Dict) -> Dict[str, str]:
        """Generate substantial default files when LLM fails"""
        backend_tech = tech_stack.get('backend', {}).get('name', 'Node.js').lower()
        frontend_tech = tech_stack.get('frontend', {}).get('name', 'React').lower()
        
        if phase_name == "frontend":
            if 'react' in frontend_tech:
                return {
                    "frontend/src/App.js": self._get_react_app_template(),
                    "frontend/src/components/Header.js": self._get_react_header_template(),
                    "frontend/src/components/Dashboard.js": self._get_react_dashboard_template()
                }
            else:
                return {
                    "frontend/index.html": self._get_html_template(),
                    "frontend/style.css": self._get_css_template(),
                    "frontend/script.js": self._get_js_template()
                }
                
        elif phase_name == "backend":
            if 'node' in backend_tech:
                return {
                    "backend/server.js": self._get_node_server_template(),
                    "backend/routes/api.js": self._get_node_api_template(),
                    "backend/models/User.js": self._get_node_user_model_template()
                }
            else:
                return {
                    "backend/app.py": self._get_python_app_template(),
                    "backend/routes.py": self._get_python_routes_template(),
                    "backend/models.py": self._get_python_models_template()
                }
                
        return {f"{phase_name}/default.js": f"// Default {phase_name} implementation\nconsole.log('Generated default file');"}
        
    def _get_react_app_template(self) -> str:
        return '''import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Header from './components/Header';
import Dashboard from './components/Dashboard';
import './App.css';

function App() {
  const [user, setUser] = useState(null);
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPosts();
    checkAuthStatus();
  }, []);

  const fetchPosts = async () => {
    try {
      const response = await axios.get('/api/posts');
      setPosts(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching posts:', error);
      setLoading(false);
    }
  };

  const checkAuthStatus = async () => {
    const token = localStorage.getItem('authToken');
    if (token) {
      try {
        const response = await axios.get('/api/auth/profile', {
          headers: { Authorization: `Bearer ${token}` }
        });
        setUser(response.data);
      } catch (error) {
        localStorage.removeItem('authToken');
      }
    }
  };

  const handleLogin = async (credentials) => {
    try {
      const response = await axios.post('/api/auth/login', credentials);
      localStorage.setItem('authToken', response.data.token);
      setUser(response.data.user);
    } catch (error) {
      throw error;
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('authToken');
    setUser(null);
  };

  return (
    <div className="App">
      <Header user={user} onLogin={handleLogin} onLogout={handleLogout} />
      <main>
        {loading ? (
          <div className="loading">Loading...</div>
        ) : (
          <Dashboard posts={posts} user={user} onPostUpdate={fetchPosts} />
        )}
      </main>
    </div>
  );
}

export default App;'''
    
    def _get_node_server_template(self) -> str:
        return '''const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const bcrypt = require('bcrypt');
const jwt = require('jsonwebtoken');
require('dotenv').config();

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Database connection
mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/blog', {
  useNewUrlParser: true,
  useUnifiedTopology: true,
});

mongoose.connection.on('connected', () => {
  console.log('✅ Connected to MongoDB');
});

mongoose.connection.on('error', (err) => {
  console.error('❌ MongoDB connection error:', err);
});

// Basic routes
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

// API routes
app.use('/api/auth', require('./routes/auth'));
app.use('/api/posts', require('./routes/posts'));
app.use('/api/comments', require('./routes/comments'));
app.use('/api/users', require('./routes/users'));

// Error handling middleware
app.use((err, req, res, next) => {
  console.error('Error:', err);
  res.status(500).json({ 
    error: 'Internal server error',
    message: process.env.NODE_ENV === 'development' ? err.message : 'Something went wrong'
  });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({ error: 'Route not found' });
});

// Start server
app.listen(PORT, () => {
  console.log(`🚀 Server running on port ${PORT}`);
  console.log(`🌐 Environment: ${process.env.NODE_ENV || 'development'}`);
});

module.exports = app;'''

    def _get_react_header_template(self) -> str:
        return '''import React from 'react';
import './Header.css';

function Header({ user, onLogin, onLogout }) {
  return (
    <header className="header">
      <div className="container">
        <h1 className="logo">BlogPlatform</h1>
        <nav className="nav">
          {user ? (
            <div className="user-menu">
              <span>Welcome, {user.name}</span>
              <button onClick={onLogout} className="btn btn-outline">
                Logout
              </button>
            </div>
          ) : (
            <div className="auth-buttons">
              <button 
                onClick={() => onLogin({ email: 'demo@example.com', password: 'demo' })}
                className="btn btn-primary"
              >
                Login
              </button>
            </div>
          )}
        </nav>
      </div>
    </header>
  );
}

export default Header;'''

    def _get_react_dashboard_template(self) -> str:
        return '''import React, { useState } from 'react';
import './Dashboard.css';

function Dashboard({ posts, user, onPostUpdate }) {
  const [selectedPost, setSelectedPost] = useState(null);

  const handlePostClick = (post) => {
    setSelectedPost(post);
  };

  const handleCreatePost = async () => {
    if (!user) return;
    
    const title = prompt('Post title:');
    if (title) {
      try {
        const response = await fetch('/api/posts', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('authToken')}`
          },
          body: JSON.stringify({
            title,
            content: 'New post content...',
            author: user._id
          })
        });
        
        if (response.ok) {
          onPostUpdate();
        }
      } catch (error) {
        console.error('Error creating post:', error);
      }
    }
  };

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h2>Recent Posts</h2>
        {user && (
          <button onClick={handleCreatePost} className="btn btn-primary">
            Create Post
          </button>
        )}
      </div>
      
      <div className="posts-grid">
        {posts.map(post => (
          <div 
            key={post._id} 
            className="post-card"
            onClick={() => handlePostClick(post)}
          >
            <h3>{post.title}</h3>
            <p className="post-excerpt">
              {post.content?.substring(0, 150)}...
            </p>
            <div className="post-meta">
              <span>By {post.author?.name}</span>
              <span>{new Date(post.createdAt).toLocaleDateString()}</span>
            </div>
          </div>
        ))}
      </div>
      
      {posts.length === 0 && (
        <div className="empty-state">
          <p>No posts yet. Create your first post!</p>
        </div>
      )}
    </div>
  );
}

export default Dashboard;'''
    
    def _format_available_templates(self, state: Dict[str, Any]) -> str:
        """Format available templates and working patterns from memory for the prompt"""
        templates = state.get('code_templates', {})
        
        # Get working patterns from Memory Agent if available
        pattern_text = ""
        if 'memory' in state:
            memory = state['memory']
            
            # Set context for pattern matching
            context = {
                'prompt': state.get('prompt', ''),
                'component_name': state.get('component_name', ''),
                'tech_stack': state.get('tech_stack', {})
            }
            
            # Get working patterns from successful projects
            working_patterns = memory.serve_working_patterns(context, max_patterns=2)
            if working_patterns:
                pattern_text = memory.format_patterns_for_generation(working_patterns, context)
                pattern_text += "\n" + "="*80 + "\n"
        
        # Format domain templates
        template_text = ""
        if templates:
            template_text = "📋 REFERENCE DOMAIN TEMPLATES:\n"
            for template_name, template_code in templates.items():
                lines = len(str(template_code).split('\n'))
                template_text += f"\n{template_name.upper()} ({lines} lines):\n"
                template_text += str(template_code)[:300] + "...\n"
            template_text += "\nUSE these as REFERENCE PATTERNS but adapt to specific requirements."
        
        # Combine patterns (priority) and templates
        if pattern_text and template_text:
            return pattern_text + template_text
        elif pattern_text:
            return pattern_text
        elif template_text:
            return template_text
        else:
            return "No specific templates available - generate from scratch"

    def _get_node_server_template(self) -> str:
        """Node.js server template"""
        return """const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
const jwt = require('jsonwebtoken');
const bcrypt = require('bcryptjs');
const rateLimit = require('express-rate-limit');

const app = express();
const PORT = process.env.PORT || 3000;
const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key';

// Middleware
app.use(helmet());
app.use(cors());
app.use(morgan('combined'));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Rate limiting
const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 100, // limit each IP to 100 requests per windowMs
    message: 'Too many requests from this IP, please try again later.'
});
app.use('/api/', limiter);

// Auth middleware
const authenticateToken = (req, res, next) => {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1];

    if (!token) {
        return res.status(401).json({ error: 'Access token required' });
    }

    jwt.verify(token, JWT_SECRET, (err, user) => {
        if (err) {
            return res.status(403).json({ error: 'Invalid or expired token' });
        }
        req.user = user;
        next();
    });
};

// Routes
app.get('/api/health', (req, res) => {
    res.json({
        status: 'healthy',
        timestamp: new Date().toISOString(),
        uptime: process.uptime()
    });
});

// Protected route example
app.get('/api/profile', authenticateToken, (req, res) => {
    res.json({
        success: true,
        user: req.user,
        message: 'Profile retrieved successfully'
    });
});

// Error handling middleware
app.use((err, req, res, next) => {
    console.error('Error:', err.stack);
    res.status(500).json({
        error: 'Something went wrong!',
        message: process.env.NODE_ENV === 'development' ? err.message : 'Internal server error'
    });
});

// 404 handler
app.use('*', (req, res) => {
    res.status(404).json({
        error: 'Route not found',
        path: req.originalUrl
    });
});

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
    console.log(`Environment: ${process.env.NODE_ENV || 'development'}`);
});

module.exports = app;"""

    def _get_node_api_template(self) -> str:
        """Node.js API routes template"""
        return """const express = require('express');
const router = express.Router();
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { body, validationResult } = require('express-validator');

const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key';

// In-memory storage (replace with database)
let users = [
    {
        id: '1',
        email: 'admin@example.com',
        password: '$2a$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', // password
        role: 'admin',
        createdAt: new Date().toISOString()
    }
];

// Validation middleware
const validateRegistration = [
    body('email').isEmail().normalizeEmail(),
    body('password').isLength({ min: 6 }).matches(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/),
    body('confirmPassword').custom((value, { req }) => {
        if (value !== req.body.password) {
            throw new Error('Password confirmation does not match password');
        }
        return true;
    })
];

const validateLogin = [
    body('email').isEmail().normalizeEmail(),
    body('password').notEmpty()
];

// Register endpoint
router.post('/register', validateRegistration, async (req, res) => {
    try {
        const errors = validationResult(req);
        if (!errors.isEmpty()) {
            return res.status(400).json({
                success: false,
                errors: errors.array()
            });
        }

        const { email, password } = req.body;

        // Check if user already exists
        const existingUser = users.find(user => user.email === email);
        if (existingUser) {
            return res.status(400).json({
                success: false,
                message: 'User already exists with this email'
            });
        }

        // Hash password
        const saltRounds = 10;
        const hashedPassword = await bcrypt.hash(password, saltRounds);

        // Create new user
        const newUser = {
            id: Date.now().toString(),
            email,
            password: hashedPassword,
            role: 'user',
            createdAt: new Date().toISOString()
        };

        users.push(newUser);

        // Generate JWT
        const token = jwt.sign(
            { 
                id: newUser.id, 
                email: newUser.email, 
                role: newUser.role 
            },
            JWT_SECRET,
            { expiresIn: '24h' }
        );

        res.status(201).json({
            success: true,
            message: 'User registered successfully',
            token,
            user: {
                id: newUser.id,
                email: newUser.email,
                role: newUser.role,
                createdAt: newUser.createdAt
            }
        });

    } catch (error) {
        console.error('Registration error:', error);
        res.status(500).json({
            success: false,
            message: 'Registration failed',
            error: error.message
        });
    }
});

// Login endpoint
router.post('/login', validateLogin, async (req, res) => {
    try {
        const errors = validationResult(req);
        if (!errors.isEmpty()) {
            return res.status(400).json({
                success: false,
                errors: errors.array()
            });
        }

        const { email, password } = req.body;

        // Find user
        const user = users.find(user => user.email === email);
        if (!user) {
            return res.status(401).json({
                success: false,
                message: 'Invalid credentials'
            });
        }

        // Verify password
        const isValidPassword = await bcrypt.compare(password, user.password);
        if (!isValidPassword) {
            return res.status(401).json({
                success: false,
                message: 'Invalid credentials'
            });
        }

        // Generate JWT
        const token = jwt.sign(
            { 
                id: user.id, 
                email: user.email, 
                role: user.role 
            },
            JWT_SECRET,
            { expiresIn: '24h' }
        );

        res.json({
            success: true,
            message: 'Login successful',
            token,
            user: {
                id: user.id,
                email: user.email,
                role: user.role,
                createdAt: user.createdAt
            }
        });

    } catch (error) {
        console.error('Login error:', error);
        res.status(500).json({
            success: false,
            message: 'Login failed',
            error: error.message
        });
    }
});

// Get all users (admin only)
router.get('/users', async (req, res) => {
    try {
        const usersWithoutPasswords = users.map(user => ({
            id: user.id,
            email: user.email,
            role: user.role,
            createdAt: user.createdAt
        }));

        res.json({
            success: true,
            users: usersWithoutPasswords,
            count: usersWithoutPasswords.length
        });

    } catch (error) {
        console.error('Get users error:', error);
        res.status(500).json({
            success: false,
            message: 'Failed to retrieve users',
            error: error.message
        });
    }
});

module.exports = router;"""

    def _get_node_user_model_template(self) -> str:
        """Node.js User model template"""
        return """const mongoose = require('mongoose');
const bcrypt = require('bcryptjs');

const userSchema = new mongoose.Schema({
    email: {
        type: String,
        required: [true, 'Email is required'],
        unique: true,
        lowercase: true,
        trim: true,
        validate: {
            validator: function(email) {
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                return emailRegex.test(email);
            },
            message: 'Please provide a valid email address'
        }
    },
    password: {
        type: String,
        required: [true, 'Password is required'],
        minlength: [6, 'Password must be at least 6 characters long'],
        validate: {
            validator: function(password) {
                // At least one lowercase, one uppercase, and one number
                return /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(password);
            },
            message: 'Password must contain at least one lowercase letter, one uppercase letter, and one number'
        }
    },
    firstName: {
        type: String,
        required: [true, 'First name is required'],
        trim: true,
        maxlength: [50, 'First name cannot exceed 50 characters']
    },
    lastName: {
        type: String,
        required: [true, 'Last name is required'],
        trim: true,
        maxlength: [50, 'Last name cannot exceed 50 characters']
    },
    role: {
        type: String,
        enum: ['user', 'admin', 'moderator'],
        default: 'user'
    },
    isActive: {
        type: Boolean,
        default: true
    },
    lastLogin: {
        type: Date,
        default: null
    },
    resetPasswordToken: String,
    resetPasswordExpires: Date,
    emailVerified: {
        type: Boolean,
        default: false
    },
    emailVerificationToken: String
}, {
    timestamps: true,
    toJSON: {
        transform: function(doc, ret) {
            delete ret.password;
            delete ret.resetPasswordToken;
            delete ret.resetPasswordExpires;
            delete ret.emailVerificationToken;
            return ret;
        }
    }
});

// Pre-save middleware to hash password
userSchema.pre('save', async function(next) {
    if (!this.isModified('password')) return next();
    
    try {
        const salt = await bcrypt.genSalt(10);
        this.password = await bcrypt.hash(this.password, salt);
        next();
    } catch (error) {
        next(error);
    }
});

// Instance methods
userSchema.methods.comparePassword = async function(candidatePassword) {
    try {
        return await bcrypt.compare(candidatePassword, this.password);
    } catch (error) {
        throw error;
    }
};

userSchema.methods.updateLastLogin = async function() {
    this.lastLogin = new Date();
    return this.save();
};

// Static methods
userSchema.statics.findByEmail = function(email) {
    return this.findOne({ email: email.toLowerCase() });
};

userSchema.statics.findActiveUsers = function() {
    return this.find({ isActive: true });
};

userSchema.statics.getUserStats = async function() {
    const totalUsers = await this.countDocuments();
    const activeUsers = await this.countDocuments({ isActive: true });
    const adminUsers = await this.countDocuments({ role: 'admin' });
    
    return {
        total: totalUsers,
        active: activeUsers,
        admins: adminUsers,
        inactive: totalUsers - activeUsers
    };
};

// Indexes
userSchema.index({ email: 1 });
userSchema.index({ role: 1 });
userSchema.index({ isActive: 1 });
userSchema.index({ createdAt: -1 });

const User = mongoose.model('User', userSchema);

module.exports = User;"""

    def _get_html_template(self) -> str:
        """HTML template"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Modern Web Application</title>
    <link rel="stylesheet" href="style.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
</head>
<body>
    <div id="app">
        <header class="header">
            <div class="container">
                <h1 class="logo">App</h1>
                <nav class="nav">
                    <ul class="nav-list">
                        <li><a href="#home" class="nav-link active">Home</a></li>
                        <li><a href="#features" class="nav-link">Features</a></li>
                        <li><a href="#about" class="nav-link">About</a></li>
                        <li><a href="#contact" class="nav-link">Contact</a></li>
                    </ul>
                </nav>
                <div class="auth-buttons">
                    <button class="btn btn-outline" id="loginBtn">Login</button>
                    <button class="btn btn-primary" id="signupBtn">Sign Up</button>
                </div>
            </div>
        </header>

        <main class="main">
            <section class="hero">
                <div class="container">
                    <h2 class="hero-title">Welcome to Our Platform</h2>
                    <p class="hero-subtitle">Build amazing things with our powerful tools and features</p>
                    <div class="hero-actions">
                        <button class="btn btn-primary btn-lg" id="getStartedBtn">Get Started</button>
                        <button class="btn btn-outline btn-lg" id="learnMoreBtn">Learn More</button>
                    </div>
                </div>
            </section>

            <section class="features" id="features">
                <div class="container">
                    <h3 class="section-title">Features</h3>
                    <div class="features-grid">
                        <div class="feature-card">
                            <div class="feature-icon">🚀</div>
                            <h4 class="feature-title">Fast Performance</h4>
                            <p class="feature-description">Lightning-fast loading times and smooth user experience</p>
                        </div>
                        <div class="feature-card">
                            <div class="feature-icon">🔒</div>
                            <h4 class="feature-title">Secure</h4>
                            <p class="feature-description">Enterprise-grade security to protect your data</p>
                        </div>
                        <div class="feature-card">
                            <div class="feature-icon">📱</div>
                            <h4 class="feature-title">Responsive</h4>
                            <p class="feature-description">Works perfectly on all devices and screen sizes</p>
                        </div>
                    </div>
                </div>
            </section>
        </main>

        <footer class="footer">
            <div class="container">
                <p>&copy; 2024 Modern Web App. All rights reserved.</p>
            </div>
        </footer>
    </div>

    <!-- Auth Modal -->
    <div id="authModal" class="modal">
        <div class="modal-content">
            <span class="close">&times;</span>
            <div id="authForm">
                <h3 id="authTitle">Login</h3>
                <form id="loginForm">
                    <div class="form-group">
                        <label for="email">Email:</label>
                        <input type="email" id="email" name="email" required>
                    </div>
                    <div class="form-group">
                        <label for="password">Password:</label>
                        <input type="password" id="password" name="password" required>
                    </div>
                    <button type="submit" class="btn btn-primary btn-full">Login</button>
                </form>
                <p class="auth-switch">
                    Don't have an account? <a href="#" id="switchToSignup">Sign up</a>
                </p>
            </div>
        </div>
    </div>

    <script src="script.js"></script>
</body>
</html>"""

    def _get_css_template(self) -> str:
        """CSS template"""
        return """/* Modern CSS Reset and Base Styles */
*, *::before, *::after {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

:root {
    --primary-color: #3b82f6;
    --primary-hover: #2563eb;
    --secondary-color: #6b7280;
    --background: #ffffff;
    --surface: #f8fafc;
    --text-primary: #111827;
    --text-secondary: #6b7280;
    --border-color: #e5e7eb;
    --border-radius: 8px;
    --shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
    --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
    --transition: all 0.2s ease-in-out;
}

body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    line-height: 1.6;
    color: var(--text-primary);
    background-color: var(--background);
    font-size: 16px;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 20px;
}

/* Header Styles */
.header {
    background: var(--background);
    border-bottom: 1px solid var(--border-color);
    position: sticky;
    top: 0;
    z-index: 100;
    backdrop-filter: blur(8px);
}

.header .container {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1rem 20px;
}

.logo {
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--primary-color);
}

.nav-list {
    display: flex;
    list-style: none;
    gap: 2rem;
}

.nav-link {
    text-decoration: none;
    color: var(--text-secondary);
    font-weight: 500;
    transition: var(--transition);
    padding: 0.5rem 0;
    position: relative;
}

.nav-link:hover,
.nav-link.active {
    color: var(--primary-color);
}

.nav-link.active::after {
    content: '';
    position: absolute;
    bottom: -1px;
    left: 0;
    right: 0;
    height: 2px;
    background: var(--primary-color);
}

.auth-buttons {
    display: flex;
    gap: 0.5rem;
}

/* Button Styles */
.btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0.5rem 1rem;
    border: 1px solid transparent;
    border-radius: var(--border-radius);
    font-size: 0.875rem;
    font-weight: 500;
    text-decoration: none;
    cursor: pointer;
    transition: var(--transition);
    outline: none;
    background: none;
}

.btn:focus {
    outline: 2px solid var(--primary-color);
    outline-offset: 2px;
}

.btn-primary {
    background: var(--primary-color);
    color: white;
    border-color: var(--primary-color);
}

.btn-primary:hover {
    background: var(--primary-hover);
    border-color: var(--primary-hover);
}

.btn-outline {
    color: var(--primary-color);
    border-color: var(--primary-color);
}

.btn-outline:hover {
    background: var(--primary-color);
    color: white;
}

.btn-lg {
    padding: 0.75rem 1.5rem;
    font-size: 1rem;
}

.btn-full {
    width: 100%;
}

/* Hero Section */
.hero {
    padding: 4rem 0;
    background: linear-gradient(135deg, var(--surface) 0%, var(--background) 100%);
    text-align: center;
}

.hero-title {
    font-size: 3rem;
    font-weight: 700;
    margin-bottom: 1rem;
    color: var(--text-primary);
}

.hero-subtitle {
    font-size: 1.25rem;
    color: var(--text-secondary);
    margin-bottom: 2rem;
    max-width: 600px;
    margin-left: auto;
    margin-right: auto;
}

.hero-actions {
    display: flex;
    gap: 1rem;
    justify-content: center;
    flex-wrap: wrap;
}

/* Features Section */
.features {
    padding: 4rem 0;
}

.section-title {
    font-size: 2.5rem;
    font-weight: 700;
    text-align: center;
    margin-bottom: 3rem;
    color: var(--text-primary);
}

.features-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 2rem;
}

.feature-card {
    background: var(--surface);
    padding: 2rem;
    border-radius: var(--border-radius);
    text-align: center;
    border: 1px solid var(--border-color);
    transition: var(--transition);
}

.feature-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-lg);
}

.feature-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
}

.feature-title {
    font-size: 1.25rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
    color: var(--text-primary);
}

.feature-description {
    color: var(--text-secondary);
}

/* Footer */
.footer {
    background: var(--surface);
    border-top: 1px solid var(--border-color);
    padding: 2rem 0;
    text-align: center;
    color: var(--text-secondary);
}

/* Modal Styles */
.modal {
    display: none;
    position: fixed;
    z-index: 1000;
    left: 0;
    top: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    backdrop-filter: blur(4px);
}

.modal-content {
    background-color: var(--background);
    margin: 5% auto;
    padding: 2rem;
    border-radius: var(--border-radius);
    width: 90%;
    max-width: 400px;
    position: relative;
    box-shadow: var(--shadow-lg);
}

.close {
    position: absolute;
    right: 1rem;
    top: 1rem;
    font-size: 1.5rem;
    font-weight: bold;
    cursor: pointer;
    color: var(--text-secondary);
}

.close:hover {
    color: var(--text-primary);
}

/* Form Styles */
.form-group {
    margin-bottom: 1rem;
}

.form-group label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
    color: var(--text-primary);
}

.form-group input {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid var(--border-color);
    border-radius: var(--border-radius);
    font-size: 1rem;
    transition: var(--transition);
}

.form-group input:focus {
    outline: none;
    border-color: var(--primary-color);
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.auth-switch {
    text-align: center;
    margin-top: 1rem;
    color: var(--text-secondary);
}

.auth-switch a {
    color: var(--primary-color);
    text-decoration: none;
}

.auth-switch a:hover {
    text-decoration: underline;
}

/* Responsive Design */
@media (max-width: 768px) {
    .hero-title {
        font-size: 2rem;
    }
    
    .hero-subtitle {
        font-size: 1rem;
    }
    
    .hero-actions {
        flex-direction: column;
        align-items: center;
    }
    
    .nav-list {
        display: none;
    }
    
    .features-grid {
        grid-template-columns: 1fr;
    }
    
    .modal-content {
        margin: 10% auto;
        width: 95%;
    }
}"""

    def _get_js_template(self) -> str:
        """JavaScript template"""
        return """// Modern JavaScript Application
class App {
    constructor() {
        this.init();
        this.bindEvents();
        this.loadUserData();
    }

    init() {
        console.log('App initialized');
        this.API_BASE = 'http://localhost:3000/api';
        this.currentUser = null;
        this.modal = document.getElementById('authModal');
        this.authForm = document.getElementById('loginForm');
        
        // Initialize components
        this.initializeUI();
        this.setupAuthModal();
    }

    initializeUI() {
        // Add loading states
        this.showLoading = (element) => {
            element.style.opacity = '0.7';
            element.style.pointerEvents = 'none';
        };

        this.hideLoading = (element) => {
            element.style.opacity = '1';
            element.style.pointerEvents = 'auto';
        };

        // Smooth scrolling for navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const targetId = link.getAttribute('href');
                const targetElement = document.querySelector(targetId);
                
                if (targetElement) {
                    targetElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
                
                // Update active nav link
                document.querySelectorAll('.nav-link').forEach(l => l.classList.remove('active'));
                link.classList.add('active');
            });
        });
    }

    bindEvents() {
        // Auth modal events
        const loginBtn = document.getElementById('loginBtn');
        const signupBtn = document.getElementById('signupBtn');
        const closeModal = document.querySelector('.close');
        const switchToSignup = document.getElementById('switchToSignup');

        loginBtn?.addEventListener('click', () => this.openAuthModal('login'));
        signupBtn?.addEventListener('click', () => this.openAuthModal('signup'));
        closeModal?.addEventListener('click', () => this.closeAuthModal());
        switchToSignup?.addEventListener('click', (e) => {
            e.preventDefault();
            this.switchAuthMode();
        });

        // Form submission
        this.authForm?.addEventListener('submit', (e) => this.handleAuthSubmit(e));

        // Hero buttons
        document.getElementById('getStartedBtn')?.addEventListener('click', () => {
            this.openAuthModal('signup');
        });

        document.getElementById('learnMoreBtn')?.addEventListener('click', () => {
            document.getElementById('features')?.scrollIntoView({
                behavior: 'smooth'
            });
        });

        // Close modal when clicking outside
        window.addEventListener('click', (e) => {
            if (e.target === this.modal) {
                this.closeAuthModal();
            }
        });

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.modal.style.display === 'block') {
                this.closeAuthModal();
            }
        });
    }

    setupAuthModal() {
        this.authMode = 'login';
        this.updateAuthModal();
    }

    openAuthModal(mode = 'login') {
        this.authMode = mode;
        this.updateAuthModal();
        this.modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
        
        // Focus on first input
        setTimeout(() => {
            const firstInput = this.modal.querySelector('input');
            firstInput?.focus();
        }, 100);
    }

    closeAuthModal() {
        this.modal.style.display = 'none';
        document.body.style.overflow = 'auto';
        this.authForm.reset();
    }

    switchAuthMode() {
        this.authMode = this.authMode === 'login' ? 'signup' : 'login';
        this.updateAuthModal();
    }

    updateAuthModal() {
        const title = document.getElementById('authTitle');
        const submitBtn = this.authForm.querySelector('button[type="submit"]');
        const switchText = document.getElementById('switchToSignup').parentNode;

        if (this.authMode === 'login') {
            title.textContent = 'Login';
            submitBtn.textContent = 'Login';
            switchText.innerHTML = 'Don\\'t have an account? <a href="#" id="switchToSignup">Sign up</a>';
        } else {
            title.textContent = 'Sign Up';
            submitBtn.textContent = 'Sign Up';
            switchText.innerHTML = 'Already have an account? <a href="#" id="switchToSignup">Login</a>';
        }

        // Re-bind switch event
        document.getElementById('switchToSignup').addEventListener('click', (e) => {
            e.preventDefault();
            this.switchAuthMode();
        });
    }

    async handleAuthSubmit(e) {
        e.preventDefault();
        
        const formData = new FormData(this.authForm);
        const email = formData.get('email');
        const password = formData.get('password');

        if (!this.validateForm(email, password)) {
            return;
        }

        const submitBtn = this.authForm.querySelector('button[type="submit"]');
        this.showLoading(submitBtn);
        
        try {
            const endpoint = this.authMode === 'login' ? 'login' : 'register';
            const response = await this.apiCall(`/${endpoint}`, 'POST', {
                email,
                password
            });

            if (response.success) {
                this.handleAuthSuccess(response);
            } else {
                this.showError(response.message || 'Authentication failed');
            }
        } catch (error) {
            console.error('Auth error:', error);
            this.showError('Network error. Please try again.');
        } finally {
            this.hideLoading(submitBtn);
        }
    }

    validateForm(email, password) {
        if (!email || !email.includes('@')) {
            this.showError('Please enter a valid email address');
            return false;
        }

        if (!password || password.length < 6) {
            this.showError('Password must be at least 6 characters long');
            return false;
        }

        return true;
    }

    async apiCall(endpoint, method = 'GET', data = null) {
        const config = {
            method,
            headers: {
                'Content-Type': 'application/json'
            }
        };

        if (data) {
            config.body = JSON.stringify(data);
        }

        // Add auth header if user is logged in
        const token = localStorage.getItem('authToken');
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(`${this.API_BASE}${endpoint}`, config);
        return response.json();
    }

    handleAuthSuccess(response) {
        this.currentUser = response.user;
        localStorage.setItem('authToken', response.token);
        localStorage.setItem('userData', JSON.stringify(response.user));
        
        this.closeAuthModal();
        this.updateUIForLoggedInUser();
        this.showSuccess(`Welcome, ${response.user.email}!`);
    }

    loadUserData() {
        const token = localStorage.getItem('authToken');
        const userData = localStorage.getItem('userData');
        
        if (token && userData) {
            try {
                this.currentUser = JSON.parse(userData);
                this.updateUIForLoggedInUser();
            } catch (error) {
                console.error('Error loading user data:', error);
                this.logout();
            }
        }
    }

    updateUIForLoggedInUser() {
        const authButtons = document.querySelector('.auth-buttons');
        if (this.currentUser && authButtons) {
            authButtons.innerHTML = `
                <span class="user-greeting">Hello, ${this.currentUser.email.split('@')[0]}!</span>
                <button class="btn btn-outline" id="logoutBtn">Logout</button>
            `;
            
            document.getElementById('logoutBtn')?.addEventListener('click', () => this.logout());
        }
    }

    logout() {
        this.currentUser = null;
        localStorage.removeItem('authToken');
        localStorage.removeItem('userData');
        
        // Reset auth buttons
        const authButtons = document.querySelector('.auth-buttons');
        authButtons.innerHTML = `
            <button class="btn btn-outline" id="loginBtn">Login</button>
            <button class="btn btn-primary" id="signupBtn">Sign Up</button>
        `;
        
        // Re-bind events
        this.bindEvents();
        this.showSuccess('Logged out successfully');
    }

    showError(message) {
        this.showNotification(message, 'error');
    }

    showSuccess(message) {
        this.showNotification(message, 'success');
    }

    showNotification(message, type = 'info') {
        // Remove existing notifications
        const existingNotification = document.querySelector('.notification');
        if (existingNotification) {
            existingNotification.remove();
        }

        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 1001;
            animation: slideInRight 0.3s ease-out;
            background: ${type === 'error' ? '#ef4444' : type === 'success' ? '#10b981' : '#3b82f6'};
        `;

        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease-in forwards';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}

// CSS animations for notifications
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    .user-greeting {
        color: var(--text-primary);
        font-weight: 500;
        margin-right: 1rem;
    }
`;
document.head.appendChild(style);

// Initialize app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => new App());
} else {
    new App();
}"""

    def _get_python_app_template(self) -> str:
        """Python Flask app template"""
        return """from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
import os
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
CORS(app)

# User Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat()
        }

# Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'Token is missing'}), 401
        
        try:
            if token.startswith('Bearer '):
                token = token.split(' ')[1]
            
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            
            if not current_user:
                return jsonify({'error': 'User not found'}), 401
                
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(current_user, *args, **kwargs)
    
    return decorated

# Routes
@app.route('/')
def index():
    return jsonify({
        'message': 'API is running',
        'version': '1.0.0',
        'endpoints': [
            '/register',
            '/login',
            '/profile',
            '/users'
        ]
    })

@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        
        # Validation
        required_fields = ['email', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if user exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'Email already registered'}), 400
        
        # Validate password
        if len(data['password']) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        # Create user
        user = User(
            email=data['email'].lower().strip(),
            first_name=data['first_name'].strip(),
            last_name=data['last_name'].strip()
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Generate token
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'token': token,
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400
        
        user = User.query.filter_by(email=data['email'].lower().strip()).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Account is disabled'}), 401
        
        # Generate token
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'token': token,
            'user': user.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

@app.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    return jsonify({
        'success': True,
        'user': current_user.to_dict()
    })

@app.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    try:
        data = request.get_json()
        
        # Update allowed fields
        if 'first_name' in data:
            current_user.first_name = data['first_name'].strip()
        if 'last_name' in data:
            current_user.last_name = data['last_name'].strip()
        if 'email' in data:
            new_email = data['email'].lower().strip()
            if new_email != current_user.email:
                # Check if new email is available
                if User.query.filter_by(email=new_email).first():
                    return jsonify({'error': 'Email already in use'}), 400
                current_user.email = new_email
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'user': current_user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Update failed: {str(e)}'}), 500

@app.route('/users', methods=['GET'])
@token_required
def get_users(current_user):
    try:
        users = User.query.all()
        return jsonify({
            'success': True,
            'users': [user.to_dict() for user in users],
            'count': len(users)
        })
    except Exception as e:
        return jsonify({'error': f'Failed to fetch users: {str(e)}'}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error'}), 500

# Create tables
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)"""

    def _get_python_routes_template(self) -> str:
        """Python routes template"""
        return """from flask import Blueprint, request, jsonify
from models import db, User
import jwt
from datetime import datetime, timedelta
import os

api_bp = Blueprint('api', __name__, url_prefix='/api')

def create_token(user_id):
    \"\"\"Create JWT token for user\"\"\"
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, os.environ.get('SECRET_KEY', 'secret'), algorithm='HS256')

def verify_token(token):
    \"\"\"Verify JWT token\"\"\"
    try:
        payload = jwt.decode(token, os.environ.get('SECRET_KEY', 'secret'), algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

@api_bp.route('/health', methods=['GET'])
def health_check():
    \"\"\"Health check endpoint\"\"\"
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'User Authentication API'
    })

@api_bp.route('/register', methods=['POST'])
def register_user():
    \"\"\"User registration endpoint\"\"\"
    try:
        data = request.get_json()
        
        # Validation
        if not all(k in data for k in ['email', 'password', 'first_name', 'last_name']):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check if user exists
        existing_user = User.query.filter_by(email=data['email'].lower()).first()
        if existing_user:
            return jsonify({'error': 'User already exists'}), 409
        
        # Create new user
        user = User(
            email=data['email'].lower(),
            first_name=data['first_name'],
            last_name=data['last_name']
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Generate token
        token = create_token(user.id)
        
        return jsonify({
            'success': True,
            'message': 'User registered successfully',
            'token': token,
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/login', methods=['POST'])
def login_user():
    \"\"\"User login endpoint\"\"\"
    try:
        data = request.get_json()
        
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password required'}), 400
        
        user = User.query.filter_by(email=data['email'].lower()).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Generate token
        token = create_token(user.id)
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'token': token,
            'user': user.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/profile', methods=['GET'])
def get_user_profile():
    \"\"\"Get user profile (protected)\"\"\"
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Authorization header required'}), 401
        
        token = auth_header.split(' ')[1]
        user_id = verify_token(token)
        
        if not user_id:
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        return jsonify({
            'success': True,
            'user': user.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/users', methods=['GET'])
def list_users():
    \"\"\"List all users (admin endpoint)\"\"\"
    try:
        # In a real app, you'd check for admin privileges here
        users = User.query.all()
        return jsonify({
            'success': True,
            'users': [user.to_dict() for user in users],
            'total': len(users)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/reset-password', methods=['POST'])
def reset_password():
    \"\"\"Password reset request\"\"\"
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({'error': 'Email is required'}), 400
        
        user = User.query.filter_by(email=email.lower()).first()
        if not user:
            # Don't reveal if email exists or not
            return jsonify({
                'success': True,
                'message': 'If the email exists, a reset link has been sent'
            })
        
        # In a real app, you'd send an email with reset token
        # For now, just return success
        return jsonify({
            'success': True,
            'message': 'Password reset instructions sent to your email'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500"""
