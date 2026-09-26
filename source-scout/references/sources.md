# Where to scan

Adjust the lists per company; keep the watchlist as the source of truth. Search the last 90 days on a first run.

## Papers

| Field | Venues (proceedings, OpenReview, DBLP) | Preprints and indexes |
|---|---|---|
| ML / AI | NeurIPS, ICML, ICLR, AAAI, KDD, ACL/EMNLP, CVPR, MLSys | arXiv cs.LG, cs.AI, cs.CL, cs.DB, cs.DC; Semantic Scholar; Papers with Code; Google Scholar alerts |
| Databases | SIGMOD, VLDB (PVLDB), ICDE, CIDR, EDBT, DaMoN | arXiv cs.DB; DBLP |
| Systems | OSDI, SOSP, NSDI, ATC, EuroSys, ASPLOS, MLSys | arXiv cs.DC, cs.OS |

Start from the research map's anchors: `scripts/scholar_search.py anchors --map research-map.md --problem R<n> --edge citations|recommendations` (Semantic Scholar API; set `S2_API_KEY` for a higher rate limit). Then expand from sources already kept (`scholar_search.py expand --id <arXiv:…|DOI:…>`). Check "best paper" and "industry track" lists separately: industry-track papers often come with deployment evidence.

## Open-source projects

- GitHub / GitLab search filtered by topic, language and recent activity; trending lists in the relevant language and topic
- Release notes and changelogs of systems the company uses or competes with (databases, query engines, vector stores, ML frameworks, serving stacks)
- Design docs, RFCs and enhancement proposals in project repos (e.g. `docs/design`, `rfcs/`, KIPs, PEPs-style proposals)
- Papers-with-Code and Hugging Face model / dataset releases for ML
- Benchmarks repositories and leaderboards (ANN-Benchmarks, TPC results, MLPerf, ClickBench, BIRD/Spider, etc.)

Signals to record: licence, last commit, maintainers' affiliation, production users, and whether benchmarks are reproducible from the repo.

## Technical blog posts

- Engineering blogs of large infrastructure companies and database / ML vendors (cloud providers, database companies, model labs, streaming and analytics vendors)
- Independent benchmarkers and consultancies that publish setups and raw numbers
- Personal blogs of well-known researchers and engineers in the field
- Aggregators: Hacker News, Lobsters, r/MachineLearning, r/dataengineering, DB and ML newsletters (Data Engineering Weekly, The Batch, Import AI, DB Weekly), conference recaps

Weigh vendor posts as `self-reported` at best; an independent reproduction or a critical discussion thread raises or lowers the evidence level.

## Query construction

For each watchlist sub-problem, write 2–4 queries from the map's *public search terms* with synonyms from adjacent communities (ML ↔ DB ↔ systems ↔ IR ↔ OR). Include the problem phrasing, the technique phrasing, and a constraint phrasing (latency, memory, cost, privacy). Add one query per *bridging concept* phrased in the adjacent field's vocabulary. Log the queries in the run report so the next run can reuse or refine them.
