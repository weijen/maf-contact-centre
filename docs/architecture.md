# Architecture

## Overview

This project is a simple multi-agent customer service system for Acme Corporation.

It contains three agents:

- **receptionist**: the single entry point for all customer conversations
- **billing**: handles payment, invoice, and account-related questions
- **support**: handles technical issues and troubleshooting

The system uses **handoff orchestration**:
1. Every customer starts with the receptionist.
2. The receptionist either:
   - answers a simple general question directly, or
   - transfers the conversation to billing or support.
3. Specialists may transfer back when the issue falls outside their responsibility.

This design keeps responsibilities clear and makes routing and task completion easier to evaluate.

---

## Design Goals

The architecture is designed to optimize for:

- **clear responsibility boundaries**
- **simple handoff behavior**
- **tool and MCP integration**
- **easy evaluation with azure-ai-evaluation**
- **future extensibility**

This is intentionally a **small and controlled architecture**, not a free-form multi-agent chat.

---

## Agent Responsibilities

### 1. Receptionist

The receptionist is the **only public entry point**.

#### Responsibilities
- greet the customer
- understand the customer's request
- answer simple general questions
- help with delivery slots and order information through the orders MCP server
- hand off billing questions to billing
- hand off technical questions to support

#### Allowed direct actions
- greeting
- clarification
- general FAQ
- order information lookup
- delivery slot booking

#### Must not do
- answer sensitive billing questions
- provide account balance details
- troubleshoot technical issues in depth
- guess specialist-only answers

#### Notes
The receptionist should remain lightweight.  
It should act as a **router plus limited front desk**, not a full-service agent.

---

### 2. Billing

The billing agent handles financial and account-related requests.

#### Responsibilities
- answer billing and payment questions
- look up account information
- explain invoices and charges
- process payment arrangements

#### Allowed direct actions
- retrieve billing information using billing tools
- answer invoice and payment questions
- request missing account details before proceeding

#### Must not do
- troubleshoot technical product issues
- answer general company FAQ unless trivial
- provide sensitive information without verification

#### Notes
Billing must verify account details before returning sensitive account information.

---

### 3. Support

The support agent handles product and technical issues.

#### Responsibilities
- troubleshoot technical problems
- provide step-by-step guidance
- create or escalate support cases when needed

#### Allowed direct actions
- diagnose technical issues
- guide the user through troubleshooting steps
- escalate difficult issues

#### Must not do
- answer billing-specific questions
- provide financial account details
- invent unsupported solutions

#### Notes
Support should be patient, structured, and procedural.

---

## Handoff Model

### Entry Rule
All conversations start with **receptionist**.

### Primary Handoffs
- receptionist -> billing  
  for payment, invoice, charge, refund, and account balance questions

- receptionist -> support  
  for technical issues, troubleshooting, login issues, product failures, and setup help

### Secondary Handoffs
- billing -> receptionist  
  for general questions outside billing scope

- billing -> support  
  when the issue is actually technical rather than financial

- support -> receptionist  
  for general questions outside support scope

- support -> billing  
  when the issue is actually billing-related

---

## Recommended Handoff Policy

To keep behavior predictable, use these rules:

### Receptionist should transfer when:
- the question clearly belongs to billing or support
- the answer requires specialist tools
- the issue contains sensitive account or technical details outside receptionist scope

### Receptionist should not transfer when:
- the question is a simple greeting
- the question is a general FAQ
- the question is about delivery slots or order information that the receptionist can answer with the orders MCP server

### Billing should transfer when:
- the issue is actually a technical fault
- the customer asks a general company question outside billing scope

### Support should transfer when:
- the issue is actually about invoices, payments, refunds, or account balance
- the customer asks a general company question outside support scope

---

## Recommended Boundary Tightening

### Suggestion 1: Make receptionist scope explicitly narrow
Your current receptionist prompt says:

> You can help with delivery slots and order information using the orders MCP server

That is fine, but I would explicitly state:

- receptionist can only handle **basic order and delivery tasks**
- receptionist should **not** diagnose order failures beyond surface-level checks
- if order problems appear technical, transfer to support
- if payment is involved, transfer to billing

Otherwise receptionist may start over-answering.

### Suggestion 2: Define order vs billing boundary clearly
You should document this explicitly:

- **order information / delivery slots** -> receptionist
- **payment for an order / charge / invoice / refund** -> billing
- **order system failure / booking bug / login issue** -> support

This will help a lot when building eval cases.

### Suggestion 3: Add an escalation concept for support
Even if you do not implement a fourth agent, note in the architecture that support can:
- escalate unresolved issues
- create a ticket
- stop after collecting the required details

This gives support a clean fallback behavior.

---

## Tool Ownership

Each agent should have a clear tool boundary.

### Receptionist tools
- general FAQ tool
- orders MCP server
- delivery slot booking tool

### Billing tools
- account lookup
- invoice lookup
- payment status lookup
- payment arrangement tools

### Support tools
- troubleshooting knowledge base
- account access / password reset
- ticket creation / escalation tools

This separation is important for evaluation because it allows us to measure:
- routing correctness
- tool selection correctness
- boundary discipline

---

## Security and Verification Rules

### Receptionist
- must not reveal sensitive account data

### Billing
- must verify account details before revealing sensitive financial information

### Support
- must verify identity before performing sensitive account actions such as password reset

These rules are important candidates for future custom evaluators.

---

## Why This Architecture Works for Evaluation

This architecture is intentionally simple and measurable.

It supports evaluation of:

- **routing accuracy**  
  Did receptionist send the request to the correct specialist?

- **boundary discipline**  
  Did each agent stay within its scope?

- **tool selection accuracy**  
  Did the correct agent call the correct tool?

- **task completion**  
  Was the customer problem actually resolved?

- **clarification behavior**  
  Did the agent ask for required missing details before acting?

This structure is a good fit for `azure-ai-evaluation`, especially for routing, task completion, and custom business-rule evaluators.

---

## Known Tradeoffs

This design intentionally trades some flexibility for control.

### Pros
- easier to reason about
- easier to test
- easier to evaluate
- clearer ownership

### Cons
- receptionist may feel less “smart”
- some edge cases may need extra clarification turns
- mixed-intent requests may require more careful routing

These tradeoffs are acceptable for v1.

---

## Version 1 Scope

Included in v1:
- receptionist as the single entry point
- billing and support specialists
- handoff between all three agents
- limited receptionist order and delivery support
- mock or basic tools
- evaluation dataset for routing and task completion

Not included in v1:
- production authentication
- real billing backend
- advanced memory
- complex multi-step workflow planning
- UI polish