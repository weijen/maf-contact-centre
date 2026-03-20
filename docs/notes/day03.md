Day 3 completed:
- Added mock tools for billing and support
- Added v2 manual test cases covering with-info and missing-info scenarios
- Verified 12/12 correct routing and handoff
- Verified agents can perform basic specialist actions
- Verified agents ask for missing required information before acting
- Main issue found: response formatting needs cleanup
- Next: tighten output formatting and expand eval cases


Main observation:
- Agent behavior is stable across the current v2 cases
- Routing and handoff remain correct on all 12 cases
- The previous output formatting issue was caused by the reporting script, not the model, and has now been fixed