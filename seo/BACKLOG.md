# SEO backlog for simplysag.dk

Maintained as the next-step queue for programmatic SEO, comparison pages, and query capture.

## High priority

- [x] **A: Connect Search Console / query ingestion to the SEO workflow**
  Real search queries can now be imported into `seo/opportunity-queue.json` via `scripts/import_gsc_queries.py`, using the existing GSC service-account access for `sc-domain:simplysag.dk`.

## Next up

- [ ] **B: Add more comparison pages**
  Good next candidates:
  - `/apacha-alternativ/`
  - `/minuba-vs-simplysag/`
  - `/ordrestyring-vs-simplysag/`
  - possibly broader commercial pages like `/billig-sagsstyring-haandvaerker/`

- [ ] **C: Expand profession/service coverage using the new generator workflow**
  Good next candidates from queue and adjacent niches:
  - skadeservice
  - ejendomsservice
  - skadedyrsbekæmpelse
  - ventilation
  - solcellemontage

## Notes

- Do not auto-publish every query.
- Prefer review-first publishing to avoid thin pages.
- When adding new pages, also improve internal linking instead of relying on sitemap only.
