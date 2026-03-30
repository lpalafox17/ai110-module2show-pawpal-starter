# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
My initial UML design model consisted of simple classess while keeping scheduling logic sepereate from data. Core entities like owner, pet, and task store essential informatio while scheudlker generates a schedule made up of timeslots.
- What classes did you include, and what responsibilities did you assign to each?
The classes I included are Pet, owner and they hold data, while preference, constraint and time are all classess that define rules, and scheduler handles all decsion making, like prioritizing tasks and enforcing constraints. 
**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Yes. One concrete change was keeping `PetCareTask` as a lightweight data-first dataclass and moving complex decision logic (sorting, choosing, conflict detection, recurrence) into a separate `Scheduler` service. I did this to keep domain objects simple and testable while making algorithmic behavior easier to iterate on without touching core data structures.



---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

One tradeoff I made is keeping conflict detection lightweight and easy to read rather than using a more optimal but more complex algorithm. The current implementation performs pairwise interval checks (O(n^2)) to detect overlapping TimeSlots and returns human-readable warnings. I shared this method with an AI assistant; it suggested a "sweep-line" approach (sort start/end events and scan once) which would reduce complexity to O(n log n) and be faster on large inputs.

Decision: I kept the pairwise approach for now because the app targets small numbers of daily tasks per owner (where O(n^2) is acceptable) and the simpler code is easier to understand and maintain. If the app needs to scale (many tasks or multi-user heavy loads), I would refactor to the sweep-line approach for better performance.


---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

I used AI in three main phases:

- Design brainstorming: I iterated on UML class relationships, asked for alternative ways to represent constraints vs preferences, and used examples to compare keeping logic in dataclasses vs a separate scheduler service.
- Implementation help: I asked for compact code snippets for common algorithms (sorting by priority, simple recurrence generation using timedelta), and for canonical ways to structure tests for dataclasses.
- Debugging and UX: I consulted AI for idiomatic Streamlit patterns (persisting state in `st.session_state`, safe widget keys) and for user-friendly warning messages for conflicts.

Helpful prompts were short, focused requests like "show a small Python example that marks a dataclass task complete and creates the next daily occurrence" or "explain tradeoffs between keeping logic in dataclasses vs a service layer".

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

Example rejected/modified suggestion

The AI suggested embedding scheduling heuristics directly inside `Pet` (e.g., `pet.schedule_tasks()`), which would couple scheduling decisions to domain state. I rejected that because it mixes responsibilities and would make unit testing harder. Instead I implemented a separate `Scheduler` class and kept `Pet`/`Owner` focused on data management.

How I evaluated it:

- I considered testing and SRP (Single Responsibility Principle): separating scheduler logic made it much easier to write focused tests for scheduling without creating or mutating pets/owners.
- I prototyped both approaches briefly; the separate `Scheduler` version produced clearer tests and simpler reasoning about side effects, so I adopted it.

How separate chat sessions helped

Keeping separate chat threads for distinct phases (design, implementation, testing) made it easy to keep context small and focused. For example, the design thread contained UML and reasoning that I referenced while implementing tests; the implementation thread focused on code snippets and keyboard-level edits. This reduced cognitive load and prevented long chat histories from polluting prompt context.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

I ran unit tests that verify:

- Basic dataclass behavior: adding tasks to a `Pet`, marking a task completed, and ensuring recurrence creates the next occurrence for daily/weekly tasks.
- Sorting and ordering: `Scheduler.sort_by_time()` returns tasks with explicit times first and then orders by priority/duration for unscheduled tasks.
- Conflict detection: scheduling overlapping `TimeSlot`s produces readable warnings rather than crashing.

These tests are important because they exercise the decision surface of the scheduler (ordering, recurrence, conflict handling) and validate behavior users will notice most often.

Confidence and next tests:

I am moderately confident for the small-scale use case (single-owner daily planning). Next tests I'd add:

- Integration tests that simulate several pets and many tasks across multiple days.
- Performance/regression tests comparing pairwise conflict detection vs a sweep-line implementation.
- Edge cases: zero-duration tasks, tasks longer than the available day window, daylight saving time boundary cases for scheduled_time.

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

What went well

- Separating domain dataclasses from scheduling logic made the codebase easier to reason about and test.
- The Streamlit UI provides a quick interactive surface for exercising the scheduler and surfaced state persistence issues early (which were solved via `st.session_state`).

What I would improve

- Replace pairwise conflict detection with a sweep-line algorithm for better scalability.
- Improve warning messages to include pet names rather than IDs and add suggested resolutions (reschedule, split task).
- Add more acceptance/integration tests and CI automation.

Key takeaway about being a lead architect with AI tools

Working as the lead architect while using powerful AI assistants is a collaboration where I set constraints, enforces design principles, and chooses where to accept or reject suggestions. AI accelerates iteration (sketching alternatives, generating boilerplate, suggesting algorithms), but my judgment is required to maintain clean separation of concerns, testability, and maintainability.
