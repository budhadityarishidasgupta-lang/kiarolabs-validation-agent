# Safe Change Checklist

Before changing validation logic:

- Are we changing the product or just the test?
- If changing the test, does it still verify the real contract?
- If enabling mutations, is the lane gated?
- Are fixtures cleaned up afterward?
- Are we preserving a trustworthy scheduled watchdog?
- Are we surfacing enough diagnostics to separate product vs test issues?
- Would a future operator understand why this assertion exists?

Prefer stronger diagnostics before weaker assertions.
