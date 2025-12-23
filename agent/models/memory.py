from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime
from enum import Enum


@dataclass
class TopicMemory:
    topic_id: str
    topic_name: Optional[str]

    predecessors_limitations: str
    core_proposal: str
    enabling_conditions: str
    problems_solved: str
    operational_understanding: str

    progress_history: List[dict] = field(default_factory=list)
    last_updated_ts: Optional[datetime] = None


class SchemaSection(str, Enum):
    PREDECESSORS_LIMITATIONS = "predecessors_limitations"
    CORE_PROPOSAL = "core_proposal"
    ENABLING_CONDITIONS = "enabling_conditions"
    PROBLEMS_SOLVED = "problems_solved"
    OPERATIONAL_UNDERSTANDING = "operational_understanding"
