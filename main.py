from pawpal_system import Owner, Pet, Task, Scheduler


owner = Owner(name="Alex", available_minutes=75)


biscuit = Pet(name="Biscuit", species="dog", age=4)
mochi   = Pet(name="Mochi",   species="cat", age=2, notes="indoor only")


biscuit.add_task(Task(
    name="Morning walk",
    duration=30,
    priority=4,
    category="walk",
))
biscuit.add_task(Task(
    name="Breakfast",
    duration=10,
    priority=5,
    category="feeding",
))
biscuit.add_task(Task(
    name="Flea treatment",
    duration=5,
    priority=5,
    category="meds",
    notes="apply between shoulder blades",
))
biscuit.add_task(Task(
    name="Agility practice",
    duration=40,
    priority=2,
    category="enrichment",
))


mochi.add_task(Task(
    name="Breakfast",
    duration=5,
    priority=5,
    category="feeding",
))
mochi.add_task(Task(
    name="Playtime",
    duration=20,
    priority=3,
    category="enrichment",
    notes="feather wand preferred",
))
mochi.add_task(Task(
    name="Brush coat",
    duration=15,
    priority=2,
    category="grooming",
))


owner.add_pet(biscuit)
owner.add_pet(mochi)


scheduler = Scheduler(owner=owner)
plan      = scheduler.generate_plan()


print("\n" + "=" * 55)
print("       🐾  PawPal+  —  Today's Schedule")
print("=" * 55)
print(f"Owner : {owner.name}")
print(f"Pets  : {', '.join(p.name for p in owner.pets)}")
print(f"Budget: {owner.available_minutes} minutes available")
print("=" * 55)

if plan.scheduled:
    print("\n✅  SCHEDULED TASKS")
    print("-" * 55)
    for i, (pet, task) in enumerate(plan.scheduled, start=1):
        stars = "★" * task.priority + "☆" * (5 - task.priority)
        print(f"  {i}. [{pet.name:8}]  {task.name:<22} {task.duration:>3} min  {stars}")
        if task.notes:
            print(f"            note: {task.notes}")

print(f"\n  Total time scheduled: {plan.total_minutes} / {owner.available_minutes} min")

if plan.skipped:
    print("\n⏭  SKIPPED  (not enough time remaining)")
    print("-" * 55)
    for pet, task in plan.skipped:
        print(
            f"  - [{pet.name}] {task.name} "
            f"({task.duration} min, priority {task.priority})"
        )

print("\n💡  REASONING")
print("-" * 55)
print(plan.reasoning())
print("=" * 55 + "\n")