# Video walkthrough

Target length: 90–110 seconds. Speak conversationally; this is a guide, not something to memorize word for word.

## Narration

> Hi Caprae team—and hopefully a few future colleagues. I'm Ashish, and this is Scout.
>
> I built it in roughly five hours, so I chose not to build another scraper. SaaSquatch already finds companies. Scout answers who is worth calling first—because a thousand-row spreadsheet is also a great way to lose an afternoon.
>
> The user defines an acquisition thesis: industry, geography, company size, operating history, and exclusions. Scout scores every lead against those rules, so the buyer stays in control instead of trusting a black box.
>
> Opening a company shows every point, positive signal, data gap, and red flag. It also creates a deterministic acquisition rationale and outreach opener. There is no paid AI API and no invented financials or owner intent.
>
> I can shortlist, review, or reject the lead. CSV import includes validation and deduplication, and the shortlist exports into a sales-ready CSV. The workflow is simple: import, score, verify, shortlist, and contact.
>
> Under the hood, this is React and TypeScript, FastAPI, and PostgreSQL. The demo runs on Render with Neon, and the repository includes a health-checked Docker Compose deployment. The scoring and main workflows are covered by automated tests.
>
> The goal was not more leads. It was fewer wasted calls and more useful owner conversations. Next, I would use replies, meetings, and LOIs to recommend transparent scoring improvements.
>
> That's the build. Thanks for taking a look—and I hope we get to build the next version together.

## Shot plan

| Time | What to show | What to emphasize |
| --- | --- | --- |
| 0:00–0:10 | Ranked lead queue | Introduce yourself, Scout, and the five-hour constraint |
| 0:10–0:24 | Scroll the queue, then open Acquisition thesis | Raw volume is not prioritization; criteria belong to the buyer |
| 0:24–0:49 | Open a strong lead | Score breakdown, reasons, warnings, red flags, and traceability |
| 0:49–1:03 | Show rationale and outreach; click Shortlist | Useful next action without fabricated claims |
| 1:03–1:15 | Open Import CSV, mention duplicate protection, then show Export | Integration with an existing outreach workflow |
| 1:15–1:30 | Briefly show README architecture and CI badge | React, FastAPI, PostgreSQL, Render/Neon, Docker, and tests |
| 1:30–1:42 | Return to the queue | Business outcome, next step, and candid close |

## Recording checklist

- Wake the free backend by opening the API health link before recording.
- Keep one or two leads shortlisted so the workflow and export are visible.
- Record the deployed application in a clean browser window at 1080p.
- Hide bookmarks, notifications, credentials, and unrelated tabs.
- Use OBS window capture and a clear microphone; a webcam is optional.
- Do one practice run, then speak from the product instead of reading every word.
- Smile at the opening and closing, but do not force the joke or rush the technical section.
- A small pause or natural correction is fine. Clarity matters more than sounding rehearsed.
- Open the uploaded video in an incognito window to confirm evaluator access.
