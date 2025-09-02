#!/usr/bin/env python3
"""
🎭 ORGANIC INTELLIGENCE: Multi-Perspective Team + Learning Guidance
⚠️ DEPRECATED: This monolith has been refactored into modular components.

New structure:
- Agents → agents/memory/, agents/team/, agents/product/
- Core utilities → core/domain_detection.py, core/events.py, core/scheduling.py, core/contracts.py
- Orchestrator → orchestrators/pipeline.py
- Tests → tests/test_pipeline.py

Use: from tests.test_pipeline import test_organic_intelligence
"""

# Re-export for backward compatibility
from tests.test_pipeline import test_organic_intelligence

if __name__ == "__main__":
    print("⚠️ This file is deprecated. Running test via new modular structure...")
    test_organic_intelligence()
