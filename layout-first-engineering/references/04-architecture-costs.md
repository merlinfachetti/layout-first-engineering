# Technology architecture, sustainability and cost discipline (S4)

## Evaluate technology **after** design + scope approval

Assess constraints first: user load, responsiveness and media needs, offline/mobile, localization, accessibility, auth, data sensitivity, external integrations, SEO, deployment geography, maintainers' skills, ownership, expected longevity, budget and portability. Existing code is a constraint and asset, not something to rewrite by reflex.

**Evaluate at least two feasible approaches** when the choice has cost, lock-in, team impact or migration implications. One should normally be the simplest maintainable solution. Comparison criteria:

- Ability to faithfully implement approved interaction/design, including motion
- Developer/team familiarity, ecosystem maturity and maintainability
- Type safety, testability, observability, security ecosystem, support horizon
- Frontend rendering needs, accessibility, performance
- Data model and sync needs, data governance, backup/restore, portability
- Operational complexity, infrastructure burden, vendor lock-in and exit plan
- Upfront cost, recurring cost and uncertainty under multiple usage scenarios

Do not recommend a backend for a static page; do not recommend serverless, microservices, Kubernetes, blockchain, AI or paid external services without an actual requirement. Vendor marketing is not evidence of technical suitability.

## Required outputs

1. **ADR(s)**: Context, drivers, options, evidence, chosen path, rejected alternatives, consequences and date/status.
2. **System context diagram** (Mermaid/plain diagram), trust boundaries, data flow and contracts, only where needed.
3. **Delivery architecture**: environments, domain/DNS, CDN/storage, CI/CD, identity, secrets, logging, backups, runtime monitoring and rollback.
4. **Threat and privacy review**: tailored to data processed; call out obligations requiring specialist legal/security review.
5. **Economics report**: one-time build, monthly recurring, variable usage, payments/transaction fees, design/AI/connectors, hosting/CDN, db, storage/egress, monitoring, email, domain, analytics, third-party API, developer tooling, VAT/taxes if applicable, contingency, support/maintenance, growth thresholds and cost drivers.

## Costing must be transparent and reproducible

- Ask for currency, expected usage and target budget **when the numbers matter** (not during first visual sketch).
- Show scenarios: baseline/MVP, plausible growth, and high-demand. Use quantities e.g. active users, stored GB, bandwidth, API calls, emails, requests, tokens, seats.
- Use explicit units and formulas: `monthly_cost = fixed_subscription + usage_units * verified_unit_rate + egress + service_fees`.
- Separate **verified provider pricing (provider URL + date + tier + region + currency)** from **assumptions**, **engineering estimates**, and **unknowns**. Never represent assumptions as a live quote.
- If no internet/tools available: do not invent current quotes; leave amounts `TBD/UNVERIFIED`, expose line items/formulas and procurement research steps. If a number is illustrative, label it clearly as illustrative, not the actual price.
- Show start-up vs steady-state costs, migration/exit charges, recurring operations and risk of vendor price changes. State excluded items.
- Suggest a spend cap/alert/usage quota and low-cost downgrade strategy.

## Sustainable engineering

Prefer systems maintainable by the expected team: conventional patterns, small surface area, data export paths, owner-run documentation, managed services only where economics justify, predictable upgrades, limited dependencies and reliable tests. Consider energy/data efficiency when workload warrants. Sustainability means lifecycle cost, accessibility, maintainability, and responsible data usage, not only infrastructure invoices.

Get G4 approval for proposed architecture, MVP boundary, cost envelope and externally committed service choices before production code.
