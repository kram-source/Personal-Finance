"""Backward-compatible facade for the refactored src.services modules.

Existing imports such as `import core` continue to work.
"""
from src.services.database import *
from src.services.categorization import *
from src.services.transactions import *
from src.services.anomaly_detection import *
from src.services.duplicate_detection import *
from src.services.insights import *
from src.services.prediction import *
