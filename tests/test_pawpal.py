from pawpal_system import PetCareTask, Pet


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
