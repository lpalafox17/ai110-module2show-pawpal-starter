from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import List, Optional, Dict, Any
import uuid


def _new_id() -> str:
    return str(uuid.uuid4())


class Priority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class TimeWindow:
    start: datetime
    end: datetime


@dataclass
class Constraint:
    id: str = field(default_factory=_new_id)
    constraint_type: str = ""  # e.g. "time_budget", "unavailable_window", "must_after"
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Preference:
    id: str = field(default_factory=_new_id)
    applies_to: str = "owner"  # "owner" or "pet"
    entity_id: Optional[str] = None
    preferred_time_windows: List[TimeWindow] = field(default_factory=list)
    max_daily_time_minutes: Optional[int] = None


@dataclass
class PetCareTask:
    id: str = field(default_factory=_new_id)
    title: str = ""
    duration_minutes: int = 0
    priority: Priority = Priority.MEDIUM
    pet_id: Optional[str] = None
    notes: Optional[str] = None

    def is_high_priority(self) -> bool:
        return self.priority == Priority.HIGH


@dataclass
class TimeSlot:
    start_time: datetime
    end_time: datetime
    task_id: Optional[str] = None
    status: str = "planned"  # "planned" | "completed" | "skipped"


@dataclass
class Schedule:
    date: date
    time_slots: List[TimeSlot] = field(default_factory=list)

    def generate(self) -> "Schedule":
        raise NotImplementedError()

    def explain(self) -> str:
        raise NotImplementedError()


@dataclass
class Pet:
    id: str = field(default_factory=_new_id)
    name: str = ""
    species: Optional[str] = None
    age: Optional[int] = None
    owner_id: Optional[str] = None


@dataclass
class Owner:
    id: str = field(default_factory=_new_id)
    name: str = ""
    contact_info: Optional[str] = None
    preferences: List[Preference] = field(default_factory=list)
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        raise NotImplementedError()

    def remove_pet(self, pet_id: str) -> None:
        raise NotImplementedError()


class Scheduler:
    def schedule_tasks(
        self,
        tasks: List[PetCareTask],
        preferences: Optional[List[Preference]] = None,
        constraints: Optional[List[Constraint]] = None,
    ) -> Schedule:
        raise NotImplementedError()

    def optimize_by_priority(self, tasks: List[PetCareTask]) -> List[PetCareTask]:
        raise NotImplementedError()
