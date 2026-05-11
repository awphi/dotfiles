# Global Agent Instructions

## Coding Style

When writing code, carefully consider the following guidance and only deviate from it if you have a strong reason to do so (i.e. simplicity, following existing patterns, ambiguity in requirements). Explain trade-offs you've made against these criteria when required.

General rules:

- Prefer simple solutions over complex ones.
- Prefer existing tools, libraries, commands, project patterns, and conventions over adding new ones.
- Introduce a new tool, dependency, abstraction, or pattern only when it clearly makes the solution simpler, safer, or more maintainable, or when explicitly requested.
- Make small, targeted changes. Avoid speculative refactors and unnecessary architecture.

### 1. Get the nouns and verbs right.

Great names capture what something is or does and create a clear, intuitive model. They show you understand the domain. Take time to find good names, where nouns and verbs fit together, making the whole greater than the sum of its parts.

### 2. Document the 'why', not the 'what'

Use comments sparingly to explain why decisions were made, not just what the code does. Knowing the intent helps others maintain and extend the code properly. Give context for complex algorithms, unusual approaches, or key constraints. Do not comment on what the code is doing if it's already clear.

### 3. Prefer pure functions where possible

Pure functions are easier to test, debug, and reuse. Seek to separate computation from side effects (I/O, state changes) by extracting pure logic into separate functions.

### 4. Limit function length

Keep functions concise, ideally under 70 lines. Shorter functions are easier to understand, test, and debug. They promote single responsibility, where each function does one thing well, leading to a more modular and maintainable codebase.

### 5. Understand and respect all errors

Never throw errors away. For every error, consider:

- Is this ever expected to occur in a well functioning system?
- Can this be recovered from?
- Does the user need to take action in response to this?
- Should I propagate this up the stack for something else to handle?

### 6. Fail fast

Halt execution the moment the system enters an invalid state. Failing late creates a gap between the root cause and the symptom, making debugging difficult and risking data corruption. Constraining the valid states of the system simplifies the number of considerations when debugging.

- **Internal Logic:** Assert liberally. Enforce programmer contracts and invariants aggressively.
- **External Boundaries:** Validate strictly. Reject malformed input at the door. Only tolerate malformed input if the UX benefits clearly outweigh the implementation complexity.

### 7. YAGNI (You Ain't Gonna Need It)

Fight to keep code simple. Avoid adding complexity until a clear justification exists for it.

### 8. New code is accompanied by tests

Code changes should be accompanied by updated tests which exercise that behaviour.

### 9. Tests are focussed

Prefer many, small tests which focus on asserting a single behaviour. Avoid large tests which arrange large amounts of state to test many things at once.
