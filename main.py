from pawpal_system import Owner, Pet, Task, Scheduler


owner = Owner(name="Alex", available_minutes=90)

biscuit = Pet(name="Biscuit", species="dog", age=4)
mochi   = Pet(name="Mochi",   species="cat", age=2)

biscuit.add_task(Task("Evening walk",  30, 3, time_slot="18:00", frequency="daily"))
biscuit.add_task(Task("Flea meds",      5, 5, time_slot="08:00", frequency="weekly"))
biscuit.add_task(Task("Morning walk",  30, 4, time_slot="07:30", frequency="daily"))
biscuit.add_task(Task("Agility",       40, 2, time_slot="10:00"))

mochi.add_task(Task("Breakfast",        5, 5, time_slot="08:00", frequency="daily"))
mochi.add_task(Task("Playtime",        20, 3, time_slot="15:00"))
mochi.add_task(Task("Brush coat",      15, 2, time_slot="17:00"))

owner.add_pet(biscuit)
owner.add_pet(mochi)

scheduler = Scheduler(owner)


print("\n" + "=" * 55)
print("  1. TASKS SORTED BY TIME SLOT (Biscuit)")
print("=" * 55)
sorted_tasks = scheduler.sort_by_time(biscuit.tasks)
for t in sorted_tasks:
    slot = t.time_slot or "(no slot)"
    print(f"  {slot}  {t.name:<22} {t.duration} min  p{t.priority}")


print("\n" + "=" * 55)
print("  2. FILTERING — pending tasks for Mochi only")
print("=" * 55)
mochi_pending = scheduler.filter_tasks(completed=False, pet_name="Mochi")
for pet, task in mochi_pending:
    print(f"  [{pet.name}] {task}")


print("\n" + "=" * 55)
print("  3. CONFLICT DETECTION")
print("=" * 55)
conflicts = scheduler.detect_conflicts()
if conflicts:
    for warning in conflicts:
        print(f"  {warning}")
else:
    print("  No conflicts found.")


print("\n" + "=" * 55)
print("  4. RECURRING TASK — mark Biscuit's Morning walk complete")
print("=" * 55)
print(f"  Before: {len(biscuit.tasks)} task(s) on Biscuit")
scheduler.mark_task_complete("Biscuit", "Morning walk")
print(f"  After : {len(biscuit.tasks)} task(s) on Biscuit  (new occurrence added)")

new_task = next(
    t for t in biscuit.tasks
    if t.name == "Morning walk" and not t.completed
)
print(f"  Next occurrence due: {new_task.due_date}")


print("\n" + "=" * 55)
print("  5. TODAY'S SCHEDULE")
print("=" * 55)
plan = scheduler.generate_plan()
print(f"\n{scheduler.explain_plan(plan)}\n")