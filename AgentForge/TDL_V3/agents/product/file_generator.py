"""
File Generator for Progressive Code Generation

Handles single-file generation with context and retry logic.
"""

import re
import json
from typing import Dict, List, Any, Optional
from core.base import LLMBackedMixin


class FileGenerator(LLMBackedMixin):
    """Generates individual files with comprehensive context and retry logic"""
    
    def __init__(self, context_manager, step_validator):
        super().__init__()
        self.context_manager = context_manager
        self.step_validator = step_validator
        self.generation_history = []
        
    def generate_file(self, filename: str, context: Dict[str, Any], 
                     requirements: Dict[str, Any], max_retries: int = 3) -> str:
        """
        Generate code for a single file with comprehensive context and validation
        """
        
        attempt = 0
        last_validation = None
        
        while attempt < max_retries:
            attempt += 1
            print(f"🔄 GENERATING {filename} (attempt {attempt}/{max_retries})")
            
            try:
                # Build the prompt with current context
                prompt = self._build_generation_prompt(filename, context, requirements, last_validation)
                
                # Select optimal model for this file type
                model = self._select_model_for_file(filename)
                if model:
                    self.force_model(model)
                
                # Generate the file content
                response = self.llm(
                    system_prompt=self._get_system_prompt(filename, context),
                    user_prompt=prompt
                )
                
                # Clean and validate response
                cleaned_content = self._clean_response(response)
                
                if not cleaned_content or len(cleaned_content.strip()) < 100:
                    print(f"⚠️ Attempt {attempt}: Response too short ({len(cleaned_content)} chars)")
                    continue
                
                # Quick validation check
                is_valid, validation_feedback = self.step_validator.validate_file(
                    filename, cleaned_content, requirements, context
                )
                
                if is_valid:
                    print(f"✅ SUCCESS: {filename} generated ({len(cleaned_content)} chars, score: {validation_feedback['score']}/10)")
                    self.generation_history.append({
                        'filename': filename,
                        'attempts': attempt,
                        'success': True,
                        'length': len(cleaned_content),
                        'score': validation_feedback['score']
                    })
                    return cleaned_content
                else:
                    print(f"⚠️ Attempt {attempt}: Validation failed (score: {validation_feedback['score']}/10)")
                    print(f"   Issues: {', '.join(validation_feedback.get('critical_errors', [])[:2])}")
                    last_validation = validation_feedback
                    
            except Exception as e:
                print(f"❌ Attempt {attempt} failed: {str(e)}")
                continue
        
        # All attempts failed, use fallback
        print(f"🔧 FALLBACK: Using template for {filename} after {max_retries} failures")
        fallback_content = self._get_fallback_template(filename, context)
        
        self.generation_history.append({
            'filename': filename,
            'attempts': max_retries,
            'success': False,
            'fallback_used': True,
            'length': len(fallback_content) if fallback_content else 0
        })
        
        return fallback_content or f"// Fallback content for {filename}\n// TODO: Implement"
    
    def _select_model_for_file(self, filename: str) -> Optional[str]:
        """Select the optimal model based on file type"""
        
        file_type = filename.split('.')[-1].lower()
        
        # Prioritize CodeLlama for code generation
        if file_type in ['ts', 'js', 'tsx', 'jsx', 'py', 'sql']:
            return "codellama:7b"
        elif file_type in ['css', 'scss', 'html']:
            return "qwen2.5-coder:7b"
        elif file_type in ['md', 'txt', 'json']:
            return "mistral:7b"
        else:
            return "codellama:7b"  # Default to code model
    
    def _get_system_prompt(self, filename: str, context: Dict[str, Any]) -> str:
        """Generate system prompt for file generation"""
        
        file_ext = filename.split('.')[-1].lower()
        tech_stack = context.get('tech_stack', {})
        
        # Determine primary technology
        if file_ext in ['ts', 'tsx']:
            tech = "TypeScript"
        elif file_ext in ['js', 'jsx']:
            tech = "JavaScript" 
        elif file_ext == 'py':
            tech = "Python"
        else:
            tech = file_ext.upper()
        
        backend_tech = "Node.js"
        frontend_tech = "React"
        
        if isinstance(tech_stack, dict):
            backend = tech_stack.get('backend', {})
            frontend = tech_stack.get('frontend', {})
            if isinstance(backend, dict):
                backend_tech = backend.get('name', 'Node.js')
            if isinstance(frontend, dict):
                frontend_tech = frontend.get('name', 'React')
        
        return f"""You are a SENIOR {tech} developer with 10+ years of experience in {backend_tech} and {frontend_tech}.

🎯 MISSION: Generate COMPLETE, production-ready code for {filename}

🚨 CRITICAL REQUIREMENTS:
- 300-800 lines of SUBSTANTIAL, working code (not scaffolding!)
- ZERO empty functions, stubs, or TODO comments
- Complete business logic with comprehensive error handling  
- Professional code structure with detailed documentation
- Fully functional and ready for immediate production deployment
- Real implementations that solve actual business problems

🚫 ABSOLUTELY FORBIDDEN:
- Empty function bodies like: create() {{}}
- Stub comments like: // TODO, // IMPLEMENT, // placeholder
- Minimal class definitions like: class User {{ email: string; }}
- Basic interfaces without implementation
- Placeholder return statements
- Generic error messages without specifics

✅ REQUIRED QUALITY STANDARDS:
- Comprehensive input validation and sanitization
- Proper error handling with specific error messages
- Security best practices (authentication, authorization, CORS, etc.)
- Performance optimizations where appropriate
- Clean, maintainable code architecture
- Meaningful variable and function names
- Detailed comments explaining complex logic"""
    
    def _build_generation_prompt(self, filename: str, context: Dict[str, Any], 
                                requirements: Dict[str, Any], 
                                validation_feedback: Optional[Dict[str, Any]] = None) -> str:
        """Build comprehensive generation prompt"""
        
        prompt_parts = []
        
        # Add retry context if this is a retry attempt
        if validation_feedback:
            retry_context = self.step_validator.get_retry_context(filename, validation_feedback)
            prompt_parts.append(f"🔄 RETRY GENERATION - PREVIOUS ATTEMPT FAILED:\n{retry_context}\n")
        
        # Add context formatted for LLM
        context_text = self.context_manager.format_context_for_llm(context)
        prompt_parts.append(context_text)
        
        # Add specific file requirements
        prompt_parts.append(f"\n🎯 GENERATE: {filename}")
        
        # Add file-specific instructions
        file_instructions = self._get_file_specific_instructions(filename, context)
        prompt_parts.append(file_instructions)
        
        # Add quality requirements
        min_lines = requirements.get('min_lines', 100)
        prompt_parts.append(f"""
📋 QUALITY REQUIREMENTS:
- Minimum {min_lines} lines of complete code
- Minimum 20 lines of business logic (not just imports/exports)
- No empty functions or placeholder comments
- Complete error handling and validation
- Professional documentation and comments
- Follow industry best practices for security and performance

🔧 OUTPUT FORMAT:
Return ONLY the complete file content. No JSON, no markdown blocks, no explanations.
Start directly with the file content (imports, comments, code, etc.).""")
        
        return "\n".join(prompt_parts)
    
    def _get_file_specific_instructions(self, filename: str, context: Dict[str, Any]) -> str:
        """Generate specific instructions based on file type and name"""
        
        filename_lower = filename.lower()
        instructions = []
        
        if 'controller' in filename_lower:
            instructions.extend([
                "🎯 CONTROLLER REQUIREMENTS:",
                "- Complete REST API endpoints (GET, POST, PUT, DELETE)",
                "- Request validation and sanitization",
                "- Error handling with proper HTTP status codes",
                "- Authentication and authorization middleware",
                "- Structured response formatting",
                "- Input validation using schemas/validators",
                "- Database integration with proper error handling",
                ""
            ])
            
        elif 'service' in filename_lower:
            instructions.extend([
                "🎯 SERVICE REQUIREMENTS:",
                "- Complete CRUD business logic operations",
                "- Data validation and sanitization",
                "- Complex business rules implementation", 
                "- Database transaction handling",
                "- Error handling with custom exceptions",
                "- Logging and monitoring integration",
                "- Performance optimizations (caching, pagination)",
                ""
            ])
            
        elif 'model' in filename_lower:
            instructions.extend([
                "🎯 MODEL/SCHEMA REQUIREMENTS:",
                "- Complete data model with all fields",
                "- Validation rules and constraints",
                "- Relationships and foreign keys",
                "- Indexes for performance",
                "- Custom methods for complex operations",
                "- Serialization/deserialization logic",
                "- Migration-friendly structure",
                ""
            ])
            
        elif 'component' in filename_lower and filename.endswith(('.tsx', '.jsx')):
            instructions.extend([
                "🎯 REACT COMPONENT REQUIREMENTS:",
                "- Complete functional component with hooks",
                "- State management (useState, useEffect, useContext)",
                "- Event handlers for all interactions",
                "- Proper TypeScript interfaces/props",
                "- Error boundaries and loading states",
                "- Accessibility features (ARIA labels, etc.)",
                "- Responsive design considerations",
                ""
            ])
            
        elif filename.endswith('.css'):
            instructions.extend([
                "🎯 STYLESHEET REQUIREMENTS:",
                "- Complete responsive design rules",
                "- Cross-browser compatibility",
                "- CSS Grid/Flexbox layouts",
                "- Dark mode support",
                "- Animation and transition effects",
                "- Print media queries",
                "- Performance optimizations",
                ""
            ])
        
        return "\n".join(instructions) if instructions else ""
    
    def _clean_response(self, response: str) -> str:
        """Clean and normalize LLM response"""
        
        if not response or not isinstance(response, str):
            return ""
        
        # Remove markdown code blocks
        response = re.sub(r'^```[a-z]*\n', '', response, flags=re.MULTILINE)
        response = re.sub(r'^```\s*$', '', response, flags=re.MULTILINE)
        
        # Remove explanatory text before code (common LLM behavior)
        lines = response.split('\n')
        
        # Find first line that looks like actual code
        code_start = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if (stripped.startswith(('import ', 'from ', 'const ', 'class ', 'function ', 
                                   'export ', '/**', '//', '/*', '{', 'interface ', 'type ')) or
                stripped.startswith(('<!DOCTYPE', '<html', '<', 'version:', 'FROM ', '#', 'SELECT'))):
                code_start = i
                break
        
        if code_start > 0:
            response = '\n'.join(lines[code_start:])
        
        # Clean up escaped characters
        response = response.replace('\\n', '\n').replace('\\\"', '"').replace("\\'", "'")
        
        # Remove trailing explanations after code
        lines = response.split('\n')
        
        # Find last meaningful code line
        code_end = len(lines)
        for i in range(len(lines) - 1, -1, -1):
            line = lines[i].strip()
            if (line and not line.startswith('This ') and not line.startswith('The ') and
                not line.startswith('Note:') and not line.startswith('Explanation:')):
                break
            code_end = i
        
        if code_end < len(lines):
            response = '\n'.join(lines[:code_end])
        
        return response.strip()
    
    def _get_fallback_template(self, filename: str, context: Dict[str, Any]) -> str:
        """Generate fallback template when LLM generation fails"""
        
        file_ext = filename.split('.')[-1].lower()
        filename_lower = filename.lower()
        
        if 'controller' in filename_lower and file_ext in ['ts', 'js']:
            return self._get_controller_template(filename, context)
        elif 'service' in filename_lower and file_ext in ['ts', 'js']:
            return self._get_service_template(filename, context)
        elif 'model' in filename_lower and file_ext in ['ts', 'js']:
            return self._get_model_template(filename, context)
        elif filename.endswith(('.tsx', '.jsx')):
            return self._get_component_template(filename, context)
        elif filename.endswith('.css'):
            return self._get_css_template(filename)
        else:
            return self._get_generic_template(filename, file_ext)
    
    def _get_controller_template(self, filename: str, context: Dict[str, Any]) -> str:
        """Generate controller template"""
        entity_name = filename.split('/')[-1].split('.')[0].replace('Controller', '').replace('controller', '')
        entity_lower = entity_name.lower()
        entity_cap = entity_name.capitalize()
        
        return f"""import express from 'express';
import {{ {entity_cap}Service }} from '../services/{entity_lower}.service';
import {{ validateRequest }} from '../middleware/validation';
import {{ authenticate }} from '../middleware/auth';
import {{ {entity_cap}CreateDto, {entity_cap}UpdateDto }} from '../dto/{entity_lower}.dto';

const router = express.Router();
const {entity_lower}Service = new {entity_cap}Service();

/**
 * Get all {entity_lower}s with pagination and filtering
 */
router.get('/', authenticate, async (req: express.Request, res: express.Response) => {{
    try {{
        const page = parseInt(req.query.page as string) || 1;
        const limit = parseInt(req.query.limit as string) || 10;
        const search = req.query.search as string;
        
        const result = await {entity_lower}Service.findAll({{
            page,
            limit,
            search,
            userId: req.user.id
        }});
        
        res.json({{
            success: true,
            data: result.items,
            pagination: {{
                page: result.page,
                limit: result.limit,
                total: result.total,
                pages: Math.ceil(result.total / result.limit)
            }}
        }});
    }} catch (error) {{
        console.error('Error fetching {entity_lower}s:', error);
        res.status(500).json({{
            success: false,
            message: 'Failed to fetch {entity_lower}s',
            error: process.env.NODE_ENV === 'development' ? error.message : undefined
        }});
    }}
}});

/**
 * Get {entity_lower} by ID
 */
router.get('/:id', authenticate, async (req: express.Request, res: express.Response) => {{
    try {{
        const id = parseInt(req.params.id);
        
        if (isNaN(id)) {{
            return res.status(400).json({{
                success: false,
                message: 'Invalid {entity_lower} ID'
            }});
        }}
        
        const {entity_lower} = await {entity_lower}Service.findById(id, req.user.id);
        
        if (!{entity_lower}) {{
            return res.status(404).json({{
                success: false,
                message: '{entity_cap} not found'
            }});
        }}
        
        res.json({{
            success: true,
            data: {entity_lower}
        }});
    }} catch (error) {{
        console.error('Error fetching {entity_lower}:', error);
        res.status(500).json({{
            success: false,
            message: 'Failed to fetch {entity_lower}',
            error: process.env.NODE_ENV === 'development' ? error.message : undefined
        }});
    }}
}});

/**
 * Create new {entity_lower}
 */
router.post('/', authenticate, validateRequest({entity_cap}CreateDto), async (req: express.Request, res: express.Response) => {{
    try {{
        const createData = req.body;
        createData.userId = req.user.id;
        
        const new{entity_cap} = await {entity_lower}Service.create(createData);
        
        res.status(201).json({{
            success: true,
            message: '{entity_cap} created successfully',
            data: new{entity_cap}
        }});
    }} catch (error) {{
        console.error('Error creating {entity_lower}:', error);
        
        if (error.name === 'ValidationError') {{
            return res.status(400).json({{
                success: false,
                message: 'Validation failed',
                errors: error.errors
            }});
        }}
        
        res.status(500).json({{
            success: false,
            message: 'Failed to create {entity_lower}',
            error: process.env.NODE_ENV === 'development' ? error.message : undefined
        }});
    }}
}});

/**
 * Update {entity_lower}
 */
router.put('/:id', authenticate, validateRequest({entity_cap}UpdateDto), async (req: express.Request, res: express.Response) => {{
    try {{
        const id = parseInt(req.params.id);
        
        if (isNaN(id)) {{
            return res.status(400).json({{
                success: false,
                message: 'Invalid {entity_lower} ID'
            }});
        }}
        
        const updated{entity_cap} = await {entity_lower}Service.update(id, req.body, req.user.id);
        
        if (!updated{entity_cap}) {{
            return res.status(404).json({{
                success: false,
                message: '{entity_cap} not found or access denied'
            }});
        }}
        
        res.json({{
            success: true,
            message: '{entity_cap} updated successfully',
            data: updated{entity_cap}
        }});
    }} catch (error) {{
        console.error('Error updating {entity_lower}:', error);
        
        if (error.name === 'ValidationError') {{
            return res.status(400).json({{
                success: false,
                message: 'Validation failed',
                errors: error.errors
            }});
        }}
        
        res.status(500).json({{
            success: false,
            message: 'Failed to update {entity_lower}',
            error: process.env.NODE_ENV === 'development' ? error.message : undefined
        }});
    }}
}});

/**
 * Delete {entity_lower}
 */
router.delete('/:id', authenticate, async (req: express.Request, res: express.Response) => {{
    try {{
        const id = parseInt(req.params.id);
        
        if (isNaN(id)) {{
            return res.status(400).json({{
                success: false,
                message: 'Invalid {entity_lower} ID'
            }});
        }}
        
        const deleted = await {entity_lower}Service.delete(id, req.user.id);
        
        if (!deleted) {{
            return res.status(404).json({{
                success: false,
                message: '{entity_cap} not found or access denied'
            }});
        }}
        
        res.json({{
            success: true,
            message: '{entity_cap} deleted successfully'
        }});
    }} catch (error) {{
        console.error('Error deleting {entity_lower}:', error);
        res.status(500).json({{
            success: false,
            message: 'Failed to delete {entity_lower}',
            error: process.env.NODE_ENV === 'development' ? error.message : undefined
        }});
    }}
}});

export default router;"""
    
    def _get_service_template(self, filename: str, context: Dict[str, Any]) -> str:
        """Generate service template"""
        entity_name = filename.split('/')[-1].split('.')[0].replace('Service', '').replace('service', '')
        entity_lower = entity_name.lower()
        entity_cap = entity_name.capitalize()
        
        return f"""import {{ {entity_cap} }} from '../models/{entity_lower}';
import {{ {entity_cap}CreateDto, {entity_cap}UpdateDto }} from '../dto/{entity_lower}.dto';
import {{ PaginationOptions, PaginationResult }} from '../types/pagination';
import {{ DatabaseError, ValidationError, NotFoundError }} from '../errors/custom.errors';

export class {entity_cap}Service {{
    
    /**
     * Find all {entity_lower}s with pagination and filtering
     */
    async findAll(options: PaginationOptions & {{ userId: number; search?: string }}): Promise<PaginationResult<{entity_cap}>> {{
        try {{
            const {{ page = 1, limit = 10, search, userId }} = options;
            const offset = (page - 1) * limit;
            
            let whereClause = {{ userId }};
            
            if (search) {{
                whereClause = {{
                    ...whereClause,
                    OR: [
                        {{ title: {{ contains: search, mode: 'insensitive' }} }},
                        {{ description: {{ contains: search, mode: 'insensitive' }} }}
                    ]
                }};
            }}
            
            const [items, total] = await Promise.all([
                {entity_cap}.findMany({{
                    where: whereClause,
                    orderBy: {{ createdAt: 'desc' }},
                    skip: offset,
                    take: limit,
                    include: {{
                        user: {{ select: {{ id: true, name: true, email: true }} }}
                    }}
                }}),
                {entity_cap}.count({{ where: whereClause }})
            ]);
            
            return {{
                items,
                total,
                page,
                limit
            }};
        }} catch (error) {{
            throw new DatabaseError(`Failed to fetch {entity_lower}s: ${{error.message}}`);
        }}
    }}
    
    /**
     * Find {entity_lower} by ID
     */
    async findById(id: number, userId: number): Promise<{entity_cap} | null> {{
        try {{
            const {entity_lower} = await {entity_cap}.findFirst({{
                where: {{ id, userId }},
                include: {{
                    user: {{ select: {{ id: true, name: true, email: true }} }}
                }}
            }});
            
            return {entity_lower};
        }} catch (error) {{
            throw new DatabaseError(`Failed to fetch {entity_lower}: ${{error.message}}`);
        }}
    }}
    
    /**
     * Create new {entity_lower}
     */
    async create(data: {entity_cap}CreateDto): Promise<{entity_cap}> {{
        try {{
            // Validate business rules
            await this.validateCreate(data);
            
            const {entity_lower} = await {entity_cap}.create({{
                data: {{
                    ...data,
                    createdAt: new Date(),
                    updatedAt: new Date()
                }},
                include: {{
                    user: {{ select: {{ id: true, name: true, email: true }} }}
                }}
            }});
            
            return {entity_lower};
        }} catch (error) {{
            if (error.name === 'ValidationError') {{
                throw error;
            }}
            throw new DatabaseError(`Failed to create {entity_lower}: ${{error.message}}`);
        }}
    }}
    
    /**
     * Update {entity_lower}
     */
    async update(id: number, data: {entity_cap}UpdateDto, userId: number): Promise<{entity_cap} | null> {{
        try {{
            // Check if {entity_lower} exists and belongs to user
            const existing = await this.findById(id, userId);
            if (!existing) {{
                return null;
            }}
            
            // Validate business rules
            await this.validateUpdate(id, data, userId);
            
            const updated{entity_cap} = await {entity_cap}.update({{
                where: {{ id, userId }},
                data: {{
                    ...data,
                    updatedAt: new Date()
                }},
                include: {{
                    user: {{ select: {{ id: true, name: true, email: true }} }}
                }}
            }});
            
            return updated{entity_cap};
        }} catch (error) {{
            if (error.name === 'ValidationError') {{
                throw error;
            }}
            throw new DatabaseError(`Failed to update {entity_lower}: ${{error.message}}`);
        }}
    }}
    
    /**
     * Delete {entity_lower}
     */
    async delete(id: number, userId: number): Promise<boolean> {{
        try {{
            // Check if {entity_lower} exists and belongs to user
            const existing = await this.findById(id, userId);
            if (!existing) {{
                return false;
            }}
            
            await {entity_cap}.delete({{
                where: {{ id, userId }}
            }});
            
            return true;
        }} catch (error) {{
            throw new DatabaseError(`Failed to delete {entity_lower}: ${{error.message}}`);
        }}
    }}
    
    /**
     * Validate create operation
     */
    private async validateCreate(data: {entity_cap}CreateDto): Promise<void> {{
        // Check for duplicate titles for the same user
        if (data.title) {{
            const existing = await {entity_cap}.findFirst({{
                where: {{
                    title: data.title,
                    userId: data.userId
                }}
            }});
            
            if (existing) {{
                throw new ValidationError('A {entity_lower} with this title already exists');
            }}
        }}
        
        // Additional business rule validations
        if (data.startDate && data.endDate && data.startDate > data.endDate) {{
            throw new ValidationError('Start date cannot be after end date');
        }}
    }}
    
    /**
     * Validate update operation
     */
    private async validateUpdate(id: number, data: {entity_cap}UpdateDto, userId: number): Promise<void> {{
        // Check for duplicate titles (excluding current record)
        if (data.title) {{
            const existing = await {entity_cap}.findFirst({{
                where: {{
                    title: data.title,
                    userId,
                    NOT: {{ id }}
                }}
            }});
            
            if (existing) {{
                throw new ValidationError('A {entity_lower} with this title already exists');
            }}
        }}
        
        // Additional business rule validations
        if (data.startDate && data.endDate && data.startDate > data.endDate) {{
            throw new ValidationError('Start date cannot be after end date');
        }}
    }}
}}"""
    
    def _get_model_template(self, filename: str, context: Dict[str, Any]) -> str:
        """Generate model template"""
        entity_name = filename.split('/')[-1].split('.')[0].replace('Model', '').replace('model', '')
        entity_cap = entity_name.capitalize()
        
        return f"""export interface {entity_cap} {{
    id: number;
    title: string;
    description?: string;
    status: {entity_cap}Status;
    priority: {entity_cap}Priority;
    userId: number;
    createdAt: Date;
    updatedAt: Date;
    startDate?: Date;
    endDate?: Date;
    tags?: string[];
    metadata?: Record<string, any>;
}}

export enum {entity_cap}Status {{
    DRAFT = 'DRAFT',
    IN_PROGRESS = 'IN_PROGRESS', 
    COMPLETED = 'COMPLETED',
    CANCELLED = 'CANCELLED'
}}

export enum {entity_cap}Priority {{
    LOW = 'LOW',
    MEDIUM = 'MEDIUM',
    HIGH = 'HIGH',
    URGENT = 'URGENT'
}}

export interface {entity_cap}CreateDto {{
    title: string;
    description?: string;
    status?: {entity_cap}Status;
    priority?: {entity_cap}Priority;
    userId: number;
    startDate?: Date;
    endDate?: Date;
    tags?: string[];
    metadata?: Record<string, any>;
}}

export interface {entity_cap}UpdateDto {{
    title?: string;
    description?: string;
    status?: {entity_cap}Status;
    priority?: {entity_cap}Priority;
    startDate?: Date;
    endDate?: Date;
    tags?: string[];
    metadata?: Record<string, any>;
}}

export default {entity_cap};"""
    
    def _get_component_template(self, filename: str, context: Dict[str, Any]) -> str:
        """Generate React component template"""
        component_name = filename.split('/')[-1].split('.')[0]
        
        return f"""import React, {{ useState, useEffect, useCallback }} from 'react';
import {{ 
    Box, 
    Button, 
    TextField, 
    Typography, 
    CircularProgress,
    Alert,
    Card,
    CardContent
}} from '@mui/material';

interface {component_name}Props {{
    id?: number;
    onSave?: (data: any) => void;
    onCancel?: () => void;
    initialData?: any;
}}

const {component_name}: React.FC<{component_name}Props> = ({{
    id,
    onSave,
    onCancel,
    initialData
}}) => {{
    const [formData, setFormData] = useState(initialData || {{}});
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [success, setSuccess] = useState(false);

    useEffect(() => {{
        if (id) {{
            loadData();
        }}
    }}, [id]);

    const loadData = async () => {{
        try {{
            setLoading(true);
            // Load data logic here
            // const data = await api.getData(id);
            // setFormData(data);
        }} catch (err) {{
            setError('Failed to load data');
        }} finally {{
            setLoading(false);
        }}
    }};

    const handleSubmit = useCallback(async (e: React.FormEvent) => {{
        e.preventDefault();
        
        try {{
            setLoading(true);
            setError(null);
            
            // Validation
            if (!formData.title) {{
                throw new Error('Title is required');
            }}
            
            // Submit logic here
            if (onSave) {{
                await onSave(formData);
                setSuccess(true);
            }}
            
        }} catch (err) {{
            setError(err instanceof Error ? err.message : 'An error occurred');
        }} finally {{
            setLoading(false);
        }}
    }}, [formData, onSave]);

    const handleChange = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) => {{
        setFormData(prev => ({{
            ...prev,
            [field]: e.target.value
        }}));
    }};

    if (loading && !formData.id) {{
        return (
            <Box display="flex" justifyContent="center" p={4}>
                <CircularProgress />
            </Box>
        );
    }}

    return (
        <Card>
            <CardContent>
                <Typography variant="h5" gutterBottom>
                    {{id ? 'Edit' : 'Create'}} Item
                </Typography>

                {{error && (
                    <Alert severity="error" sx={{{{ mb: 2 }}}}>
                        {{error}}
                    </Alert>
                )}}

                {{success && (
                    <Alert severity="success" sx={{{{ mb: 2 }}}}>
                        Item saved successfully!
                    </Alert>
                )}}

                <Box component="form" onSubmit={{handleSubmit}} noValidate>
                    <TextField
                        fullWidth
                        label="Title"
                        value={{formData.title || ''}}
                        onChange={{handleChange('title')}}
                        margin="normal"
                        required
                        error={{!!error && !formData.title}}
                        helperText={{!!error && !formData.title ? 'Title is required' : ''}}
                    />

                    <TextField
                        fullWidth
                        label="Description"
                        value={{formData.description || ''}}
                        onChange={{handleChange('description')}}
                        margin="normal"
                        multiline
                        rows={{4}}
                    />

                    <Box sx={{{{ mt: 3, display: 'flex', gap: 2 }}}}>
                        <Button
                            type="submit"
                            variant="contained"
                            disabled={{loading}}
                            startIcon={{loading ? <CircularProgress size={20} /> : null}}
                        >
                            {{loading ? 'Saving...' : 'Save'}}
                        </Button>
                        
                        {{onCancel && (
                            <Button
                                variant="outlined"
                                onClick={{onCancel}}
                                disabled={{loading}}
                            >
                                Cancel
                            </Button>
                        )}}
                    </Box>
                </Box>
            </CardContent>
        </Card>
    );
}};

export default {component_name};"""
    
    def _get_css_template(self, filename: str) -> str:
        """Generate CSS template"""
        return """/* Modern CSS Reset and Base Styles */
*, *::before, *::after {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

html {
    font-size: 16px;
    scroll-behavior: smooth;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
    line-height: 1.6;
    color: var(--text-primary);
    background-color: var(--bg-primary);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
}

/* CSS Custom Properties (CSS Variables) */
:root {
    /* Colors */
    --primary: #3b82f6;
    --primary-hover: #2563eb;
    --secondary: #6b7280;
    --success: #10b981;
    --warning: #f59e0b;
    --error: #ef4444;
    
    /* Light theme */
    --bg-primary: #ffffff;
    --bg-secondary: #f8fafc;
    --bg-tertiary: #f1f5f9;
    --text-primary: #1f2937;
    --text-secondary: #6b7280;
    --text-muted: #9ca3af;
    --border: #e5e7eb;
    --border-hover: #d1d5db;
    
    /* Spacing */
    --space-xs: 0.25rem;
    --space-sm: 0.5rem;
    --space-md: 1rem;
    --space-lg: 1.5rem;
    --space-xl: 2rem;
    --space-2xl: 3rem;
    
    /* Border radius */
    --radius-sm: 0.25rem;
    --radius-md: 0.375rem;
    --radius-lg: 0.5rem;
    --radius-xl: 0.75rem;
    
    /* Shadows */
    --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
    --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
    --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
    
    /* Transitions */
    --transition-fast: 150ms ease-in-out;
    --transition-normal: 200ms ease-in-out;
    --transition-slow: 300ms ease-in-out;
}

/* Dark theme */
@media (prefers-color-scheme: dark) {
    :root {
        --bg-primary: #111827;
        --bg-secondary: #1f2937;
        --bg-tertiary: #374151;
        --text-primary: #f9fafb;
        --text-secondary: #d1d5db;
        --text-muted: #9ca3af;
        --border: #374151;
        --border-hover: #4b5563;
    }
}

/* Layout Components */
.container {
    width: 100%;
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 var(--space-md);
}

.grid {
    display: grid;
    gap: var(--space-lg);
}

.flex {
    display: flex;
    align-items: center;
    gap: var(--space-md);
}

.flex-col {
    flex-direction: column;
}

.justify-between {
    justify-content: space-between;
}

.justify-center {
    justify-content: center;
}

.items-start {
    align-items: flex-start;
}

/* Typography */
.heading-1 {
    font-size: 2.25rem;
    font-weight: 800;
    line-height: 1.2;
    color: var(--text-primary);
}

.heading-2 {
    font-size: 1.875rem;
    font-weight: 700;
    line-height: 1.3;
    color: var(--text-primary);
}

.heading-3 {
    font-size: 1.5rem;
    font-weight: 600;
    line-height: 1.4;
    color: var(--text-primary);
}

.text-lg {
    font-size: 1.125rem;
    line-height: 1.75;
}

.text-sm {
    font-size: 0.875rem;
    line-height: 1.25;
}

.text-xs {
    font-size: 0.75rem;
    line-height: 1;
}

.text-muted {
    color: var(--text-muted);
}

/* Buttons */
.btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: var(--space-sm);
    padding: var(--space-sm) var(--space-lg);
    font-size: 0.875rem;
    font-weight: 500;
    line-height: 1;
    text-decoration: none;
    border: 1px solid transparent;
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: all var(--transition-fast);
    white-space: nowrap;
}

.btn:focus {
    outline: 2px solid var(--primary);
    outline-offset: 2px;
}

.btn-primary {
    background-color: var(--primary);
    color: white;
}

.btn-primary:hover {
    background-color: var(--primary-hover);
}

.btn-secondary {
    background-color: var(--bg-secondary);
    color: var(--text-primary);
    border-color: var(--border);
}

.btn-secondary:hover {
    background-color: var(--bg-tertiary);
    border-color: var(--border-hover);
}

/* Cards */
.card {
    background-color: var(--bg-primary);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-sm);
    overflow: hidden;
    transition: box-shadow var(--transition-normal);
}

.card:hover {
    box-shadow: var(--shadow-md);
}

.card-header {
    padding: var(--space-lg);
    border-bottom: 1px solid var(--border);
}

.card-body {
    padding: var(--space-lg);
}

.card-footer {
    padding: var(--space-lg);
    background-color: var(--bg-secondary);
    border-top: 1px solid var(--border);
}

/* Forms */
.form-group {
    margin-bottom: var(--space-lg);
}

.form-label {
    display: block;
    margin-bottom: var(--space-xs);
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-primary);
}

.form-input {
    width: 100%;
    padding: var(--space-sm) var(--space-md);
    font-size: 0.875rem;
    background-color: var(--bg-primary);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    transition: border-color var(--transition-fast);
}

.form-input:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: 0 0 0 3px rgb(59 130 246 / 0.1);
}

.form-textarea {
    resize: vertical;
    min-height: 100px;
}

/* Responsive Design */
@media (max-width: 768px) {
    .container {
        padding: 0 var(--space-sm);
    }
    
    .grid {
        gap: var(--space-md);
    }
    
    .flex {
        gap: var(--space-sm);
    }
    
    .heading-1 {
        font-size: 1.875rem;
    }
    
    .heading-2 {
        font-size: 1.5rem;
    }
    
    .btn {
        padding: var(--space-xs) var(--space-md);
        font-size: 0.8rem;
    }
}

/* Utilities */
.sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
}

.loading {
    opacity: 0.6;
    pointer-events: none;
}

.hidden {
    display: none;
}

/* Animations */
@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

@keyframes slideUp {
    from {
        opacity: 0;
        transform: translateY(10px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.fade-in {
    animation: fadeIn var(--transition-normal);
}

.slide-up {
    animation: slideUp var(--transition-normal);
}"""
    
    def _get_generic_template(self, filename: str, file_ext: str) -> str:
        """Generate generic template for unknown file types"""
        return f"""/*
 * {filename}
 * Generated fallback template
 * 
 * This file needs to be implemented according to the project requirements.
 */

// TODO: Implement {filename} based on the application requirements
// This is a fallback template that should be replaced with actual implementation

export default {{}};"""
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """Get statistics about file generation attempts"""
        if not self.generation_history:
            return {"total_files": 0, "success_rate": 0, "average_attempts": 0}
        
        total_files = len(self.generation_history)
        successful_files = sum(1 for h in self.generation_history if h.get('success', False))
        total_attempts = sum(h.get('attempts', 0) for h in self.generation_history)
        fallback_used = sum(1 for h in self.generation_history if h.get('fallback_used', False))
        
        return {
            "total_files": total_files,
            "successful_files": successful_files,
            "success_rate": (successful_files / total_files * 100) if total_files > 0 else 0,
            "average_attempts": total_attempts / total_files if total_files > 0 else 0,
            "fallback_used": fallback_used,
            "fallback_rate": (fallback_used / total_files * 100) if total_files > 0 else 0
        }
