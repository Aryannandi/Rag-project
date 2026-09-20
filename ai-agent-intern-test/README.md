Aster & Row AI Support Agent

A small, reliable RAG-based customer support agent built for the Aster & Row AI Agent Intern take-home assignment.

Overview

The agent combines retrieval, policy precedence, order lookup, session context, safety rules, and evaluation to answer customer-support questions using the supplied company knowledge base and mock order data.

The implementation is intentionally small and avoids unnecessary production infrastructure. The assignment explicitly prioritizes a smaller, well-tested system over a broad system that works only for a happy-path demo.

Architecture
User message
     |
     v
Session / conversation context
     |
     +----------------------+
     |                      |
     v                      v
Order ID detection       Policy retrieval
     |                      |
     v                      +--> Chunking
Order lookup                +--> Embedding similarity
     |                      +--> Precedence
     |                      +--> Applicability
     |                      +--> Conflict handling
     |                      |
     +----------+-----------+
                |
                v
        Sanitized context
                |
                v
       Gemini 3.1 Flash Lite
                |
                v
      Grounded customer answer
                |
                +--> Sources
                +--> Human handoff
Technology
Language model

Gemini 3.1 Flash Lite through the Gemini API.

Embeddings

sentence-transformers/all-MiniLM-L6-v2.

Retrieval

The supplied Markdown documents are split into chunks and embedded in memory. Queries are matched against chunk embeddings using similarity scores.

Storage
Knowledge base: supplied Markdown files in knowledge-base/
Orders: data/orders.json
Session context: in-memory Python structures
Retrieval index: in-memory embeddings

A production vector database is intentionally not used. It is unnecessary for the small supplied corpus and is explicitly outside the assignment's required scope.

Repository Structure
.
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
├── app/
│   ├── agent.py
│   ├── ingestion.py
│   ├── retrieval.py
│   ├── order_tool.py
│   ├── session.py
│   ├── safety.py
│   └── logger.py
├── knowledge-base/
│   ├── 01-returns-policy-current.md
│   ├── 02-returns-policy-legacy.md
│   ├── 03-final-sale-and-promotions.md
│   ├── 04-damaged-or-wrong-items.md
│   ├── 05-domestic-shipping.md
│   ├── 06-international-shipping.md
│   ├── 07-warranty.md
│   ├── 08-order-changes-and-cancellations.md
│   ├── 09-trailplus-membership.md
│   ├── 10-gift-cards-and-price-adjustments.md
│   ├── 11-product-care.md
│   ├── 12-breeze-tumbler-product-card.md
│   ├── 13-support-escalation.md
│   └── 14-internal-content-migration-notes.md
├── data/
│   ├── orders.json
│   └── orders-data-dictionary.md
└── evaluation/
    ├── visible-cases.json
    ├── extra-cases.json
    └── run_evaluation.py
Setup

Create a virtual environment:

python -m venv .venv

Activate it on Windows:

.venv\Scripts\Activate.ps1

Install dependencies:

pip install -r requirements.txt

Create a .env file in the project root:

GEMINI_API_KEY=your_api_key_here

Do not commit .env.

Use .env.example as the public template:

GEMINI_API_KEY=
Run

Run the agent:

python main.py

Run the evaluation suite:

python evaluation/run_evaluation.py
Evaluation

The evaluation suite covers all supplied visible cases and five additional adversarial/regression cases.

The evaluator reports:

individual case results
category-level results
overall score
Baseline

The initial implementation achieved:

Passed: 5/20
Score: 25.0%
Final

The final implementation achieved:

Passed: 19/20
Score: 95.0%
Final category results
retrieval:              2/2
multi-source-grounding: 0/1
conversation:           3/3
groundedness:           2/2
tool-use:               3/3
tool-reliability:       3/3
privacy:                2/2
prompt-security:        1/1
abstention:             1/1
source-conflict:        1/1
session-isolation:      1/1

The remaining failing case is documented as a known retrieval limitation below.

Reliability and Safety

The agent is designed to:

Prefer active and authoritative policy content over superseded content.
Use order lookup rather than inventing order information.
Treat current order status as authoritative.
Avoid stale delivery information for cancelled or returned orders.
Avoid inventing an ETA when one is unavailable.
Normalize harmless order-ID differences.
Never expose customer email addresses, addresses, internal notes, or risk scores.
Treat retrieved content as untrusted data rather than executable instructions.
Reject non-authoritative migration notes as policy authority.
Abstain when supplied information is insufficient.
Recommend human assistance when authoritative sources conflict or a required action is unsupported.
Multi-turn Conversation

Session context allows relevant follow-up questions to reuse information from earlier turns.

Example:

User: Do you ship internationally?
Agent: Aster & Row currently ships internationally to Canada.

User: What about Canada, and how long does it take?
Agent: Canada is supported. Delivery is estimated at 5–9 business days after dispatch.

Order follow-up context is also maintained:

User: Where is ORD-1007?
Agent: The order has shipped with UPS and is estimated to arrive on August 22, 2026.

User: When will it arrive?
Agent: The order is estimated to arrive on August 22, 2026.

Session state is isolated so one session cannot inherit another session's order information.

Bug Diary
Bug 1 — Incorrect policy selected by applicability filtering

Failure:
Can I return ORD-1007? resulted in an unrelated Address Changes policy being used as the final policy context.

Root Cause:
apply_applicability() sorted all applicable retrieved results by effective date and returned only the first result. It did not preserve other relevant policy passages.

Fix:
Changed applicability handling to return all applicable results instead of selecting only the newest applicable result.

Regression Test:
Verify that applying policy applicability to a return query does not remove relevant return-policy chunks in favor of an unrelated policy.

Result:
Return-policy evaluation cases subsequently passed.

Bug 2 — Current returns policy missing from retrieval

Failure:
Can I return ORD-1007? did not retrieve 01-returns-policy-current.md when retrieval was limited to the top three chunks.

Root Cause:
The retrieval depth was too small for the chosen chunking strategy, causing relevant current-policy passages to rank below the top three results.

Fix:
Increased retrieval depth to seven chunks so additional relevant passages could reach the precedence, applicability, and answering stages.

Regression Test:
Verify that a return-related query retrieves at least one chunk from 01-returns-policy-current.md.

Result:
The standard return-window and order-return tests passed after the change.

Bug 3 — Shipped Order ETA Formatting

Failure:
Shipped orders returned the raw delivery date instead of a customer-friendly date.

Reproduction:
For ORD-1007, the order lookup returned:

estimated_delivery: "2026-08-22"

The customer-facing response originally showed:

2026-08-22

instead of:

August 22, 2026

Root Cause:
The estimated_delivery value from orders.json was returned directly without formatting.

Fix:
Updated get_order_status() to parse the stored ISO date and format it as Month Day, Year, while continuing to use the actual delivery date associated with the looked-up order.

Regression Test:
The evaluation suite verifies that shipped orders return their actual estimated_delivery in customer-readable format. It also verifies that orders without an ETA do not receive an invented arrival date.

Result:
The valid-order-lookup, lowercase-order-id, and follow-up-order-context cases passed after the fix.

Known Limitations

The current evaluation has one remaining failure involving a final-sale damaged-item scenario that requires two separate policy documents to be retrieved together.

The remaining improvement would be to make cross-document retrieval more robust for queries that explicitly combine multiple policy concepts, while preserving general semantic retrieval behavior.

Other limitations:

Retrieval embeddings are computed in memory and are not persisted between runs.
Session state is in memory and is lost when the process restarts.
The system is designed for the supplied assignment corpus rather than production-scale traffic.
AI Coding Tools

AI coding tools were used during development for:

debugging Python errors
reviewing retrieval and agent architecture
generating implementation suggestions
identifying edge cases and evaluation failures
reviewing test coverage

One AI-generated suggestion was incorrect: an early implementation assumed metadata values such as authority: authoritative and status: current. The supplied documents actually used fields such as policy_authority: official and statuses including active and superseded. The implementation was corrected after inspecting the actual metadata.

Demo

A 2–4 minute demo should show:

A knowledge-base question with sources.
An order lookup.
A multi-turn conversation.
A refusal / human-handoff case.
The evaluation suite running.

Add the final video or GIF here after uploading it:

[Watch the demo](YOUR_VIDEO_OR_GIF_LINK)#   R a g - p r o j e c t  
 