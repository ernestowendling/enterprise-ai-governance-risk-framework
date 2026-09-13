# AI Governance Target Operating Model

## Three lines and decision rights

The first line—Business, Product, Technology and Data Owners—owns purpose, design, operation, controls and remediation. The second line—AI Governance, Model Risk, Compliance, Legal, Information Security, Data Governance and Operational Risk—sets standards, challenges evidence and controls risk acceptance. Internal Audit provides independent third-line assurance. Senior Management sets risk appetite; the AI Governance Committee approves high-risk uses and escalates critical uses to the Executive Risk Committee.

| Activity | Business Owner | Product / Technical | Data Owner | AI Governance | Model Risk | Compliance / Legal | InfoSec | Operational Risk | Internal Audit | Committee |
|---|---|---|---|---|---|---|---|---|---|---|
| Intake and purpose | A/R | R | C | C | I | C | C | I | I | I |
| Classification | C | R | C | A/R | C | C | C | C | I | I |
| Risk assessment | A | R | R | C | C | C | C | C | I | I |
| Validation | C | C | C | C | A/R | C | C | I | I | I |
| Approval | R | C | C | C | C | C | C | C | I | A |
| Production control | A | R | R | C | C | C | R | C | I | I |
| Monitoring and findings | A | R | R | C | C | C | C | R | I | I |
| Independent assurance | I | I | I | C | C | C | C | C | A/R | I |

`R` responsible · `A` accountable · `C` consulted · `I` informed. The model is intentionally pragmatic: one accountable Business Owner remains answerable even where specialist reviews are distributed.

## Decision rights

| Decision | Accountable authority | Challenge / execution |
|---|---|---|
| Calculated classification | AI Governance framework owner | Technical or Product Owner supplies attributes |
| Classification override | Authority configured for the effective tier | A separate authorised governance requester proposes with rationale |
| Risk assessment | Business Owner | Specialist second-line functions challenge their domains |
| Independent validation conclusion | Model Risk or appointed independent validator | Development supplies evidence but does not approve its own work |
| Control implementation acceptance | Named Control Owner | Second line reviews material evidence |
| Exception approval | Risk Owner at least equivalent to the unmet control | Control Owner remediates; AI Governance tracks expiry |
| Production approval | Tier-derived committee or accountable owner | Business Owner requests; second line advises and challenges |
| Revalidation conclusion | Tier-derived approval authority | Model Risk validates; Business Owner owns continued use |
| Suspension | Business Owner or Risk Owner under defined trigger authority | Operations executes and AI Governance records |
| Retirement | Business Owner | Technology closes access and evidence; AI Governance updates inventory |

Committee participation does not create diffuse shared accountability. Business ownership, specialist conclusions and independent assurance remain distinct.
