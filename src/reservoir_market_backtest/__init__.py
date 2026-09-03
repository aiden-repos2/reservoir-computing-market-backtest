"""Reconstruction tools for the historical reservoir-computing market backtest."""

from .backtest import StrategyResult, strategy_returns
from .metrics import PerformanceMetrics, summarize_returns
from .model import FROZEN_IKEDA_CONFIGURATION, IkedaConfiguration, ikeda_states
from .pipeline import SymbolBacktest, equal_weight_common_dates, run_symbol_backtest

__all__ = [
    "PerformanceMetrics",
    "FROZEN_IKEDA_CONFIGURATION",
    "IkedaConfiguration",
    "StrategyResult",
    "SymbolBacktest",
    "equal_weight_common_dates",
    "run_symbol_backtest",
    "strategy_returns",
    "summarize_returns",
    "ikeda_states",
]

__version__ = "1.0.0"
