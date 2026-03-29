import streamlit as st
from pawpal_system import Owner, Pet, PetCareTask, Scheduler, Priority

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

st.subheader("Quick Demo Inputs (UI only)")
owner_name = st.text_input("Owner name", value="Jordan")
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["dog", "cat", "other"])

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

# Add pet UI
pet_col1, pet_col2 = st.columns(2)
with pet_col1:
    new_pet_name = st.text_input("New pet name", value="", key="new_pet_name")
with pet_col2:
    new_species = st.selectbox("New pet species", ["dog", "cat", "other"], key="new_species")

if st.button("Add pet"):
    if not new_pet_name:
        st.error("Enter a pet name first")
    else:
        p = Pet(name=new_pet_name, species=new_species)
        owner.add_pet(p)
        st.session_state.owner = owner
        st.success(f"Added pet {p.name}")

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
        st.write(f"- {p.name} ({p.species}) — {len(p.get_tasks())} pending tasks")
        for t in p.get_tasks():
            st.write(f"    • {t.title} ({t.duration_minutes}m) — Priority: {t.priority.name}")
else:
    st.info("No pets yet. Add one above.")

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
        # display schedule
        if not schedule.time_slots:
            st.info("No tasks scheduled for today.")
        else:
            st.write(f"### Today's Schedule ({schedule.date.isoformat()})")
            for slot in schedule.time_slots:
                start = slot.start_time.strftime("%H:%M")
                end = slot.end_time.strftime("%H:%M")
                # find task and pet
                task = None
                pet_name = "(unknown)"
                for p in owner.get_all_pets():
                    for t in p.get_tasks(include_completed=True):
                        if t.id == slot.task_id:
                            task = t
                            pet_name = p.name
                            break
                    if task:
                        break
                title = task.title if task else "(unknown task)"
                priority = task.priority.name if task else "-"
                st.write(f"- {start}-{end}: {title} [{pet_name}] (Priority: {priority})")
