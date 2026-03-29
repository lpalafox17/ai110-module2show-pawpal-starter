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
