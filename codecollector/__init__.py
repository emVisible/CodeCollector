"""CodeCollector - Collect project code files for AI assistants."""

__version__ = "1.0.0"
__author__ = "thawn"
__license__ = "MIT"

from codecollector.collector import FileCollector
from codecollector.config import CollectorConfig

__all__ = ["FileCollector", "CollectorConfig", "__version__"]