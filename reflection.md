# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.

The initial UML included five classes: Owner, Pet, Task, Scheduler, and Plan

- What classes did you include, and what responsibilities did you assign to each?

Owner holds the pet owner's name, available time for the day, and a preferences dict for future extensibility. Pet is a simple data holder — name, species, age, and freeform notes. Task represents a single care activity with a name, duration in minutes, a 1–5 priority, a category string, and a is_valid() method to keep bad data out of the scheduler. Scheduler is the core engine: it holds references to an Owner and a Pet, owns the list of tasks, and exposes add_task, remove_task, generate_plan, and explain_plan. Plan is a dedicated output object that carries the scheduled list, the skipped list, total minutes used, and methods for human-readable output (summary, reasoning, to_dict).
The key responsibility split was: data classes know nothing about scheduling, and Scheduler knows nothing about display. Plan sits in between as a clean handoff object.

**b. Design changes**

- Did your design change during implementation?

Yes

- If yes, describe at least one change and why you made it.

One meaningful change from the initial stub design: explain_plan on Scheduler ended up delegating almost entirely to plan.reasoning() rather than building its own explanation string. The original stub suggested Scheduler would own that logic, but during implementation it became clear that Plan already held everything needed (the scheduled list, skipped list, and time totals), so putting the reasoning there avoided having Scheduler reach back into a Plan it had just produced. This made Plan more self-contained and made explain_plan on Scheduler a thin wrapper that just prepends a header line.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?

The scheduler considers two constraints: available time (the owner's available_minutes budget) and task priority (the 1–5 value on each Task). 

- How did you decide which constraints mattered most?

Priority was treated as the primary signal because it directly encodes what the owner considers important, a priority=5 task like medication should never be bumped in favour of a priority=2 enrichment activity just because the enrichment activity was added first. Time is the hard outer constraint: no matter how the priorities sort out, the total scheduled duration cannot exceed the budget.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.

The scheduler uses a greedy first-fit approach: it walks the priority-sorted list and includes each task if it still fits, skipping it otherwise even if a later, shorter task could have filled the remaining gap. For example, if 15 minutes remain and the next task needs 20 minutes, that task is skipped — even if a 10-minute task sitting lower in the list would have fit.

- Why is that tradeoff reasonable for this scenario?

his is reasonable here because the scenario is a daily care plan for a pet owner, not a bin-packing optimisation problem. The owner benefits more from a predictable, easy-to-explain plan than from a mathematically optimal one. A greedy priority-sort is also transparent: you can look at the output and immediately understand why each task was included or skipped, which is exactly what plan.reasoning() communicates.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
