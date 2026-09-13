# Swiss Banking Governance Context

## Purpose

This section places the operating model in the context of a Swiss regulated financial institution. It does not assert compliance with Swiss law or FINMA requirements. Applicability, legal interpretation, risk appetite and decision authorities must be confirmed by the institution's competent Legal, Compliance and Risk functions.

## Integration with the bank control environment

AI governance should operate through established governance rather than as a parallel control system:

| Bank discipline | AI governance interaction | Illustrative evidence | Primary decision right |
|---|---|---|---|
| Enterprise risk management | Aggregate AI exposure, residual risk, exceptions and risk acceptance | Portfolio report and committee decision | Senior Management sets risk appetite |
| Model governance | Determine whether model-risk standards apply; validate consequential models independently | Model inventory linkage and validation report | Model Risk owns validation conclusions, not business use |
| Operational risk | Assess process failure, resilience, manual fallback, incidents and remediation | Scenario assessment, continuity test and finding | Business Owner owns operation; Operational Risk challenges |
| Information security | Threat-model AI interfaces, access, data leakage, misuse and provider connectivity | Security assessment and test results | Information Security accepts only its specialist control conclusions |
| Data governance and privacy | Establish ownership, lineage, quality, permitted use, retention and data-subject considerations | Data-quality and privacy assessments | Data Owner is accountable for data fitness |
| Third-party and outsourcing risk | Assess material dependency, contractual controls, change notification, concentration and exit | Due diligence, contract clauses and exit test | Business Owner retains accountability for outsourced use |
| Compliance and Legal | Interpret applicable conduct, customer, employment, privacy and AI obligations | Written assessment and conditions | Competent functions determine institution-specific interpretation |
| Internal control system | Translate risk treatment into controlled activities, evidence, testing and issue management | Control implementation and test records | Control Owners operate; Risk Owners accept residual exposure |
| Internal Audit | Independently assess design and operating effectiveness across the three lines | Audit report and tracked actions | Internal Audit remains independent third-line assurance |

## Decision discipline

The calculated risk tier routes work consistently. An authorised second-line challenge may propose an override, but the calculated result remains visible. An approved effective tier determines controls, validation depth and approval authority. The Business Owner remains accountable for intended use and business outcomes; specialist review does not transfer that ownership.

Production approval requires an institution-specific authority matrix. A critical finding, missing mandatory control evidence, ineffective human oversight or unacceptable validation blocks progression. RED monitoring creates a finding and event-driven revalidation; it does not predetermine suspension or model failure. The accountable authority must explicitly decide whether to investigate, impose conditions, suspend, continue with accepted residual risk or retire.

## Regulatory interpretation boundary

External sources should be separated into three layers:

1. **Confirmed external requirement** — verified current text and competent interpretation.
2. **Illustrative control mapping** — this repository's non-authoritative translation into process, controls and evidence.
3. **Institution-specific implementation** — the bank's policies, materiality, risk appetite, organisation, products and supervisory context.

Swiss regulatory application requires institution-specific interpretation. The repository is not legal advice, a compliance product or evidence that an institution meets any supervisory expectation.
