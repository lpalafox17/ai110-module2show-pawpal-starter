from datetime import datetime, timedelta

from pawpal_system import PetCareTask, Pet, Owner, Scheduler, Priority


def test_task_completion():
    t = PetCareTask(title="Test Task", duration_minutes=5)
    assert not t.completed
    t.mark_completed()
    assert t.completed


def test_task_addition():
    p = Pet(name="TestPet")
    initial = len(p.get_tasks())
    t = PetCareTask(title="Feed", duration_minutes=5)
    p.add_task(t)
    assert len(p.get_tasks()) == initial + 1
    # ensure the task is the one we added
    assert any(task.title == "Feed" for task in p.get_tasks())


def test_sorting_correctness():
    """Tasks with scheduled_time should be returned in chronological order."""
    owner = Owner(name="Tester")
    pet = Pet(name="Buddy")
    owner.add_pet(pet)

    # create tasks out of order
    t1 = PetCareTask(title="T1", duration_minutes=10)
    t2 = PetCareTask(title="T2", duration_minutes=10)
    t3 = PetCareTask(title="T3", duration_minutes=10)

    today = datetime.today()
    t1.scheduled_time = datetime.combine(today.date(), datetime.strptime("09:00", "%H:%M").time())
    t2.scheduled_time = datetime.combine(today.date(), datetime.strptime("08:30", "%H:%M").time())
    t3.scheduled_time = datetime.combine(today.date(), datetime.strptime("08:45", "%H:%M").time())

    pet.add_task(t1)
    pet.add_task(t2)
    pet.add_task(t3)

    sched = Scheduler()
    sorted_tasks = sched.sort_by_time(owner.get_all_tasks(include_completed=True))
    times = [t.scheduled_time for t in sorted_tasks]
    assert times == sorted(times)


def test_recurring_task_generation():
    """Completing a daily task creates the next day's occurrence."""
    pet = Pet(name="Coco")
    t = PetCareTask(title="Daily Walk", duration_minutes=15, frequency="daily")
    today = datetime.today()
    t.scheduled_time = datetime.combine(today.date(), datetime.strptime("08:00", "%H:%M").time())
    pet.add_task(t)

    # complete the task
    new_task = pet.complete_task(t.id)

    # original task marked completed
    assert any(task.id == t.id and task.completed for task in pet.get_tasks(include_completed=True))
    # new recurring instance created
    assert new_task is not None
    assert new_task.frequency == "daily"
    assert new_task.scheduled_time.date() == (t.scheduled_time.date() + timedelta(days=1))


def test_conflict_detection_flags_duplicates():
    """Scheduler should flag tasks with duplicate times as conflicts."""
    owner = Owner(name="ConflictOwner")
    p1 = Pet(name="A")
    p2 = Pet(name="B")
    owner.add_pet(p1)
    owner.add_pet(p2)

    t1 = PetCareTask(title="TaskA", duration_minutes=30)
    t2 = PetCareTask(title="TaskB", duration_minutes=20)
    today = datetime.today()
    scheduled = datetime.combine(today.date(), datetime.strptime("09:00", "%H:%M").time())
    t1.scheduled_time = scheduled
    t2.scheduled_time = scheduled

    p1.add_task(t1)
    p2.add_task(t2)

    sched = Scheduler()
    schedule = sched.schedule_for_owner(owner)

    assert schedule.warnings, "Expected conflict warnings but found none"
    # ensure warning mentions both task titles
    combined = " ".join(schedule.warnings)
    assert "TaskA" in combined and "TaskB" in combined
