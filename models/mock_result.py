from dataclasses import dataclass

@dataclass
class ErrorLogEntry:
    id: int
    date: str
    topic: str
    error_type: str
    concept: str
    tags: str