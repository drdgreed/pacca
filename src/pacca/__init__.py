"""
PACCA - Prior Authorization & Care Coordination Agent Platform

A multi-agent AI system for automating healthcare prior authorization workflows
while maintaining human-centered decision-making for high-stakes cases.
"""

__version__ = "0.1.0"
__author__ = "PACCA Team"

from pacca.config.settings import get_settings

__all__ = ["__version__", "get_settings"]
