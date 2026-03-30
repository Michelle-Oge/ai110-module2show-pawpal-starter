from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any


@dataclass
class Task:

    name: str
    duration: int                       # minutes
    priority: int                       # 1 (low) – 5 (high)
    category: str = "general"
    notes: str = ""
    completed: bool = False
    time_slot: str = ""                 # "HH:MM" – when the task is scheduled
    frequency: str = "once"            # "once" | "daily" | "weekly"
    due_date: date = field(default_factory=date.today)

    def is_valid(self) -> bool:
  
        if not self.name or not self.name.strip():
            return False
        if self.duration <= 0:
            return False
        if not (1 <= self.priority <= 5):
            return False
        return True

    def mark_complete(self) -> "Task | None":
       
        self.completed = True

        if self.frequency == "daily":
            return Task(
                name=self.name,
                duration=self.duration,
                priority=self.priority,
                category=self.category,
                notes=self.notes,
                time_slot=self.time_slot,
                frequency=self.frequency,
                due_date=self.due_date + timedelta(days=1),
            )
        if self.frequency == "weekly":
            return Task(
                name=self.name,
                duration=self.duration,
                priority=self.priority,
                category=self.category,
                notes=self.notes,
                time_slot=self.time_slot,
                frequency=self.frequency,
                due_date=self.due_date + timedelta(weeks=1),
            )
        return None     # "once" — no follow-up task needed

    def __repr__(self) -> str:
       
        status = "✓" if self.completed else "○"
        slot   = f" @{self.time_slot}" if self.time_slot else ""
        return (
            f"[{status}] {self.name}{slot} ({self.duration} min, "
            f"p{self.priority}, {self.frequency})"
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
       
        return [t for t in self.tasks if not t.completed]

    def __repr__(self) -> str:
        
        return f"Pet({self.name!r}, {self.species}, age {self.age})"



@dataclass
class Owner:

    name: str
    available_minutes: int
    preferences: dict[str, Any] = field(default_factory=dict)
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
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
                slot = f" @{task.time_slot}" if task.time_slot else ""
                lines.append(
                    f"  ✓ [{pet.name}] {task.name}{slot} "
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
                    "time_slot": task.time_slot,
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


    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        
        return sorted(
            tasks,
            key=lambda t: ("1", "") if not t.time_slot else ("0", t.time_slot),
        )


    def filter_tasks(
        self,
        *,
        completed: bool | None = None,
        pet_name: str | None = None,
    ) -> list[tuple[Pet, Task]]:
       
        results = self.owner.get_all_tasks()

        if completed is not None:
            results = [(p, t) for p, t in results if t.completed == completed]

        if pet_name is not None:
            results = [(p, t) for p, t in results
                       if p.name.lower() == pet_name.lower()]

        return results


    def mark_task_complete(self, pet_name: str, task_name: str) -> bool:
    
        for pet in self.owner.pets:
            if pet.name == pet_name:
                for task in pet.tasks:
                    if task.name == task_name:
                        next_task = task.mark_complete()   # may return a new Task
                        if next_task is not None:
                            pet.add_task(next_task)        # auto-schedule recurrence
                        return True
        return False

    # ── conflict detection ────────────────────────────────────────────────────

    def detect_conflicts(self) -> list[str]:
       
        warnings: list[str] = []
        all_tasks = self.owner.get_all_tasks()   # [(pet, task), ...]

        # Compare every pair once (i < j avoids double-reporting)
        for i in range(len(all_tasks)):
            for j in range(i + 1, len(all_tasks)):
                pet_a, task_a = all_tasks[i]
                pet_b, task_b = all_tasks[j]

                if (
                    task_a.time_slot
                    and task_b.time_slot
                    and task_a.time_slot == task_b.time_slot
                ):
                    warnings.append(
                        f"⚠ Conflict at {task_a.time_slot}: "
                        f"[{pet_a.name}] {task_a.name} "
                        f"vs [{pet_b.name}] {task_b.name}"
                    )

        return warnings


    def generate_plan(self) -> Plan:
        
        budget  = self.owner.available_minutes
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

    def get_all_tasks_grouped(self) -> dict[str, list[Task]]:
        
        return {pet.name: pet.tasks for pet in self.owner.pets}