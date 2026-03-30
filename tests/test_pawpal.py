from pawpal_system import Owner, Pet, Task, Scheduler


def make_task(name="Walk", duration=20, priority=3, category="walk"):
    return Task(name=name, duration=duration, priority=priority, category=category)

def make_pet(name="Biscuit", species="dog", age=3):
    return Pet(name=name, species=species, age=age)


def test_mark_complete_changes_status():
    
    task = make_task()
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True

def test_mark_complete_is_idempotent():
    
    task = make_task()
    task.mark_complete()
    task.mark_complete()
    assert task.completed is True

def test_completed_task_excluded_from_pending():
    
    pet = make_pet()
    task = make_task()
    pet.add_task(task)
    task.mark_complete()
    assert task not in pet.get_pending_tasks()


def test_add_task_increases_count():
    
    pet = make_pet()
    before = len(pet.tasks)
    pet.add_task(make_task())
    assert len(pet.tasks) == before + 1

def test_add_multiple_tasks_increases_count():
    
    pet = make_pet()
    for i in range(3):
        pet.add_task(make_task(name=f"Task {i}"))
    assert len(pet.tasks) == 3

def test_add_invalid_task_raises():
    
    pet = make_pet()
    bad_task = Task(name="", duration=10, priority=3)
    try:
        pet.add_task(bad_task)
        assert False, "Expected ValueError was not raised"
    except ValueError:
        pass


# ── Scheduler integration ─────────────────────────────────────────────────────

def test_scheduler_sees_tasks_from_all_pets():
    
    owner = Owner(name="Alex", available_minutes=120)
    dog = make_pet("Biscuit", "dog")
    cat = make_pet("Mochi", "cat")
    dog.add_task(make_task("Walk", 30, 4))
    cat.add_task(make_task("Feed", 5, 5))
    owner.add_pet(dog)
    owner.add_pet(cat)

    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan()
    scheduled_names = [t.name for _, t in plan.scheduled]
    assert "Walk" in scheduled_names
    assert "Feed" in scheduled_names

def test_scheduler_skips_completed_tasks():
    
    owner = Owner(name="Alex", available_minutes=60)
    pet = make_pet()
    done = make_task("Already done", 10, 5)
    done.mark_complete()
    pet.add_task(done)
    owner.add_pet(pet)

    scheduler = Scheduler(owner)
    plan = scheduler.generate_plan()
    scheduled_names = [t.name for _, t in plan.scheduled]
    assert "Already done" not in scheduled_names