"""OnePaste - Collect project code files for AI assistants."""

__version__ = "1.3.2"
__author__ = "thawn"
__license__ = "MIT"

from onepaste.collector import FileCollector
from onepaste.config import CollectorConfig

__all__ = ["FileCollector", "CollectorConfig", "__version__"]