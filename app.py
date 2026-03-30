import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler


st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("Daily care planner for busy pet owners")


if "owner" not in st.session_state:
    st.session_state.owner = None


with st.sidebar:
    st.header("Owner info")
    with st.form("owner_form"):
        owner_name = st.text_input(
            "Your name",
            value=st.session_state.owner.name if st.session_state.owner else "Alex",
        )
        avail_min = st.number_input(
            "Available minutes today",
            min_value=1, max_value=720,
            value=st.session_state.owner.available_minutes
                  if st.session_state.owner else 60,
            step=5,
        )
        if st.form_submit_button("Save owner"):
            old_pets = st.session_state.owner.pets if st.session_state.owner else []
            st.session_state.owner = Owner(name=owner_name,
                                           available_minutes=avail_min)
            for p in old_pets:
                st.session_state.owner.add_pet(p)
            st.success(f"Saved — {owner_name}, {avail_min} min")

if st.session_state.owner is None:
    st.info("Fill in your name and available time in the sidebar, "
            "then click **Save owner** to get started.")
    st.stop()

owner: Owner = st.session_state.owner
scheduler    = Scheduler(owner)


tab_pets, tab_tasks, tab_plan = st.tabs(["🐶 Pets", "📋 Tasks", "🗓 Today's Plan"])


with tab_pets:
    st.subheader("Your pets")

    with st.expander("➕ Add a pet", expanded=len(owner.pets) == 0):
        with st.form("add_pet_form"):
            c1, c2 = st.columns(2)
            pet_name    = c1.text_input("Pet name")
            pet_species = c2.selectbox("Species",
                          ["dog", "cat", "rabbit", "bird", "other"])
            pet_age     = c1.number_input("Age (years)",
                          min_value=0, max_value=30, value=1)
            pet_notes   = c2.text_input("Notes (optional)")
            if st.form_submit_button("Add pet"):
                if not pet_name.strip():
                    st.error("Pet name cannot be empty.")
                else:
                    owner.add_pet(Pet(name=pet_name.strip(), species=pet_species,
                                     age=pet_age, notes=pet_notes))
                    st.success(f"Added {pet_name}!")
                    st.rerun()

    for pet in owner.pets:
        with st.container(border=True):
            c_info, c_del = st.columns([5, 1])
            c_info.markdown(
                f"**{pet.name}** &nbsp;·&nbsp; {pet.species} "
                f"&nbsp;·&nbsp; age {pet.age}"
            )
            if pet.notes:
                c_info.caption(pet.notes)
            pending = len(pet.get_pending_tasks())
            total   = len(pet.tasks)
            c_info.caption(f"{total} task(s) total · {pending} pending")
            if c_del.button("✕", key=f"del_pet_{pet.name}"):
                owner.remove_pet(pet.name)
                st.rerun()

    if not owner.pets:
        st.info("No pets yet — add one above.")


with tab_tasks:
    st.subheader("Care tasks")

    if not owner.pets:
        st.warning("Add a pet first before creating tasks.")
        st.stop()

    conflicts = scheduler.detect_conflicts()
    if conflicts:
        st.error(
            f"**⚠ {len(conflicts)} scheduling conflict(s) detected** — "
            "two or more tasks share the same time slot. "
            "Update the tasks below to resolve them."
        )
        for w in conflicts:
            st.warning(w)


    with st.expander("➕ Add a task", expanded=True):
        with st.form("add_task_form"):
            c1, c2 = st.columns(2)
            target_pet  = c1.selectbox("For which pet?", options=owner.pets,
                                       format_func=lambda p: p.name)
            t_category  = c2.selectbox("Category",
                          ["walk", "feeding", "meds", "enrichment",
                           "grooming", "training", "general"])
            t_name      = c1.text_input("Task name",
                          placeholder="e.g. Morning walk")
            t_time_slot = c2.text_input("Time slot (HH:MM, optional)",
                          placeholder="08:00")
            t_duration  = c1.number_input("Duration (min)",
                          min_value=1, max_value=240, value=20)
            t_priority  = c2.slider("Priority", 1, 5, 3,
                          help="1 = low · 5 = critical")
            t_frequency = c1.selectbox("Frequency",
                          ["once", "daily", "weekly"])
            t_notes     = c2.text_input("Notes (optional)")

            if st.form_submit_button("Add task"):
                new_task = Task(
                    name=t_name.strip(),
                    duration=t_duration,
                    priority=t_priority,
                    category=t_category,
                    notes=t_notes,
                    time_slot=t_time_slot.strip(),
                    frequency=t_frequency,
                )
                try:
                    target_pet.add_task(new_task)
                    st.success(f"Added '{new_task.name}' to {target_pet.name}.")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))


    st.markdown("#### Task list")
    fc1, fc2 = st.columns(2)
    pet_filter    = fc1.selectbox(
        "Filter by pet",
        options=["All"] + [p.name for p in owner.pets],
    )
    status_filter = fc2.selectbox(
        "Filter by status",
        options=["All", "Pending", "Completed"],
    )


    filter_kwargs: dict = {}
    if pet_filter    != "All":
        filter_kwargs["pet_name"]  = pet_filter
    if status_filter == "Pending":
        filter_kwargs["completed"] = False
    elif status_filter == "Completed":
        filter_kwargs["completed"] = True

    filtered = scheduler.filter_tasks(**filter_kwargs)


    sorted_pairs = []
    for pet in owner.pets:
        pet_tasks = [t for p, t in filtered if p.name == pet.name]
        for t in scheduler.sort_by_time(pet_tasks):
            sorted_pairs.append((pet, t))


    if sorted_pairs:
        current_pet_name = None
        for pet, task in sorted_pairs:
            # Print a pet header whenever the pet changes
            if pet.name != current_pet_name:
                st.markdown(f"**{pet.name}**")
                current_pet_name = pet.name

            c_info, c_done, c_del = st.columns([5, 1, 1])
            strike = "~~" if task.completed else ""
            slot   = f" `{task.time_slot}`" if task.time_slot else ""
            freq   = f" ·  _{task.frequency}_" if task.frequency != "once" else ""
            stars  = "★" * task.priority + "☆" * (5 - task.priority)

            c_info.markdown(
                f"{strike}{task.name}{strike}{slot}  "
                f"{stars} · {task.duration} min · "
                f"`{task.category}`{freq}"
            )
            if task.notes:
                c_info.caption(task.notes)

            if not task.completed:
                if c_done.button("✓", key=f"done_{pet.name}_{task.name}"):
                    # mark_task_complete handles recurrence automatically
                    scheduler.mark_task_complete(pet.name, task.name)
                    st.rerun()
            if c_del.button("✕", key=f"del_{pet.name}_{task.name}"):
                pet.remove_task(task.name)
                st.rerun()
    else:
        st.info("No tasks match the current filter.")


with tab_plan:
    st.subheader("Today's plan")

    if conflicts:
        st.error(
            f"⚠ **{len(conflicts)} conflict(s)** found in your task list. "
            "Resolve them in the **Tasks** tab before generating a plan."
        )
        for w in conflicts:
            st.warning(w)

    pending = owner.get_all_pending_tasks()
    if not pending:
        st.info("No pending tasks — add some in the Tasks tab.")
    else:
        if st.button("🗓 Generate plan", type="primary"):
            plan = scheduler.generate_plan()

            st.success(plan.summary())

            if plan.scheduled:
                st.markdown("### ✅ Scheduled")

                sorted_sched = sorted(
                    plan.scheduled,
                    key=lambda pt: ("1", "") if not pt[1].time_slot
                                  else ("0", pt[1].time_slot),
                )

                rows = []
                for pet, task in sorted_sched:
                    rows.append({
                        "Time":     task.time_slot or "—",
                        "Pet":      pet.name,
                        "Task":     task.name,
                        "Duration": f"{task.duration} min",
                        "Priority": "★" * task.priority + "☆" * (5 - task.priority),
                        "Category": task.category,
                    })
                st.table(rows)

            if plan.skipped:
                st.markdown("### ⏭ Skipped (not enough time)")
                for pet, task in plan.skipped:
                    st.markdown(
                        f"- **{task.name}** ({pet.name}) — "
                        f"{task.duration} min · priority {task.priority}"
                    )

            with st.expander("💡 Why this plan?"):
                st.text(scheduler.explain_plan(plan))