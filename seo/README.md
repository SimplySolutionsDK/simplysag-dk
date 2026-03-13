# SEO workflow for simplysag.dk

This folder is the lightweight semi-automatic SEO system.

## Files

- `profession-mapping.json` — known professions, synonyms, slugs and page input data
- `opportunity-queue.json` — search intents not yet covered, plus comparison opportunities
- `BACKLOG.md` — prioritized next steps so good ideas do not get lost
- `../scripts/generate_seo_page.py` — queue and publish helper
- `../scripts/import_gsc_queries.py` — imports real Google Search Console queries into the opportunity queue

## Best-practice workflow

1. Add or inspect a query:
   ```bash
   python3 scripts/generate_seo_page.py queue-query "sagsstyring skadeservice"
   ```
2. If it maps to an existing profession page, do not create a duplicate URL.
3. If it does not map, review the suggested slug in `seo/opportunity-queue.json`.
4. Publish only when the profession/service is commercially relevant and the page will be useful.
5. After publishing, improve internal links where relevant — don't rely on sitemap alone.

## Import real Search Console queries

List available properties:

```bash
python3 scripts/import_gsc_queries.py --list-sites
```

Import queries from the SimplySag property into the queue:

```bash
python3 scripts/import_gsc_queries.py \
  --site-url sc-domain:simplysag.dk \
  --days 90 \
  --row-limit 250 \
  --min-impressions 3
```

What this does:
- pulls real GSC queries via the existing service-account key
- runs each query through the queue classifier
- maps known intents to existing pages
- ignores broad junk like purely generic modifier phrases
- queues only uncovered opportunities worth reviewing

## Publish a new profession page

```bash
python3 scripts/generate_seo_page.py publish-profession \
  --slug sagsstyring-skadeservice \
  --title "Sagsstyring til skadeservice" \
  --group "skadeservicefirmaer" \
  --companies "skadeservicefirmaer" \
  --examples "akutte opgaver, affugtning, skader og dokumentation" \
  --intro "Hold styr på sager, billeder og tidsforbrug i skadeservicearbejde."
```

That command will:
- generate the page folder and `index.html`
- append the page to `sitemap.xml`
- append the page to `llms.txt`

## Important constraint

Do not auto-publish every query. This system is intentionally semi-automatic. Thin pages and noisy long-tail spam will hurt more than help.
