# 90-second walkthrough script

> Hi, I'm Ashish. SaaSquatch already covers discovery, enrichment, export, outreach, and AI scoring. I focused on the next decision: which sourced companies deserve attention first, and why?
>
> I built Scout, an acquisition-qualification layer. A searcher defines industries, geography, size, operating history, and exclusions; every lead is rescored against those rules.
>
> The queue ranks companies by acquisition fit. Opening a lead shows every awarded point, positive signal, missing field, and red flag. It also creates an acquisition rationale and owner outreach opener from deterministic templates. No paid AI or API key is required, and generated language is never presented as verified fact.
>
> From there, the user can shortlist, review, reject, import deduplicated CSV data, and export a sales-ready shortlist.
>
> Technically, this is React and TypeScript, FastAPI, PostgreSQL, Nginx, and Docker Compose. The scoring engine is isolated and covered by automated tests.
>
> The product decision was not to maximize lead volume. It was to help a searcher spend limited time on companies most likely to produce useful owner conversations.
>
> Next, I would feed replies, meetings, and LOIs back into the system so real outcomes can recommend transparent scoring improvements.

## Recording shot list

| Time | Screen | Narration focus |
| --- | --- | --- |
| 0:00–0:12 | Ranked queue | Problem and product promise |
| 0:12–0:25 | Acquisition thesis | User-controlled criteria |
| 0:25–0:50 | Strong lead drawer | Reasons, breakdown, gaps, rationale |
| 0:50–1:02 | Status controls and opener | Complete qualification workflow |
| 1:02–1:12 | CSV import/export | Existing sales workflow integration |
| 1:12–1:24 | README architecture/tests | Technical decisions |
| 1:24–1:30 | Queue | Business value and next step |
