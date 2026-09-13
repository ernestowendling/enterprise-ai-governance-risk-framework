# Architecture

The repository separates policy and configuration from deterministic domain logic and the demonstration interface. YAML expresses rules, controls, thresholds and mappings. Python validates inventory data and executes classification, assessment, lifecycle, monitoring and evidence logic. CSV files contain synthetic scenarios. Streamlit presents the operating model without owning governance decisions.

```mermaid
flowchart TB
  U[Business and AI use cases] --> I[AI intake] --> V[Central AI inventory] --> C[Risk classification] --> A[Risk assessment] --> K[Control framework] --> G[Validation and governance approval] --> P[Production AI] --> M[Monitoring · drift · fairness] --> R[Revalidation · incident · retirement]
  O[AI Governance · Model Risk · Compliance · Data Governance · Information Security · Operational Risk] -. challenge and oversight .-> C
  O -. independent review .-> G
  O -. escalation and assurance .-> M
  R --> V
```

The reference implementation uses local files to remain inspectable. A production architecture would add identity and access management, workflow, durable versioned storage, immutable evidence, integrations, segregation of duties and operational resilience.
