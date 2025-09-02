#!/usr/bin/env python3
"""
🔄 EVENT SYSTEM
Standardized event handling utilities
"""

from typing import Dict, Any, List


def emit_event(state: Dict[str, Any], event: Dict[str, Any]):
    """Emit a standardized event with type and meta fields"""
    events = state.setdefault('events', [])
    
    # Ensure event has proper structure
    if isinstance(event, str):
        # Convert string events to dict format
        event = {"type": event, "meta": {}}
    elif not isinstance(event, dict):
        event = {"type": str(event), "meta": {}}
    elif 'type' not in event:
        event = {"type": "unknown", "meta": event}
    
    events.append(event)


def get_event_type(event) -> str:
    """Safely extract event type from either string or dict format"""
    if isinstance(event, dict):
        return event.get('type', 'unknown')
    return str(event)


def filter_events_by_type(events: List, exclude_type: str) -> List:
    """Filter out events of a specific type, handling both string and dict formats"""
    return [e for e in events if get_event_type(e) != exclude_type]


def has_event_type(events: List, event_type: str) -> bool:
    """Check if events list contains an event of the specified type"""
    return any(get_event_type(e) == event_type for e in events)
