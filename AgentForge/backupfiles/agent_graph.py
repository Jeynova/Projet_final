# agent_graph.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Set, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import traceback
import time
import copy


@dataclass
class Node:
    name: str
    run: Callable[[Dict[str, Any]], Dict[str, Any]]
    can_run: Callable[[Dict[str, Any]], bool]
    max_retries: int = 0
    parallel_group: Optional[str] = None
    repeatable: bool = False  # <= permet aux noeuds de se ré-exécuter (boucles)


@dataclass
class GraphConfig:
    nodes: Dict[str, Node]
    # callbacks UI / télémétrie
    on_start: Optional[Callable[[str, Dict[str, Any]], None]] = None
    on_complete: Optional[Callable[[str, Dict[str, Any], Dict[str, Any]], None]] = None
    on_error: Optional[Callable[[str, Exception], None]] = None
    # scheduling
    max_steps: int = 100
    concurrency: int = 1          # >1 => exécution parallèle
    tick_sleep: float = 0.0       # pause courte (respiration UI)


class GraphRunner:
    """
    Planificateur adaptatif :
      - scanne les noeuds prêts (can_run(state) == True et pas déjà terminés)
      - exécute les lots (parallèles si autorisé)
      - fusionne les résultats dans l'état partagé
      - s'arrête quand plus rien n'est prêt ou max_steps atteint
    """
    def __init__(self, config: GraphConfig):
        self.cfg = config
        self._done: Set[str] = set()
        self._running: Set[str] = set()

    def run(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        state = dict(initial_state)
        steps = 0

        while steps < self.cfg.max_steps:
            steps += 1

            # 1) noeuds prêts
            ready = [
                n for n in self.cfg.nodes.values()
                if n.name not in self._done
                and n.name not in self._running
                and _safe_can_run(n, state)
            ]
            if not ready and not self._running:
                break  # plus de travail

            # 2) batching par groupe parallèle
            batches: List[List[Node]] = []
            if self.cfg.concurrency > 1 and ready:
                groups: Dict[str, List[Node]] = {}
                singles: List[Node] = []
                for n in ready:
                    if n.parallel_group:
                        groups.setdefault(n.parallel_group, []).append(n)
                    else:
                        singles.append(n)
                batches = list(groups.values()) + [[n] for n in singles]
            else:
                batches = [[n] for n in ready]  # série

            # 3) exécution des batches
            for batch in batches:
                if not batch:
                    continue

                # télémétrie : start
                for node in batch:
                    self._running.add(node.name)
                    if self.cfg.on_start:
                        try:
                            self.cfg.on_start(node.name, state)
                        except Exception:
                            pass

                # stratégie : parallèle dans le batch si possible
                if self.cfg.concurrency > 1 and len(batch) > 1:
                    with ThreadPoolExecutor(max_workers=min(self.cfg.concurrency, len(batch))) as ex:
                        fut_map = {
                            # on passe un snapshot de l'état pour éviter les mutations concurrentes
                            ex.submit(_safe_run, node, copy.deepcopy(state)): node
                            for node in batch
                        }
                        for fut in as_completed(fut_map):
                            node = fut_map[fut]
                            try:
                                result = fut.result()
                                state.update(result or {})
                                if self.cfg.on_complete:
                                    self.cfg.on_complete(node.name, state, result or {})
                            except Exception as e:
                                if self.cfg.on_error:
                                    self.cfg.on_error(node.name, e)

                    # marquage fin d'exécution des noeuds du batch
                    for node in batch:
                        self._running.discard(node.name)
                        if not node.repeatable:
                            self._done.add(node.name)

                else:
                    # exécution série
                    for node in batch:
                        try:
                            # idem : snapshot d'état
                            result = _safe_run(node, copy.deepcopy(state))
                            state.update(result or {})
                            if self.cfg.on_complete:
                                self.cfg.on_complete(node.name, state, result or {})
                        except Exception as e:
                            if self.cfg.on_error:
                                self.cfg.on_error(node.name, e)
                        finally:
                            self._running.discard(node.name)
                            if not node.repeatable:
                                self._done.add(node.name)

            if self.cfg.tick_sleep:
                time.sleep(self.cfg.tick_sleep)

        return state


def _safe_can_run(node: Node, state: Dict[str, Any]) -> bool:
    try:
        return node.can_run(state)
    except Exception:
        return False


def _safe_run(node: Node, state: Dict[str, Any]) -> Dict[str, Any]:
    try:
        return node.run(state) or {}
    except Exception:
        traceback.print_exc()
        raise