# Setup script for Enhanced Agentic System
# PowerShell script to set up the environment

param(
    [switch]$Enhanced,
    [switch]$InstallDeps,
    [switch]$Test
)

Write-Host "🚀 AgentForge Enhanced Agentic Setup" -ForegroundColor Cyan

# Check if we're in the right directory
if (-not (Test-Path "requirements.txt")) {
    Write-Host "❌ Please run this script from the AgentForge directory" -ForegroundColor Red
    exit 1
}

# Install enhanced dependencies
if ($InstallDeps -or $Enhanced) {
    Write-Host "📦 Installing enhanced agentic dependencies..." -ForegroundColor Yellow
    
    # Install base requirements first
    pip install -r requirements.txt
    
    # Install enhanced requirements
    pip install -r requirements-enhanced-agentic.txt
    
    Write-Host "Dependencies installed" -ForegroundColor Green
}

# Set up enhanced agentic mode
if ($Enhanced) {
    Write-Host "⚙️ Configuring enhanced agentic mode..." -ForegroundColor Yellow
    
    # Update .env file
    $envContent = @"
# Enhanced Agentic Configuration
AGENTFORGE_AGENTIC=1
AGENTFORGE_MODE=hybrid
AGENTFORGE_ASK=1

# Enhanced features
FEATURE_MEMORY=1
FEATURE_SPEC_REFINER=1
FEATURE_TECH_VALIDATOR=1
FEATURE_INFRA_AGENT=1
FEATURE_VALIDATION=1

# Comparison mode
AGENTFORGE_COMPARE_APPROACHES=1

# LLM Provider
AGENTFORGE_LLM=ollama
"@
    
    $envContent | Out-File -FilePath ".env" -Encoding UTF8
    
    Write-Host "Enhanced agentic mode configured" -ForegroundColor Green
}

# Run tests
if ($Test -or $Enhanced) {
    Write-Host "🧪 Running enhanced agentic tests..." -ForegroundColor Yellow
    
    python test_enhanced_agentic.py
    
    Write-Host "Tests completed" -ForegroundColor Green
}

# Create sample RAG snippets
if ($Enhanced) {
    Write-Host "📚 Creating RAG snippets..." -ForegroundColor Yellow
    
    # Create rag_snippets directory
    New-Item -ItemType Directory -Force -Path "rag_snippets" | Out-Null
    
    # Create sample snippets
    @"
# Authentication Patterns

## JWT Authentication
```python
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer
import jwt

security = HTTPBearer()

def verify_token(token: str = Depends(security)):
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

## Session-based Authentication
```python
from fastapi import Request, HTTPException
from starlette.middleware.sessions import SessionMiddleware

def require_auth(request: Request):
    if "user_id" not in request.session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return request.session["user_id"]
```
"@ | Out-File -FilePath "rag_snippets/auth_patterns.md" -Encoding UTF8

    @"
# Error Handling Patterns

## FastAPI Error Handling
```python
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"error": "Invalid input", "detail": str(exc)}
    )

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={"error": "Resource not found", "path": str(request.url)}
    )
```

## Database Error Handling
```python
import sqlalchemy.exc
from contextlib import contextmanager

@contextmanager
def db_transaction():
    try:
        yield
        db.commit()
    except sqlalchemy.exc.IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Integrity constraint violation")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail="Database error")
```
"@ | Out-File -FilePath "rag_snippets/error_handling.md" -Encoding UTF8

    Write-Host "RAG snippets created" -ForegroundColor Green
}

Write-Host ""
Write-Host "Enhanced Agentic System setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Test the system: python test_enhanced_agentic.py" -ForegroundColor White
Write-Host "  2. Run a comparison: python orchestrator/enhanced_smart_graph.py" -ForegroundColor White
Write-Host "  3. Create a project: python graph.py --prompt 'your project description'" -ForegroundColor White
Write-Host ""
Write-Host "Configuration:" -ForegroundColor Cyan
Write-Host "  - Mode: hybrid (templates + agents)" -ForegroundColor White
Write-Host "  - Ask questions: enabled" -ForegroundColor White
Write-Host "  - Memory: enabled" -ForegroundColor White
Write-Host "  - Validation: enabled" -ForegroundColor White
