from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta, time
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
    scheduled_time: Optional[datetime] = None
    frequency: Optional[str] = None  # free-form (e.g., "daily", "weekly")
    completed: bool = False

    def is_high_priority(self) -> bool:
        """Return True when this task has high priority."""
        return self.priority == Priority.HIGH

    def mark_completed(self) -> None:
        """Mark the task as completed."""
        self.completed = True

    def is_pending(self) -> bool:
        """Return True when the task has not been completed yet."""
        return not self.completed


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
    tasks: List[PetCareTask] = field(default_factory=list)

    def add_task(self, task: PetCareTask) -> None:
        """Attach a PetCareTask to this pet."""
        task.pet_id = self.id
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> None:
        """Remove a task from this pet by id."""
        self.tasks = [t for t in self.tasks if t.id != task_id]

    def get_tasks(self, include_completed: bool = False) -> List[PetCareTask]:
        """Return this pet's tasks; optionally include completed ones."""
        if include_completed:
            return list(self.tasks)
        return [t for t in self.tasks if not t.completed]


@dataclass
class Owner:
    id: str = field(default_factory=_new_id)
    name: str = ""
    contact_info: Optional[str] = None
    preferences: List[Preference] = field(default_factory=list)
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Add a Pet to this owner and set ownership."""
        pet.owner_id = self.id
        self.pets.append(pet)

    def remove_pet(self, pet_id: str) -> None:
        """Remove a Pet from this owner by id."""
        self.pets = [p for p in self.pets if p.id != pet_id]

    def get_all_pets(self) -> List[Pet]:
        """Return a list of this owner's pets."""
        return list(self.pets)

    def get_all_tasks(self, include_completed: bool = False) -> List[PetCareTask]:
        """Aggregate tasks from all pets owned by this owner."""
        tasks: List[PetCareTask] = []
        for p in self.pets:
            tasks.extend(p.get_tasks(include_completed=include_completed))
        return tasks


class Scheduler:
    def schedule_tasks(
        self,
        tasks: List[PetCareTask],
        preferences: Optional[List[Preference]] = None,
        constraints: Optional[List[Constraint]] = None,
    ) -> Schedule:
        """Produce a Schedule by greedily placing pending tasks into the day."""
        # Simple greedy scheduler that fills the day sequentially.
        # Default working window: 08:00 - 20:00
        if not tasks:
            return Schedule(date=date.today(), time_slots=[])

        # Filter pending tasks
        pending = [t for t in tasks if not t.completed]
        # Order by priority (HIGH first) then shorter duration first
        pending = self.optimize_by_priority(pending)

        day = date.today()
        start_dt = datetime.combine(day, time(hour=8, minute=0))
        end_dt = datetime.combine(day, time(hour=20, minute=0))

        slots: List[TimeSlot] = []
        cursor = start_dt

        for task in pending:
            needed = timedelta(minutes=task.duration_minutes)
            if cursor + needed > end_dt:
                # no room left in the day
                break
            slot = TimeSlot(start_time=cursor, end_time=cursor + needed, task_id=task.id)
            slots.append(slot)
            task.scheduled_time = cursor
            cursor = cursor + needed

        return Schedule(date=day, time_slots=slots)

    def optimize_by_priority(self, tasks: List[PetCareTask]) -> List[PetCareTask]:
        """Return tasks ordered by priority and duration (high/short first)."""
        # Sort by priority (HIGH first), then by duration (shorter first)
        priority_value = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}
        return sorted(tasks, key=lambda t: (priority_value.get(t.priority, 1), t.duration_minutes))

    def schedule_for_owner(
        self,
        owner: Owner,
        for_date: Optional[date] = None,
        preferences: Optional[List[Preference]] = None,
        constraints: Optional[List[Constraint]] = None,
    ) -> Schedule:
        """Gather tasks from an Owner and produce a Schedule for them."""
        # Gather tasks from owner and schedule them
        tasks = owner.get_all_tasks(include_completed=False)
        if for_date:
            # for now we ignore recurrence and date filtering
            pass
        return self.schedule_tasks(tasks, preferences=preferences, constraints=constraints)
