#!/usr/bin/env python3
"""
📅 SCHEDULING UTILITIES
Agent scheduling and queue management
"""

from typing import Dict, Any, Union, List


def schedule_agents(state: Dict[str, Any], agent_ids: Union[str, List[str]], front: bool = False):
    """Schedule agents for execution in the pipeline queue"""
    q = state.setdefault('next_agents', [])
    if isinstance(agent_ids, str):
        agent_ids = [agent_ids]
    
    for aid in agent_ids:
        if front:
            q.insert(0, aid)
        else:
            q.append(aid)
