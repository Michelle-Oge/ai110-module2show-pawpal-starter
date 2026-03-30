import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler


st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")


if "owner" not in st.session_state:
    st.session_state.owner = None   # created the first time the form is saved


owner_name = st.text_input("Owner name", value="Jordan")
pet_name   = st.text_input("Pet name",   value="Mochi")
species    = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Save owner & pet"):
    pet   = Pet(name=pet_name.strip(), species=species, age=0)
    owner = Owner(name=owner_name.strip(), available_minutes=60)
    owner.add_pet(pet)
    st.session_state.owner = owner
    st.success(f"Saved {owner_name} with pet {pet_name}.")
    st.rerun()


if st.session_state.owner:
    st.session_state.owner.available_minutes = st.number_input(
        "Available minutes today",
        min_value=1, max_value=720,
        value=st.session_state.owner.available_minutes,
        step=5,
    )

st.divider()


st.markdown("### Tasks")
st.caption("Add tasks below. These feed directly into your scheduler.")

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    duration = st.number_input("Duration (minutes)", min_value=1,
                                max_value=240, value=20)
with col3:
    priority_label = st.selectbox("Priority", ["low", "medium", "high"], index=2)

PRIORITY_MAP = {"low": 1, "medium": 3, "high": 5}

if st.button("Add task"):
    if st.session_state.owner is None:
        st.warning("Save an owner & pet first.")
    else:
        pet  = st.session_state.owner.pets[0]   # single-pet mode (starter style)
        task = Task(
            name=task_title.strip(),
            duration=int(duration),
            priority=PRIORITY_MAP[priority_label],
            category="general",
        )
        try:
            pet.add_task(task)                   # calls Pet.add_task() → validates
            st.rerun()
        except ValueError as e:
            st.error(str(e))


if st.session_state.owner and st.session_state.owner.pets:
    pet = st.session_state.owner.pets[0]
    if pet.tasks:
        st.write("Current tasks:")
        # Build a plain list-of-dicts so st.table works just like the starter
        st.table([
            {
                "title":            t.name,
                "duration_minutes": t.duration,
                "priority":         t.priority,
                "completed":        t.completed,
            }
            for t in pet.tasks
        ])
    else:
        st.info("No tasks yet. Add one above.")
else:
    st.info("No tasks yet. Add one above.")

st.divider()


st.subheader("Build Schedule")
st.caption("Calls your Scheduler and displays the plan.")

if st.button("Generate schedule"):
    if st.session_state.owner is None:
        st.warning("Save an owner & pet first.")
    elif not st.session_state.owner.get_all_pending_tasks():
        st.warning("Add at least one task before generating a schedule.")
    else:
        scheduler = Scheduler(st.session_state.owner)   # Scheduler talks to Owner
        plan      = scheduler.generate_plan()

        st.success(plan.summary())

        if plan.scheduled:
            st.markdown("#### ✅ Scheduled")
            for pet, task in plan.scheduled:
                st.markdown(
                    f"- **{task.name}** — {task.duration} min &nbsp; "
                    f"(priority {task.priority})"
                )

        if plan.skipped:
            st.markdown("#### ⏭ Skipped (not enough time)")
            for pet, task in plan.skipped:
                st.markdown(
                    f"- {task.name} — {task.duration} min "
                    f"(priority {task.priority})"
                )

        with st.expander("💡 Why this plan?"):
            st.text(scheduler.explain_plan(plan))