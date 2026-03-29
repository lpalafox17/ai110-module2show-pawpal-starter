from datetime import datetime
from pawpal_system import Owner, Pet, PetCareTask, Priority, Scheduler


def format_schedule(schedule, tasks_by_id, pets_by_id):
    if not schedule.time_slots:
        print("No tasks scheduled for today.")
        return

    print(f"Today's Schedule ({schedule.date.isoformat()}):")
    for slot in schedule.time_slots:
        start = slot.start_time.strftime("%H:%M")
        end = slot.end_time.strftime("%H:%M")
        task = tasks_by_id.get(slot.task_id)
        pet = pets_by_id.get(task.pet_id) if task else None
        title = task.title if task else "(unknown task)"
        pet_name = pet.name if pet else "(unknown pet)"
        priority = task.priority.name if task else "-"
        print(f" - {start}-{end}: {title} [{pet_name}] (Priority: {priority})")

    # show unscheduled tasks
    scheduled_ids = {s.task_id for s in schedule.time_slots}
    unscheduled = [t for t in tasks_by_id.values() if t.id not in scheduled_ids and not t.completed]
    if unscheduled:
        print("\nUnscheduled tasks:")
        for t in unscheduled:
            pet = pets_by_id.get(t.pet_id)
            pet_name = pet.name if pet else "(unknown pet)"
            print(f" - {t.title} [{pet_name}] ({t.duration_minutes}m, Priority: {t.priority.name})")


if __name__ == '__main__':
    # create owner
    owner = Owner(name="Alex")

    # create pets
    dog = Pet(name="Buddy", species="Dog", age=4)
    cat = Pet(name="Mittens", species="Cat", age=2)
    owner.add_pet(dog)
    owner.add_pet(cat)

    # create tasks
    t1 = PetCareTask(title="Morning Walk", duration_minutes=30, priority=Priority.HIGH)
    t2 = PetCareTask(title="Feed Breakfast", duration_minutes=10, priority=Priority.MEDIUM)
    t3 = PetCareTask(title="Play Session", duration_minutes=20, priority=Priority.LOW)

    # assign tasks to pets (add out-of-order times)
    # set scheduled_time values so tasks are intentionally out-of-order
    t1.scheduled_time = datetime.combine(datetime.today(), datetime.strptime("09:00", "%H:%M").time())
    t2.scheduled_time = datetime.combine(datetime.today(), datetime.strptime("08:30", "%H:%M").time())
    # Make t3 conflict with t1 by scheduling it at the same time as t1
    t3.scheduled_time = datetime.combine(datetime.today(), datetime.strptime("09:00", "%H:%M").time())

    dog.add_task(t1)
    dog.add_task(t2)
    cat.add_task(t3)

    # collect helper maps
    tasks = owner.get_all_tasks()
    tasks_by_id = {t.id: t for t in tasks}
    pets_by_id = {p.id: p for p in owner.get_all_pets()}

    # schedule
    sched = Scheduler()
    schedule = sched.schedule_for_owner(owner)

    # print schedule (greedy result)
    format_schedule(schedule, tasks_by_id, pets_by_id)

    # print any warnings produced by the scheduler
    if getattr(schedule, 'warnings', None):
        print("\nScheduler warnings:")
        for w in schedule.warnings:
            print(" -", w)

    # Demonstrate sorting by scheduled_time using Scheduler.sort_by_time
    print("\nTasks sorted by scheduled_time:")
    all_tasks = owner.get_all_tasks(include_completed=True)
    sorted_tasks = sched.sort_by_time(all_tasks)
    for t in sorted_tasks:
        stime = t.scheduled_time.strftime("%H:%M") if t.scheduled_time else "(no time)"
        pet = pets_by_id.get(t.pet_id)
        pet_name = pet.name if pet else "(unknown)"
        print(f" - {stime}: {t.title} [{pet_name}]")

    # Demonstrate filtering: only tasks for Buddy
    print("\nFiltered tasks (pet=Buddy):")
    filtered = sched.filter_tasks(owner, pet_name="Buddy", completed=False)
    for t in filtered:
        stime = t.scheduled_time.strftime("%H:%M") if t.scheduled_time else "(no time)"
        print(f" - {stime}: {t.title} [Buddy]")
