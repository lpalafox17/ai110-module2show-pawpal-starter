import streamlit as st
from pawpal_system import Owner, Pet, PetCareTask, Scheduler, Priority

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")


with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )



st.divider()

st.subheader("Quick Demo Inputs (UI only)")

# Move owner + pet creation to the sidebar for a cleaner main UI
with st.sidebar:
    st.header("Owner & Pets")
    owner_name = st.text_input("Owner name", value="Jordan")
    new_pet_name = st.text_input("New pet name", value="Mochi", key="sidebar_pet_name")
    new_species = st.selectbox("Species", ["dog", "cat", "other"], key="sidebar_species")
    if st.button("Create/Update owner (sidebar)"):
        if "owner" not in st.session_state:
            st.session_state.owner = Owner(name=owner_name)
        st.session_state.owner.name = owner_name
        st.success(f"Owner set to {owner_name}")
    if st.button("Add pet (sidebar)"):
        if not new_pet_name:
            st.error("Enter a pet name first")
        else:
            p = Pet(name=new_pet_name, species=new_species)
            if "owner" not in st.session_state:
                st.session_state.owner = Owner(name=owner_name)
            st.session_state.owner.add_pet(p)
            st.success(f"Added pet {p.name}")

st.markdown("### Tasks")
st.caption("Add a few tasks. In your final version, these should feed into your scheduler.")

if "tasks" not in st.session_state:
    st.session_state.tasks = []

# Ensure an Owner object persists in session_state
if "owner" not in st.session_state:
    st.session_state.owner = Owner(name=owner_name)

owner = st.session_state.owner

if st.button("Create/Update owner"):
    owner.name = owner_name
    st.session_state.owner = owner
    st.success(f"Owner set to {owner.name}")

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
with col3:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

# (pet creation moved to the sidebar)

# Select which pet to add tasks to
pet_names = [p.name for p in owner.get_all_pets()]
selected_pet = None
if pet_names:
    sel = st.selectbox("Assign task to pet", options=pet_names)
    # find pet object
    for p in owner.get_all_pets():
        if p.name == sel:
            selected_pet = p

if st.button("Add task to selected pet"):
    if selected_pet is None:
        st.error("Create or select a pet first")
    else:
        task = PetCareTask(title=task_title, duration_minutes=int(duration), priority=Priority[priority.upper()])
        selected_pet.add_task(task)
        st.session_state.owner = owner
        st.success(f"Added task '{task.title}' to {selected_pet.name}")

st.markdown("### Current pets and tasks")
if owner.get_all_pets():
    for p in owner.get_all_pets():
        st.subheader(f"{p.name} ({p.species}) — {len(p.get_tasks())} pending tasks")
        # Show tasks in columns with an action button per task
        for t in p.get_tasks(include_completed=True):
            cols = st.columns([3, 1, 1, 1, 1])
            cols[0].write(f"**{t.title}** — {t.duration_minutes}m")
            cols[1].write(t.priority.name)
            cols[2].write(t.scheduled_time.strftime("%H:%M") if t.scheduled_time else "(unscheduled)")
            cols[3].write("✅" if t.completed else "")
            # complete button
            if cols[4].button("Complete", key=f"complete_{t.id}"):
                new_task = p.complete_task(t.id)
                st.session_state.owner = owner
                st.success(f"Marked '{t.title}' complete for {p.name}.")
                if new_task:
                    st.info(f"Created next occurrence for '{new_task.title}' at {new_task.scheduled_time}.")
else:
    st.info("No pets yet. Add one in the sidebar.")

st.divider()

st.subheader("Build Schedule")
st.caption("This button should call your scheduling logic once you implement it.")

if st.button("Generate schedule"):
    if not owner.get_all_pets():
        st.error("Add at least one pet before generating a schedule")
    else:
        sched = Scheduler()
        schedule = sched.schedule_for_owner(owner)
        st.session_state.schedule = schedule

        # helper maps
        all_tasks = owner.get_all_tasks(include_completed=True)
        tasks_by_id = {t.id: t for t in all_tasks}
        pets_by_id = {p.id: p for p in owner.get_all_pets()}

        # display any scheduler warnings prominently
        if getattr(schedule, "warnings", None):
            st.warning("Conflicts detected in schedule:")
            for w in schedule.warnings:
                st.warning(w)

        # display schedule as a table for readability
        if not schedule.time_slots:
            st.info("No tasks scheduled for today.")
        else:
            st.write(f"### Today's Schedule ({schedule.date.isoformat()})")
            rows = []
            for slot in schedule.time_slots:
                start = slot.start_time.strftime("%H:%M")
                end = slot.end_time.strftime("%H:%M")
                task = tasks_by_id.get(slot.task_id)
                pet = pets_by_id.get(task.pet_id) if task and task.pet_id else None
                rows.append(
                    {
                        "start": start,
                        "end": end,
                        "task": task.title if task else "(unknown)",
                        "pet": pet.name if pet else "(unknown)",
                        "priority": task.priority.name if task else "-",
                    }
                )
            st.table(rows)

        # show sorted tasks (by scheduled_time) and allow filtering by pet/completed
        st.markdown("### All tasks (sorted)")
        filter_pet = st.selectbox("Filter by pet", options=["(all)"] + [p.name for p in owner.get_all_pets()])
        filter_completed = st.selectbox("Completion", options=["all", "pending", "completed"]) 

        sorted_tasks = sched.sort_by_time(all_tasks)
        display_rows = []
        for t in sorted_tasks:
            pet = pets_by_id.get(t.pet_id) if t.pet_id else None
            if filter_pet != "(all)" and (not pet or pet.name != filter_pet):
                continue
            if filter_completed == "pending" and t.completed:
                continue
            if filter_completed == "completed" and not t.completed:
                continue
            display_rows.append(
                {
                    "time": t.scheduled_time.strftime("%H:%M") if t.scheduled_time else "(unscheduled)",
                    "task": t.title,
                    "pet": pet.name if pet else "(unknown)",
                    "priority": t.priority.name,
                    "duration_min": t.duration_minutes,
                }
            )

        if display_rows:
            st.table(display_rows)
        else:
            st.info("No tasks match the selected filters.")
