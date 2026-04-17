from dataclasses import dataclass

@dataclass
class TodoItem:
    id: int
    task: str
    done: bool

@dataclass
class SpacedRepItem:
    topic: str
    module: str
    conf: int
    days_ago: int
    urgency: int