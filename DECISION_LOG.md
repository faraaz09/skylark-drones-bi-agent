# Decision Log — Skylark Drones BI Agent

## 1. Key assumptions
- The two supplied datasets are imported into two separate Monday.com boards: **Deals** and **Work Orders**, as requested.
- Monday.com is the system of record. The application does not embed or hardcode the supplied dataset.
- Board columns may contain blanks and inconsistent text/date representations; the agent should not infer missing values.
- Founder questions are conversational, so the agent is instructed to ask one focused clarification when a request cannot be answered unambiguously.

## 2. Architecture and trade-offs
**Choice:** Streamlit + Python + Monday.com GraphQL API + OpenAI Responses API.

**Why:** This is fast to build, easy to host, and directly satisfies the required conversational interface and Monday.com integration. A full multi-agent framework would add setup and failure modes without being necessary for the six-hour assignment.

**Trade-off:** The prototype sends a bounded snapshot of live board data to the model instead of implementing a sophisticated semantic query planner. This is simpler and appropriate for the supplied data volume, but a production version should add pagination, deterministic metric tools, query planning, and stronger access controls.

## 3. Data resilience
- Normalize whitespace and blank values before analysis.
- Preserve missingness rather than converting unknown values into guesses.
- Explicitly instruct the agent to report data-quality caveats.
- Monday API/configuration failures stop the answer rather than returning invented business numbers.

## 4. Leadership updates interpretation
I interpret “prepare data for leadership updates” as the ability to answer a concise executive-summary request such as: **“Prepare a leadership update covering pipeline, revenue/execution signals, risks, and key actions.”** The agent should summarize the most decision-relevant signals from both boards, include caveats, and avoid unsupported claims.

## 5. What I would do with more time
- Add deterministic KPI functions for pipeline value, weighted pipeline, aging, collections/AR, and execution status.
- Add pagination and schema-aware Monday column parsing.
- Add automated tests for missing/null values and inconsistent dates.
- Add authentication, audit logging, monitoring, and rate-limit handling.
- Add export to a leadership-ready PDF/email/slide format.
