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
    warnings: List[str] = field(default_factory=list)

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

    def complete_task(self, task_id: str) -> Optional[PetCareTask]:
        """Mark a task as completed. If the task is recurring ('daily' or 'weekly'),
        create and append the next occurrence and return it; otherwise return None.
        """
        for t in self.tasks:
            if t.id == task_id:
                t.mark_completed()
                freq = (t.frequency or "").lower()
                if freq in ("daily", "weekly"):
                    # compute next scheduled_time using timedelta
                    offset = timedelta(days=1) if freq == "daily" else timedelta(weeks=1)
                    if t.scheduled_time:
                        next_time = t.scheduled_time + offset
                    else:
                        next_time = datetime.now() + offset
                    new_task = PetCareTask(
                        title=t.title,
                        duration_minutes=t.duration_minutes,
                        priority=t.priority,
                        pet_id=self.id,
                        notes=t.notes,
                        frequency=t.frequency,
                        scheduled_time=next_time,
                    )
                    self.tasks.append(new_task)
                    return new_task
                return None
        return None


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
        """Produce a Schedule by placing tasks into the day.

        Behavior:
        - If a task has `scheduled_time`, the scheduler will place it at that time.
        - Otherwise tasks are placed greedily after the running cursor.
        After building slots, the scheduler runs conflict detection and returns warnings.
        """
        # Simple scheduler with support for user-provided scheduled_time
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
            if task.scheduled_time:
                # honor requested scheduled_time
                start = task.scheduled_time
                end = start + needed
                # drop tasks outside the scheduling window
                if start < start_dt or end > end_dt:
                    # skip tasks that don't fit in the window
                    continue
                slot = TimeSlot(start_time=start, end_time=end, task_id=task.id)
                slots.append(slot)
            else:
                if cursor + needed > end_dt:
                    # no room left in the day
                    break
                slot = TimeSlot(start_time=cursor, end_time=cursor + needed, task_id=task.id)
                slots.append(slot)
                task.scheduled_time = cursor
                cursor = cursor + needed

        schedule = Schedule(date=day, time_slots=slots)

        # build quick lookup of tasks by id for conflict messages
        tasks_by_id: Dict[str, PetCareTask] = {t.id: t for t in tasks}
        schedule.warnings = self.detect_conflicts(schedule.time_slots, tasks_by_id)
        return schedule

    def optimize_by_priority(self, tasks: List[PetCareTask]) -> List[PetCareTask]:
        """Return tasks ordered by priority and duration (high/short first)."""
        # Sort by priority (HIGH first), then by duration (shorter first)
        priority_value = {Priority.HIGH: 0, Priority.MEDIUM: 1, Priority.LOW: 2}
        return sorted(tasks, key=lambda t: (priority_value.get(t.priority, 1), t.duration_minutes))

    def sort_by_time(self, tasks: List[PetCareTask]) -> List[PetCareTask]:
        """Sort tasks by their scheduled_time (earliest first).

        Tasks without a `scheduled_time` are ordered last by treating their
        key as `datetime.max` so explicit times are prioritized.
        """
        def key_fn(t: PetCareTask):
            # Use scheduled_time (datetime) when present, otherwise a far-future datetime
            return t.scheduled_time if t.scheduled_time is not None else datetime.max

        return sorted(tasks, key=key_fn)

    def filter_tasks(self, owner: Owner, pet_name: Optional[str] = None, completed: Optional[bool] = None) -> List[PetCareTask]:
        """Return tasks optionally filtered by `pet_name` and/or completion status.

        Parameters
        - owner: Owner whose pets/tasks will be searched
        - pet_name: when provided, only tasks for that pet name are returned
        - completed: when True/False, filter by completion status; when None, include both

        Returns a list of matching `PetCareTask` objects.
        """
        results: List[PetCareTask] = []
        for p in owner.get_all_pets():
            if pet_name and p.name != pet_name:
                continue
            for t in p.get_tasks(include_completed=True):
                if completed is None or t.completed == completed:
                    results.append(t)
        return results

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

    def detect_conflicts(self, slots: List[TimeSlot], tasks_by_id: Dict[str, PetCareTask]) -> List[str]:
        """Lightweight conflict detection using pairwise interval checks.

        This function returns a list of human-readable warning strings for any
        overlapping `TimeSlot` pairs. It is intentionally simple (O(n^2)) for
        readability and because the expected number of daily tasks is small.
        """
        warnings: List[str] = []
        n = len(slots)
        for i in range(n):
            a = slots[i]
            for j in range(i + 1, n):
                b = slots[j]
                # overlap if a.start < b.end and b.start < a.end
                if a.start_time < b.end_time and b.start_time < a.end_time:
                    ta = tasks_by_id.get(a.task_id)
                    tb = tasks_by_id.get(b.task_id)
                    a_title = ta.title if ta else a.task_id
                    b_title = tb.title if tb else b.task_id
                    a_pet = ta.pet_id if ta else "?"
                    b_pet = tb.pet_id if tb else "?"
                    msg = f"Conflict: '{a_title}' (pet_id={a_pet}) overlaps with '{b_title}' (pet_id={b_pet})"
                    warnings.append(msg)
        # deduplicate
        unique = []
        for w in warnings:
            if w not in unique:
                unique.append(w)
        return unique
