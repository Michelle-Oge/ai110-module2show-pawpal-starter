from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Task:
    """Represents a single pet-care activity with a duration, priority, and completion state."""

    name: str
    duration: int
    priority: int
    category: str = "general"
    notes: str = ""
    completed: bool = False

    def is_valid(self) -> bool:
        """Return True if name is non-empty, duration is positive, and priority is 1–5."""
        if not self.name or not self.name.strip():
            return False
        if self.duration <= 0:
            return False
        if not (1 <= self.priority <= 5):
            return False
        return True

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def __repr__(self) -> str:
        """Return a concise string showing completion status, name, duration, and category."""
        status = "✓" if self.completed else "○"
        return (
            f"[{status}] {self.name} ({self.duration} min, "
            f"p{self.priority}, {self.category})"
        )


@dataclass
class Pet:
    """Stores pet profile information and owns the list of care tasks for that pet."""

    name: str
    species: str
    age: int
    notes: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Validate task and append it to this pet's task list, raising ValueError if invalid."""
        if not task.is_valid():
            raise ValueError(
                f"Invalid task {task!r}: check name, duration (>0), "
                "and priority (1–5)."
            )
        self.tasks.append(task)

    def remove_task(self, name: str) -> bool:
        """Remove the first task matching the given name; return True if found, False otherwise."""
        for i, t in enumerate(self.tasks):
            if t.name == name:
                self.tasks.pop(i)
                return True
        return False

    def get_pending_tasks(self) -> list[Task]:
        """Return only tasks that have not yet been marked complete."""
        return [t for t in self.tasks if not t.completed]

    def __repr__(self) -> str:
        """Return a concise string with the pet's name, species, and age."""
        return f"Pet({self.name!r}, {self.species}, age {self.age})"


@dataclass
class Owner:
    """Manages an owner's profile, time budget, and the collection of their pets."""

    name: str
    available_minutes: int
    preferences: dict[str, Any] = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a new pet with this owner."""
        self.pets.append(pet)

    def remove_pet(self, name: str) -> bool:
        """Remove the first pet matching the given name; return True if found, False otherwise."""
        for i, p in enumerate(self.pets):
            if p.name == name:
                self.pets.pop(i)
                return True
        return False

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Return every (pet, task) pair across all registered pets."""
        return [(pet, task) for pet in self.pets for task in pet.tasks]

    def get_all_pending_tasks(self) -> list[tuple[Pet, Task]]:
        """Return only (pet, task) pairs where the task is not yet completed."""
        return [
            (pet, task)
            for pet in self.pets
            for task in pet.get_pending_tasks()
        ]

    def __repr__(self) -> str:
        """Return a summary string with name, available minutes, and pet count."""
        return (
            f"Owner({self.name!r}, {self.available_minutes} min available, "
            f"{len(self.pets)} pet(s))"
        )


@dataclass
class Plan:
    """Holds the output of one scheduling run: scheduled tasks, skipped tasks, and total time used."""

    scheduled: list[tuple[Pet, Task]] = field(default_factory=list)
    skipped:   list[tuple[Pet, Task]] = field(default_factory=list)
    total_minutes: int = 0

    def summary(self) -> str:
        """Return a one-line string summarising how many tasks were scheduled vs skipped."""
        return (
            f"{len(self.scheduled)} task(s) scheduled "
            f"({self.total_minutes} min); "
            f"{len(self.skipped)} skipped due to time constraints."
        )

    def reasoning(self) -> str:
        """Return a multi-line explanation of which tasks were scheduled or skipped and why."""
        lines = [
            "Tasks were sorted by priority (highest first).",
            "Ties broken by shorter duration first.",
            "",
        ]
        if self.scheduled:
            lines.append("Scheduled:")
            for pet, task in self.scheduled:
                lines.append(
                    f"  ✓ [{pet.name}] {task.name} "
                    f"— priority {task.priority}, {task.duration} min"
                )
        if self.skipped:
            lines.append("\nSkipped (not enough time remaining):")
            for pet, task in self.skipped:
                lines.append(
                    f"  ✗ [{pet.name}] {task.name} "
                    f"— priority {task.priority}, {task.duration} min"
                )
        return "\n".join(lines)

    def to_dict(self) -> dict:
        """Serialise the plan to a plain dict suitable for JSON export or Streamlit display."""
        return {
            "scheduled": [
                {
                    "pet": pet.name,
                    "task": task.name,
                    "duration": task.duration,
                    "priority": task.priority,
                    "category": task.category,
                    "notes": task.notes,
                }
                for pet, task in self.scheduled
            ],
            "skipped": [
                {"pet": pet.name, "task": task.name,
                 "duration": task.duration, "priority": task.priority}
                for pet, task in self.skipped
            ],
            "total_minutes": self.total_minutes,
            "summary": self.summary(),
        }


class Scheduler:
    """Retrieves tasks from the Owner's pets, sorts them by priority, and produces a Plan."""

    def __init__(self, owner: Owner) -> None:
        """Initialise the scheduler with a reference to the Owner whose pets will be scheduled."""
        self.owner = owner

    def generate_plan(self) -> Plan:
        """Sort all pending tasks by priority (desc) then duration (asc) and greedily fit them into the owner's time budget."""
        budget = self.owner.available_minutes
        pending = self.owner.get_all_pending_tasks()

        sorted_pairs = sorted(
            pending,
            key=lambda pt: (-pt[1].priority, pt[1].duration),
        )

        scheduled: list[tuple[Pet, Task]] = []
        skipped:   list[tuple[Pet, Task]] = []
        used = 0

        for pet, task in sorted_pairs:
            if used + task.duration <= budget:
                scheduled.append((pet, task))
                used += task.duration
            else:
                skipped.append((pet, task))

        return Plan(scheduled=scheduled, skipped=skipped, total_minutes=used)

    def explain_plan(self, plan: Plan) -> str:
        """Return a formatted plain-English explanation of the given plan, including a header and reasoning."""
        header = (
            f"Plan for {self.owner.name} "
            f"({self.owner.available_minutes} min available today)\n"
            + "=" * 55
        )
        return f"{header}\n{plan.reasoning()}\n\n{plan.summary()}"

    def mark_task_complete(self, pet_name: str, task_name: str) -> bool:
        """Find the named task on the named pet and mark it complete; return True if found."""
        for pet in self.owner.pets:
            if pet.name == pet_name:
                for task in pet.tasks:
                    if task.name == task_name:
                        task.mark_complete()
                        return True
        return False

    def get_all_tasks_grouped(self) -> dict[str, list[Task]]:
        """Return a dict mapping each pet's name to its full task list."""
        return {pet.name: pet.tasks for pet in self.owner.pets}