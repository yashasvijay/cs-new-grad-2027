# Sources and attribution

## Direct job feeds

- [Greenhouse Job Board API](https://docs.greenhouse.io/job-board.html)
- [SmartRecruiters Posting API](https://developers.smartrecruiters.com/docs/posting-api)
- [Lever Postings API](https://github.com/lever/postings-api)
- [Ashby public job posting API](https://developers.ashbyhq.com/docs/public-job-posting-api)
- [GitHub schedule behavior](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)

Each configured employer includes its employer board URL in `data/employers.json`. A successful provider response verifies board access, not complete coverage of every employer subsidiary or role.

## Employer universe

The candidate S&P 500 inventory was retrieved on 2026-10-05 from [Wikipedia's constituent table](https://en.wikipedia.org/wiki/List_of_S%26P_500_companies), under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). This derived inventory keeps company names and symbols, deduplicates multiple share classes by company name, and adds curated technology/AI employers and source configuration. The derived inventory is CC BY-SA 4.0; adapter code is independently authored. Wikipedia contributors are credited through the [page history](https://en.wikipedia.org/w/index.php?title=List_of_S%26P_500_companies&action=history). This is a candidate inventory, not confirmed current official index membership. The [official S&P index page](https://www.spglobal.com/spdji/en/indices/equity/sp-500/) is authoritative; no official licensed constituent export was obtained.

## Discovery and visual references

[Vansh's New-Grad-2027](https://github.com/vanshb03/New-Grad-2027) informed employer discovery (Quora, Chicago Trading Company, SimpliSafe, Twitch, Sierra, Replit, and Appian). Its MIT license was checked on 2026-10-05; the notice is retained in `docs/VANSH-LICENSE.txt`. Discovery links are checked through direct employer APIs before publication; discovery-list dates are not copied as employer posting dates.

[Simplify's New-Grad-Positions](https://github.com/SimplifyJobs/New-Grad-Positions) informed the compact company/role/location/apply table layout only. No job database or artwork from Simplify is imported. The Jobright list remains a future discovery source pending license review; no data from it is imported.
