from datetime import date, timedelta
import pytest
from pawpal_system import Owner, Pet, Task, Scheduler


@pytest.fixture
def basic_owner():
    return Owner(name="Alex", available_minutes=90)

@pytest.fixture
def biscuit():
    return Pet(name="Biscuit", species="dog", age=4)

@pytest.fixture
def mochi():
    return Pet(name="Mochi", species="cat", age=2)

@pytest.fixture
def scheduler_with_pets(basic_owner, biscuit, mochi):
    basic_owner.add_pet(biscuit)
    basic_owner.add_pet(mochi)
    return Scheduler(basic_owner)



class TestTaskValidation:
    def test_valid_task(self):
        assert Task("Walk", 30, 4).is_valid()

    def test_empty_name_invalid(self):
        assert not Task("", 10, 3).is_valid()

    def test_whitespace_name_invalid(self):
        assert not Task("   ", 10, 3).is_valid()

    def test_zero_duration_invalid(self):
        assert not Task("Feed", 0, 3).is_valid()

    def test_negative_duration_invalid(self):
        assert not Task("Feed", -5, 3).is_valid()

    def test_priority_too_low(self):
        assert not Task("Groom", 20, 0).is_valid()

    def test_priority_too_high(self):
        assert not Task("Groom", 20, 6).is_valid()

    def test_priority_boundaries(self):
        assert Task("Play", 15, 1).is_valid()
        assert Task("Meds", 5, 5).is_valid()


class TestRecurrence:
    def test_mark_complete_sets_flag(self):
        
        t = Task("Walk", 30, 4)
        t.mark_complete()
        assert t.completed is True

    def test_once_task_returns_none(self):
        
        t = Task("Walk", 30, 4, frequency="once")
        result = t.mark_complete()
        assert result is None

    def test_daily_task_creates_next_occurrence(self):
        
        t = Task("Walk", 30, 4, frequency="daily",
                 due_date=date(2025, 6, 1))
        next_t = t.mark_complete()
        assert next_t is not None

    def test_daily_task_due_date_is_tomorrow(self):
        
        today = date(2025, 6, 1)
        t = Task("Walk", 30, 4, frequency="daily", due_date=today)
        next_t = t.mark_complete()
        assert next_t.due_date == today + timedelta(days=1)

    def test_weekly_task_due_date_is_next_week(self):
        
        today = date(2025, 6, 1)
        t = Task("Bath", 20, 3, frequency="weekly", due_date=today)
        next_t = t.mark_complete()
        assert next_t.due_date == today + timedelta(weeks=1)

    def test_recurrence_preserves_task_attributes(self):
        
        t = Task("Meds", 5, 5, category="meds", frequency="daily",
                 due_date=date(2025, 6, 1))
        next_t = t.mark_complete()
        assert next_t.name     == t.name
        assert next_t.duration == t.duration
        assert next_t.priority == t.priority
        assert next_t.category == t.category

    def test_recurrence_new_task_not_completed(self):
        
        t = Task("Walk", 30, 4, frequency="daily",
                 due_date=date(2025, 6, 1))
        next_t = t.mark_complete()
        assert next_t.completed is False

    def test_scheduler_adds_recurrence_to_pet(self, scheduler_with_pets, biscuit):
        
        task = Task("Morning walk", 30, 4, frequency="daily",
                    due_date=date.today())
        biscuit.add_task(task)
        count_before = len(biscuit.tasks)
        scheduler_with_pets.mark_task_complete("Biscuit", "Morning walk")
        assert len(biscuit.tasks) == count_before + 1

    def test_scheduler_once_task_no_new_occurrence(self, scheduler_with_pets, biscuit):
        
        task = Task("Vet visit", 60, 5, frequency="once")
        biscuit.add_task(task)
        count_before = len(biscuit.tasks)
        scheduler_with_pets.mark_task_complete("Biscuit", "Vet visit")
        assert len(biscuit.tasks) == count_before



class TestSorting:
    def test_tasks_returned_in_chronological_order(self, scheduler_with_pets):
        
        tasks = [
            Task("Dinner",   20, 3, time_slot="18:00"),
            Task("Meds",      5, 5, time_slot="08:00"),
            Task("Lunch",    10, 3, time_slot="12:30"),
            Task("Breakfast", 5, 5, time_slot="07:00"),
        ]
        result = scheduler_with_pets.sort_by_time(tasks)
        slots  = [t.time_slot for t in result]
        assert slots == ["07:00", "08:00", "12:30", "18:00"]

    def test_tasks_without_slot_sorted_last(self, scheduler_with_pets):
        
        tasks = [
            Task("No slot task", 15, 3),
            Task("Early task",   10, 4, time_slot="06:00"),
        ]
        result = scheduler_with_pets.sort_by_time(tasks)
        assert result[0].time_slot == "06:00"
        assert result[1].time_slot == ""

    def test_empty_list_returns_empty(self, scheduler_with_pets):
       
        assert scheduler_with_pets.sort_by_time([]) == []

    def test_single_task_unchanged(self, scheduler_with_pets):
        
        tasks  = [Task("Solo", 10, 3, time_slot="09:00")]
        result = scheduler_with_pets.sort_by_time(tasks)
        assert result[0].name == "Solo"



class TestConflictDetection:
    def test_duplicate_slot_flagged(self, scheduler_with_pets, biscuit, mochi):
        
        biscuit.add_task(Task("Meds",      5, 5, time_slot="08:00"))
        mochi.add_task(  Task("Breakfast", 5, 5, time_slot="08:00"))
        warnings = scheduler_with_pets.detect_conflicts()
        assert len(warnings) == 1
        assert "08:00" in warnings[0]

    def test_no_conflict_when_slots_differ(self, scheduler_with_pets, biscuit, mochi):
        
        biscuit.add_task(Task("Walk",      30, 4, time_slot="07:00"))
        mochi.add_task(  Task("Breakfast",  5, 5, time_slot="08:00"))
        assert scheduler_with_pets.detect_conflicts() == []

    def test_no_conflict_when_no_slots_set(self, scheduler_with_pets, biscuit):
        
        biscuit.add_task(Task("Task A", 10, 3))
        biscuit.add_task(Task("Task B", 10, 3))
        assert scheduler_with_pets.detect_conflicts() == []

    def test_multiple_conflicts_all_reported(self, scheduler_with_pets, biscuit, mochi):
        
        biscuit.add_task(Task("Task A", 10, 3, time_slot="09:00"))
        biscuit.add_task(Task("Task B", 10, 3, time_slot="11:00"))
        mochi.add_task(  Task("Task C", 10, 3, time_slot="09:00"))
        mochi.add_task(  Task("Task D", 10, 3, time_slot="11:00"))
        warnings = scheduler_with_pets.detect_conflicts()
        assert len(warnings) == 2

    def test_conflict_warning_contains_pet_and_task_names(
        self, scheduler_with_pets, biscuit, mochi
    ):
        
        biscuit.add_task(Task("Meds",      5, 5, time_slot="08:00"))
        mochi.add_task(  Task("Breakfast", 5, 5, time_slot="08:00"))
        warning = scheduler_with_pets.detect_conflicts()[0]
        assert "Biscuit"   in warning
        assert "Mochi"     in warning
        assert "Meds"      in warning
        assert "Breakfast" in warning



class TestFiltering:
    def test_filter_pending_only(self, scheduler_with_pets, biscuit):
        
        t1 = Task("Walk", 30, 4)
        t2 = Task("Feed",  5, 5)
        t2.mark_complete()
        biscuit.add_task(t1)
        biscuit.add_task(t2)
        results = scheduler_with_pets.filter_tasks(completed=False)
        assert all(not t.completed for _, t in results)

    def test_filter_completed_only(self, scheduler_with_pets, biscuit):
        
        t1 = Task("Walk", 30, 4)
        t2 = Task("Feed",  5, 5)
        t2.mark_complete()
        biscuit.add_task(t1)
        biscuit.add_task(t2)
        results = scheduler_with_pets.filter_tasks(completed=True)
        assert all(t.completed for _, t in results)

    def test_filter_by_pet_name(self, scheduler_with_pets, biscuit, mochi):
        
        biscuit.add_task(Task("Walk",      30, 4))
        mochi.add_task(  Task("Playtime",  20, 3))
        results = scheduler_with_pets.filter_tasks(pet_name="Mochi")
        assert all(p.name == "Mochi" for p, _ in results)

    def test_filter_pet_name_case_insensitive(self, scheduler_with_pets, biscuit):
        
        biscuit.add_task(Task("Walk", 30, 4))
        assert scheduler_with_pets.filter_tasks(pet_name="biscuit") != []

    def test_filter_no_criteria_returns_all(self, scheduler_with_pets, biscuit, mochi):
        
        biscuit.add_task(Task("Walk",     30, 4))
        mochi.add_task(  Task("Playtime", 20, 3))
        assert len(scheduler_with_pets.filter_tasks()) == 2



class TestGeneratePlan:
    def test_high_priority_scheduled_first(self, scheduler_with_pets, biscuit):
        
        biscuit.add_task(Task("Low",  10, 1))
        biscuit.add_task(Task("High",  5, 5))
        plan = scheduler_with_pets.generate_plan()
        assert plan.scheduled[0][1].name == "High"

    def test_task_skipped_when_over_budget(self, basic_owner, biscuit):
        
        basic_owner.available_minutes = 20
        basic_owner.add_pet(biscuit)
        biscuit.add_task(Task("Long task", 60, 3))
        plan = Scheduler(basic_owner).generate_plan()
        assert len(plan.skipped) == 1

    def test_completed_tasks_excluded_from_plan(
        self, scheduler_with_pets, biscuit
    ):
        
        t = Task("Done", 10, 5)
        t.mark_complete()
        biscuit.add_task(t)
        plan = scheduler_with_pets.generate_plan()
        scheduled_names = [t.name for _, t in plan.scheduled]
        assert "Done" not in scheduled_names

    def test_total_minutes_matches_scheduled(self, scheduler_with_pets, biscuit):
        
        biscuit.add_task(Task("A", 15, 3))
        biscuit.add_task(Task("B", 20, 4))
        plan = scheduler_with_pets.generate_plan()
        assert plan.total_minutes == sum(t.duration for _, t in plan.scheduled)