# ShopEasy RAG Knowledge Base

This folder contains eight separate, retrieval-friendly Markdown
documents:

1.  Returns
2.  Refunds
3.  Shipping and delivery
4.  Cancellation
5.  Warranty
6.  Payments
7.  Customer FAQ
8.  Privacy

## Important: sample policies

These are synthetic demonstration policies written for the ShopEasy
project. They are not verified terms of a real retailer and are not
legal advice. Before production use, replace illustrative timelines,
eligibility rules, exclusions, and contact details with policies
approved by the business.

## Suggested ingestion

-   Keep each Markdown file as a separate source document.
-   Attach metadata from the YAML front matter: `title`, `category`,
    `document_type`, `version`, `effective_date`, `region`, and
    `status`.
-   Split on Markdown headings where possible, then apply a token-based
    chunk-size limit with a small overlap.
-   Preserve the document title and section heading in each chunk's
    metadata or text.
-   Do not merge unrelated policy sections into one chunk.
-   Re-ingest changed documents by version or content hash; avoid
    leaving stale policy chunks active.
-   Keep these general policy documents separate from private customer
    order, payment, and ticket records.

## Important RAG boundary

Use RAG for general policy and FAQ answers. Use authenticated database
tools for customer-specific facts such as order status, payment state,
refund state, ticket history, and delivery tracking. Never use vector
retrieval as an authorization mechanism.

## Suggested evaluation questions

-   How many days do I have to return an eligible product?
-   Does submitting a return request mean my refund is complete?
-   My payment was deducted but no order was created. What should I do?
-   Can I cancel an order after it has shipped?
-   Does every product have a one-year warranty?
-   What should I do if tracking says delivered but I did not receive
    the parcel?
-   Can I share my OTP with customer support?
-   Does the RAG knowledge base contain my private order history?

For questions where the demo policy does not provide enough information,
the assistant should say that the policy does not specify the answer and
offer escalation rather than inventing a rule.
