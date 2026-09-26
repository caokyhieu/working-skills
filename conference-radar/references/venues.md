# Venues and how to fetch them

Checked on 2026-09-26. Listing formats change; when a fetch parses 0 papers, check the listing by hand before trusting any count.

## Scripted backends

| Venue | Usually held | Backend and command | Abstracts in listing | Notes |
|---|---|---|---|---|
| ICLR | Apr–May | `fetch virtual --conf iclr --year Y` | 2025 yes; **2026 no** | orals appear twice (oral and poster events); the script merges them |
| ICML | July | `fetch virtual --conf icml --year Y` | 2025 yes; **2026 no** | includes the position-paper track; filter it with `--none "^position"` on titles if unwanted |
| NeurIPS | December (decisions late Sep) | `fetch virtual --conf neurips --year Y` once the virtual site lists papers (usually Oct–Nov); before that `fetch arxiv --comment "NeurIPS Y"` | 2025 yes | datasets and benchmarks track is included; its topic label says so |
| CVPR | June | `fetch virtual --conf cvpr --year Y` | yes | host `cvpr.thecvf.com` |
| ICCV | October, odd years | `fetch virtual --conf iccv --year Y` | yes | host `iccv.thecvf.com` |
| ECCV | Sep–Oct, even years | `fetch virtual --conf eccv --year Y` | yes | host `eccv.ecva.net` |
| AISTATS | May | `fetch virtual --conf aistats --year Y` | yes | host `virtual.aistats.org` |
| ACL, EMNLP, NAACL, EACL, COLING | Jul, Nov, Apr–Jun, Mar, Jan | `fetch acl --volume <id>` | yes | volume ids: `2025.acl-long`, `2025.acl-short`, `2025.findings-acl`, `2025.emnlp-main`, `2025.findings-emnlp`, `2025.naacl-long`; the ids are listed on `aclanthology.org/events/<venue>-<year>/` |
| Any venue before its proceedings | — | `fetch arxiv --comment "<Venue> <Year>"` | yes | catches only authors who wrote the venue in the arXiv comment, typically 20–40 % of a venue; say so in the coverage section |
| An arXiv area | — | `fetch arxiv --cat cs.LG --since Y --max N` | yes | for "what is new in the field" rather than a venue |

Other conferences on the same virtual-site platform work with `--host <host>`: the listing is `https://<host>/static/virtual/data/<conf>-<year>-orals-posters.json`.

Tracks are normalised to `award`, `oral`, `spotlight`, `poster` (virtual sites), `main`, `findings` (ACL Anthology) and `preprint` (arXiv). The listings do not carry awards. Take them from the venue's awards page or blog, and set `track` to `award` by hand with the page URL in the triage notes.

## Blocked or rate-limited for scripts

| Source | What happens | Use instead |
|---|---|---|
| OpenReview API and PDFs | 403 "challenge verification required" for anonymous clients | virtual-site JSON for listings; `enrich` for arXiv PDFs; a logged-in browser for single PDFs |
| DBLP | bot wall (JavaScript challenge) | the venue's own listing |
| Semantic Scholar API | 429 without a key | set `S2_API_KEY` and use `source-scout/scripts/scholar_search.py` for citation counts or related work |
| arXiv API | rejects Python's HTTP client with 406 | the script retries through `curl`; keep calls at least 3 s apart (the script does) |

## Venues without a backend

AAAI (Feb), IJCAI (Aug), KDD (Aug), COLM (Oct), UAI, COLT, CoRL, RSS, MLSys, TMLR, SIGMOD, VLDB, ICDE, OSDI, SOSP.

1. Try `fetch arxiv --comment "<Venue> <Year>"` first. Report its coverage honestly.
2. Otherwise open the venue's accepted-paper page (or PMLR volume, ACM DL table of contents, `ojs.aaai.org` issue), save it under `.cache/`, and write one JSON line per paper to `papers.jsonl`:

```json
{"id": "kdd2026:<slug>", "venue": "KDD 2026", "year": 2026, "title": "...", "authors": ["..."],
 "affiliations": [], "abstract": "", "topic": "<session or track name>", "keywords": [], "track": "main",
 "url": "<paper page>", "pdf": "", "arxiv": "", "source": "<listing URL>", "also": []}
```

Then run `enrich` on the shortlist to fill abstracts and arXiv links. Every other command works the same way.

## Picking a baseline for trends

Use the previous edition of the **same** venue. When it has abstracts and the current one does not, `trends` compares titles only, which is fairer than mixing and still useful. Comparing different venues (for example, ICML against NeurIPS) mostly measures what each venue attracts, not what changed.
