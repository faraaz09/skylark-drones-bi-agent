# Skylark Drones — Monday.com Business Intelligence Agent

## What it does
A hosted conversational BI agent that reads the Deals and Work Orders boards in Monday.com (read-only), normalizes blank/text values, and answers founder-level business questions with an LLM grounded in the live board data.

## Architecture
`Streamlit UI → Monday.com GraphQL API → normalization → OpenAI Responses API → conversational answer`

The source data is **not hardcoded** into the application. Every refresh queries Monday.com dynamically.

## Setup
1. Import `Deal funnel Data.xlsx` as a Monday.com board named `Deals`.
2. Import `Work_Order_Tracker Data.xlsx` as a separate board named `Work Orders`.
3. Configure suitable Monday column types: text, status, date, numbers/currency, people/text, and dropdown where appropriate.
4. Create a Monday API token with read access.
5. Create an OpenAI API key.
6. In Streamlit Cloud, add these secrets/environment variables:

```text
MONDAY_API_TOKEN=...
MONDAY_DEALS_BOARD_ID=...
MONDAY_WORK_ORDERS_BOARD_ID=...
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4.1-mini
```

7. Deploy `app.py` with `requirements.txt`.

## Example questions
- How is our pipeline looking by sector?
- Which sectors have the highest open pipeline value?
- What deals are likely to close soon?
- What operational work orders have billing or collection risk?
- Compare sales pipeline with execution status.
- Prepare a concise leadership update.

## Error handling
- Missing configuration produces an explicit setup message.
- Monday API errors are surfaced without fabricating results.
- Blank values remain blank and the agent is instructed to disclose data-quality caveats.
- The app is read-only and performs no Monday mutations.

## Time-boxed design
The assignment has a six-hour timeline, so the prototype prioritizes a reliable end-to-end path over a complex multi-agent framework. With more time, add typed tool/function calls, pagination, stronger deterministic KPI calculations, authentication, tests, observability, and a richer leadership-report export.
