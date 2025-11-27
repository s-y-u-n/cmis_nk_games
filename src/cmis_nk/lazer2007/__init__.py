"""Lazer & Friedman (2007) scenario namespace.

This module simply re-exports the generic NK simulation and game-table builder
for consistency with other scenario-specific namespaces (levinthal, ethiraj).
"""

from .game_table import GameTableBuilder, AverageFinalScoreProtocol, GameValueProtocol
from ..agents import Agent, create_agents
from ..networks import NetworkFactory
from ..simulation import SimulationConfig, SimulationEngine, SimulationResult
from ..landscape import NKLandscape

__all__ = [
    "GameTableBuilder",
    "AverageFinalScoreProtocol",
    "GameValueProtocol",
    "Agent",
    "create_agents",
    "NetworkFactory",
    "SimulationConfig",
    "SimulationEngine",
    "SimulationResult",
    "NKLandscape",
]
