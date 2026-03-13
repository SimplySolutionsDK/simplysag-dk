#!/usr/bin/env python3
import argparse
import json
import subprocess
from datetime import date, timedelta
from pathlib import Path

from google.oauth2 import service_account
from googleapiclient.discovery import build

ROOT = Path(__file__).resolve().parent.parent
QUEUE_SCRIPT = ROOT / 'scripts' / 'generate_seo_page.py'
QUEUE_PATH = ROOT / 'seo' / 'opportunity-queue.json'
DEFAULT_KEY_PATH = Path('/home/jacobsimplysolutions/.openclaw/media/inbound/file_55---a5433b54-4ced-456a-a2a7-2d59a49050a1.json')
SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']


def get_service(key_path: Path):
    creds = service_account.Credentials.from_service_account_file(str(key_path), scopes=SCOPES)
    return build('searchconsole', 'v1', credentials=creds, cache_discovery=False)


def list_sites(service):
    return service.sites().list().execute().get('siteEntry', [])


def query_search_analytics(service, site_url: str, start_date: str, end_date: str, row_limit: int):
    body = {
        'startDate': start_date,
        'endDate': end_date,
        'dimensions': ['query'],
        'rowLimit': row_limit,
        'startRow': 0,
        'dataState': 'all',
    }
    res = service.searchanalytics().query(siteUrl=site_url, body=body).execute()
    return res.get('rows', [])


def queue_query(query: str):
    result = subprocess.run(
        ['python3', str(QUEUE_SCRIPT), 'queue-query', query],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(result.stdout)


def load_queue():
    return json.loads(QUEUE_PATH.read_text())


def main():
    parser = argparse.ArgumentParser(description='Import Google Search Console queries into the simplysag.dk SEO opportunity queue')
    parser.add_argument('--key-file', default=str(DEFAULT_KEY_PATH))
    parser.add_argument('--site-url', help='GSC property URL, e.g. sc-domain:simplysag.dk or https://simplysag.dk/')
    parser.add_argument('--days', type=int, default=90)
    parser.add_argument('--row-limit', type=int, default=250)
    parser.add_argument('--min-clicks', type=float, default=0.0)
    parser.add_argument('--min-impressions', type=float, default=5.0)
    parser.add_argument('--list-sites', action='store_true')
    args = parser.parse_args()

    service = get_service(Path(args.key_file))

    if args.list_sites:
        for site in list_sites(service):
            print(json.dumps(site, ensure_ascii=False))
        return

    if not args.site_url:
        raise SystemExit('--site-url is required unless --list-sites is used')

    end = date.today() - timedelta(days=1)
    start = end - timedelta(days=args.days - 1)
    rows = query_search_analytics(service, args.site_url, start.isoformat(), end.isoformat(), args.row_limit)

    processed = []
    for row in rows:
        query = (row.get('keys') or [''])[0].strip()
        clicks = float(row.get('clicks', 0))
        impressions = float(row.get('impressions', 0))
        if not query:
            continue
        if clicks < args.min_clicks:
            continue
        if impressions < args.min_impressions:
            continue
        queued = queue_query(query)
        processed.append({
            'query': query,
            'clicks': clicks,
            'impressions': impressions,
            'queue': queued,
        })

    queue = load_queue()
    queue['generatedAt'] = date.today().isoformat()
    queue['lastGscImport'] = {
        'siteUrl': args.site_url,
        'startDate': start.isoformat(),
        'endDate': end.isoformat(),
        'rowLimit': args.row_limit,
        'minClicks': args.min_clicks,
        'minImpressions': args.min_impressions,
        'processedCount': len(processed),
    }
    QUEUE_PATH.write_text(json.dumps(queue, ensure_ascii=False, indent=2) + '\n')

    summary = {
        'siteUrl': args.site_url,
        'startDate': start.isoformat(),
        'endDate': end.isoformat(),
        'processedCount': len(processed),
        'sample': processed[:10],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
