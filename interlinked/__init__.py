import importlib.metadata

from .router import Router  # noqa [F401]
from .workflow import provide, depend, run, default_workflow, Workflow  # noqa [F401]


__version__ = importlib.metadata.version(__name__)
