# Day 1 Notes

## What I completed
- Read core Microsoft Agent Framework docs
- Read Azure AI Evaluation SDK overview
- Created repo: maf-contact-centre
- Provisioned AI Foundry with Terraform
- Created Foundry project
- Added README.md
- Added architecture.md

## Key decisions
- Use receptionist as the only entry point
- Use handoff orchestration, not free-form group chat
- Keep receptionist limited to triage + simple order/delivery tasks
- Separate billing and support responsibilities clearly

## Open questions
- Should billing/support transfer directly to each other in v1?
- How much order-related logic should stay with receptionist?
- Which tools should be MCP first?

## Risks
- Receptionist may become too capable
- Boundaries between order vs billing vs support may become fuzzy
- Evaluation may be messy if routing policy is not explicit

## Plan for Day 2
- Build minimal 3-agent skeleton
- Write first version of prompts
- Define 5-10 eval sample cases