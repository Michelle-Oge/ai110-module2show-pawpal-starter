from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Task:
    name: str
    duration: int                   # minutes
    priority: int                   # 1 (low) – 5 (high)
    category: str = "general"       # "walk", "feeding", "meds", "enrichment", …
    notes: str = ""
    completed: bool = False

    def is_valid(self) -> bool:
        
        if not self.name or not self.name.strip():
            return False
        if self.duration <= 0:
            return False
        if not (1 <= self.priority <= 5):
            return False
        return True

    def mark_complete(self) -> None:
        
        self.completed = True

    def __repr__(self) -> str:
        status = "✓" if self.completed else "○"
        return (
            f"[{status}] {self.name} ({self.duration} min, "
            f"p{self.priority}, {self.category})"
        )


@dataclass
class Pet:
    name: str
    species: str 
    age: int
    notes: str = ""
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        
        if not task.is_valid():
            raise ValueError(
                f"Invalid task {task!r}: check name, duration (>0), "
                "and priority (1–5)."
            )
        self.tasks.append(task)

    def remove_task(self, name: str) -> bool:
        
        for i, t in enumerate(self.tasks):
            if t.name == name:
                self.tasks.pop(i)
                return True
        return False

    def get_pending_tasks(self) -> list[Task]:
        """Return only tasks that are not yet completed."""
        return [t for t in self.tasks if not t.completed]

    def __repr__(self) -> str:
        return f"Pet({self.name!r}, {self.species}, age {self.age})"


@dataclass
class Owner:
    name: str
    available_minutes: int          # total free time today
    preferences: dict[str, Any] = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet with this owner."""
        self.pets.append(pet)

    def remove_pet(self, name: str) -> bool:
        
        for i, p in enumerate(self.pets):
            if p.name == name:
                self.pets.pop(i)
                return True
        return False

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        
        return [(pet, task) for pet in self.pets for task in pet.tasks]

    def get_all_pending_tasks(self) -> list[tuple[Pet, Task]]:
        
        return [
            (pet, task)
            for pet in self.pets
            for task in pet.get_pending_tasks()
        ]

    def __repr__(self) -> str:
        return (
            f"Owner({self.name!r}, {self.available_minutes} min available, "
            f"{len(self.pets)} pet(s))"
        )


@dataclass
class Plan:
    scheduled: list[tuple[Pet, Task]] = field(default_factory=list)
    skipped:   list[tuple[Pet, Task]] = field(default_factory=list)
    total_minutes: int = 0

    def summary(self) -> str:
        return (
            f"{len(self.scheduled)} task(s) scheduled "
            f"({self.total_minutes} min); "
            f"{len(self.skipped)} skipped due to time constraints."
        )

    def reasoning(self) -> str:
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

    def __init__(self, owner: Owner) -> None:
        self.owner = owner


    def generate_plan(self) -> Plan:
        """
        1. Ask the Owner for all pending (pet, task) pairs.
        2. Sort by priority desc, then duration asc (shorter wins ties).
        3. Greedily fit tasks into owner.available_minutes.
        4. Return a Plan with scheduled + skipped lists.
        """
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
        
        header = (
            f"Plan for {self.owner.name} "
            f"({self.owner.available_minutes} min available today)\n"
            + "=" * 55
        )
        return f"{header}\n{plan.reasoning()}\n\n{plan.summary()}"

    def mark_task_complete(self, pet_name: str, task_name: str) -> bool:
        
        for pet in self.owner.pets:
            if pet.name == pet_name:
                for task in pet.tasks:
                    if task.name == task_name:
                        task.mark_complete()
                        return True
        return False

    def get_all_tasks_grouped(self) -> dict[str, list[Task]]:
       
        return {pet.name: pet.tasks for pet in self.owner.pets}