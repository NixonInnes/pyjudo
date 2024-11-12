from enum import Enum

class ServiceLife(Enum):
    SINGLETON = 1
    SCOPED = 2
    TRANSIENT = 3