# Runtime Validation Rules

These rules keep runtime validation useful and safe.

## Default posture

- Scheduled checks should be safe and predominantly read-only.
- Deeper mutation checks should be gated and intentional.
- Validation should reflect deployed truth, not local assumptions.

## Coverage priorities

- auth
- dashboard
- entitlement gates
- core practice flows
- admin visibility
- selected admin mutations

## Failure classification

Every failure should be classified as one of:

- product bug
- environment/deploy bug
- test harness issue

Do not blur these categories.

## Data safety

- Use cleanup for mutation-created fixtures where possible.
- Avoid leaving junk data in production.
- Prefer explicit test namespaces or markers when mutation data must exist briefly.
