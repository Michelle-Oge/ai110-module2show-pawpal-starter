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

AI was used across every phase of the project, but the role it played shifted as the work progressed. Early on it was most useful for design brainstorming, working through what responsibilities each class should own, whether Pet or Owner should hold the task list, and how Scheduler should reach the data it needs. In the middle phases it helped with implementation.

- What kinds of prompts or questions were most helpful?

The most productive prompts were ones that gave context before asking a question. Something like "given that Scheduler only holds a reference to Owner, how should it get all pending tasks across multiple pets?" got a more useful answer than "how do I get tasks?" because it constrained the solution space to fit the existing design. 

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.

The clearest moment of not accepting a suggestion as-is was around conflict detection. An early AI suggestion implemented it by raising a ValueError when a conflict was found, stopping execution immediately.

- How did you evaluate or verify what the AI suggested?
Verification was mostly done by mentally tracing the function call
---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

The test suite covered four main areas: task validation (is_valid), recurrence logic (mark_complete return values and date arithmetic), sorting correctness (chronological order, slotless tasks last), and conflict detection (one conflict, multiple conflicts, no false positives, warning string contents). On top of those, filtering and the generate_plan integration tests verified that the scheduler's outputs matched the inputs correctly.
These were important for different reasons.  Conflict detection needed the "multiple conflicts all reported" test specifically because the naive implementation might short-circuit after the first match. Sorting needed the out-of-order input test because a correct sort on already-sorted input proves nothing.

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

Very Cofident.
The edge cases worth testing next would be: a task whose duration exactly equals the remaining budget after previous tasks are scheduled (off-by-one in the greedy loop), an owner with zero available_minutes, a recurring task that is marked complete multiple times in the same session, and conflict detection when the same pet has two tasks at the same slot rather than two different pets.
---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
The cleanest decision in the project was making Plan a dedicated output object rather than returning a plain dict or tuple from generate_plan. Having summary(), reasoning(), and to_dict() live on Plan meant the Streamlit UI could call them without the scheduler needing to know anything about how results would be displayed. That separation held up through all three phases without needing to be revisited, which is usually a sign that a design boundary was drawn in the right place.

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
The time_slot field being a raw "HH:MM" string is the shakiest part of the design. It works as long as inputs are well-formed, but there is no validation that "08:00" is actually a valid time. Someone could enter "25:99" and the sort would still run without error, just with a invalid result.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

The most important thing this project demonstrated is that AI is most useful when the design decisions have already been made and the question is implementation, not architecture. 

DEMO:
c:\Users\miche\OneDrive\Pictures\Screenshots\Screenshot 2026-03-29 235825.png
