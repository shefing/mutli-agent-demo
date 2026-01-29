"""
Core shared logic for scanner execution
Used by both UI and CLI
"""

from .scanner_runner import run_scanners_on_session, aggregate_results

__all__ = ['run_scanners_on_session', 'aggregate_results']
