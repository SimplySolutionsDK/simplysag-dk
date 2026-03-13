#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parent.parent
SEO_DIR = ROOT / 'seo'
MAPPING_PATH = SEO_DIR / 'profession-mapping.json'
QUEUE_PATH = SEO_DIR / 'opportunity-queue.json'
SITEMAP_PATH = ROOT / 'sitemap.xml'
INDEX_PATH = ROOT / 'index.html'
LLMS_PATH = ROOT / 'llms.txt'

EXISTING_TOPIC_PATTERNS = [
    {
        'patterns': ['sagsstyring håndværker', 'sagsstyring håndværkere', 'håndværker sagsstyring', 'håndværkere sagsstyring'],
        'slug': 'sagsstyring-haandvaerker',
        'title': 'Sagsstyring til håndværkere',
        'type': 'topic',
        'reason': 'maps to existing core topic page',
    },
    {
        'patterns': ['arbejdsseddel håndværker', 'tidsregistrering håndværker', 'timeregistrering håndværker', 'håndværker tidsregistrering', 'håndværker timeregistrering'],
        'slug': 'sagsstyring-haandvaerker',
        'title': 'Sagsstyring til håndværkere',
        'type': 'topic',
        'reason': 'maps to existing core topic page until dedicated page exists',
    },
    {
        'patterns': ['minuba alternativ'],
        'slug': 'minuba-alternativ',
        'title': 'SimplySag som Minuba alternativ',
        'type': 'comparison',
        'reason': 'maps to existing comparison page',
    },
    {
        'patterns': ['ordrestyring alternativ'],
        'slug': 'ordrestyring-alternativ',
        'title': 'SimplySag som Ordrestyring alternativ',
        'type': 'comparison',
        'reason': 'maps to existing comparison page',
    },
]

COMPARISON_TERMS = ['alternativ', 'vs', 'versus', 'sammenligning']
IGNORED_GENERIC_QUERIES = {
    'app til sagsstyring', 'digital sagsstyring', 'elektronisk sagsstyring',
    'online sagsstyring', 'sagsstyring', 'sagsstyring app', 'sagsstyring system',
    'sagsstyringsprogram', 'sagsstyring gratis', 'simpel tidsregistrering',
    'time sagsstyring', 'time sagsstyring app'
}


def load_json(path: Path):
    return json.loads(path.read_text())


def save_json(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def normalize(text: str) -> str:
    return re.sub(r'\s+', ' ', text.strip().lower())


def slugify(text: str) -> str:
    text = text.lower().strip()
    replacements = {
        'æ': 'ae', 'ø': 'oe', 'å': 'aa',
        '&': ' og ', '/': ' ', '_': ' ',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'\s+', '-', text)
    text = re.sub(r'-+', '-', text).strip('-')
    return text


def infer_from_query(query: str, mapping: dict):
    q = normalize(query)

    if q in IGNORED_GENERIC_QUERIES:
        return {
            'matched': False,
            'existing': False,
            'slug': None,
            'title': None,
            'type': 'generic',
            'status': 'ignored',
            'reason': 'generic query not suitable for a dedicated landing page'
        }

    for topic in EXISTING_TOPIC_PATTERNS:
        if any(pattern in q for pattern in topic['patterns']):
            return {
                'matched': True,
                'existing': True,
                'slug': topic['slug'],
                'title': topic['title'],
                'type': topic['type'],
                'status': 'mapped-existing',
                'reason': topic['reason']
            }

    for profession in mapping['professions']:
        for synonym in profession.get('synonyms', []):
            if normalize(synonym) in q:
                return {
                    'matched': True,
                    'existing': True,
                    'slug': profession['slug'],
                    'title': profession['title'],
                    'type': 'profession',
                    'status': 'mapped-existing',
                    'reason': f"matched synonym: {synonym}"
                }

    cleaned = q
    for phrase in ['sagsstyring', 'app til', 'system til', 'software til', 'for', 'til']:
        cleaned = cleaned.replace(phrase, ' ')
    cleaned = normalize(cleaned)

    if any(term in q for term in COMPARISON_TERMS):
        return {
            'matched': True,
            'existing': False,
            'slug': slugify(q),
            'title': q.title(),
            'type': 'comparison',
            'status': 'queued',
            'reason': 'comparison intent not yet covered'
        }

    if not cleaned or len(cleaned) < 4:
        return {
            'matched': False,
            'existing': False,
            'slug': None,
            'title': None,
            'type': 'generic',
            'status': 'ignored',
            'reason': 'query too broad or too short to justify dedicated page'
        }

    blocked_tokens = {'online', 'digital', 'elektronisk', 'gratis', 'app', 'system', 'program', 'simpel', 'time'}
    cleaned_tokens = set(cleaned.split())
    if cleaned_tokens and cleaned_tokens.issubset(blocked_tokens):
        return {
            'matched': False,
            'existing': False,
            'slug': None,
            'title': None,
            'type': 'generic',
            'status': 'ignored',
            'reason': 'generic modifier query not suitable for dedicated page'
        }

    suggested_slug = f"sagsstyring-{slugify(cleaned)}" if cleaned else None
    return {
        'matched': bool(cleaned),
        'existing': False,
        'slug': suggested_slug,
        'title': f"Sagsstyring til {cleaned}" if cleaned else None,
        'type': 'profession',
        'status': 'queued',
        'reason': 'no existing synonym match'
    }


def ensure_queue_item(query: str):
    mapping = load_json(MAPPING_PATH)
    queue = load_json(QUEUE_PATH)
    info = infer_from_query(query, mapping)
    normalized = normalize(query)

    for item in queue['items']:
        if item['normalized'] == normalized:
            return item, info, False

    item = {
        'query': query,
        'normalized': normalized,
        'suggestedSlug': info['slug'],
        'type': info.get('type', 'profession'),
        'status': info.get('status', ('mapped-existing' if info['existing'] else 'queued')),
        'reason': info['reason']
    }
    queue['items'].append(item)
    save_json(QUEUE_PATH, queue)
    return item, info, True


def generate_page(slug: str, title: str, group: str, companies: str, examples: str, intro: str):
    path = ROOT / slug / 'index.html'
    path.parent.mkdir(parents=True, exist_ok=True)
    html = f'''<!DOCTYPE html>
<html lang="da">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} | SimplySag</title>
  <meta name="description" content="{title} med styr på timer, materialer, billeder og medarbejdere. SimplySag er lavet til små danske {companies}. Fra 199 kr/md.">
  <meta name="robots" content="index,follow">
  <link rel="canonical" href="https://simplysag.dk/{slug}/">
  <link rel="stylesheet" href="/tailwind.min.css">
</head>
<body class="bg-slate-50 text-slate-800 antialiased">
  <main class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16">
    <a href="/" class="inline-flex items-center text-sm font-medium text-blue-700 hover:underline mb-8">← Tilbage til forsiden</a>
    <header class="mb-12">
      <span class="inline-flex items-center rounded-full bg-blue-100 text-blue-800 text-xs font-semibold px-3 py-1 mb-4">Branche</span>
      <h1 class="text-4xl sm:text-5xl font-extrabold tracking-tight text-slate-900 mb-5">{title}</h1>
      <p class="text-lg text-slate-600 max-w-3xl leading-relaxed">{intro}</p>
    </header>
    <section class="bg-white border border-slate-200 rounded-3xl p-8 shadow-sm mb-10">
      <h2 class="text-2xl font-bold text-slate-900 mb-4">Hvorfor er det relevant for {group}?</h2>
      <p class="text-slate-700 leading-relaxed mb-4">Mange {companies} arbejder med flere små og mellemstore opgaver ad gangen. Når oplysninger om kunde, adresse, billeder, materialer og timer ligger forskellige steder, bliver det svært at bevare overblikket.</p>
      <p class="text-slate-700 leading-relaxed">SimplySag samler det daglige arbejde ét sted og gør det lettere at følge {examples} uden at bygge tunge processer omkring det.</p>
    </section>
    <section class="grid sm:grid-cols-2 gap-6 mb-10">
      <div class="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
        <h2 class="text-xl font-bold text-slate-900 mb-3">Det du typisk skal holde styr på</h2>
        <ul class="space-y-3 text-sm text-slate-700 leading-relaxed">
          <li>aktive sager og status på dem</li>
          <li>hvem der arbejder hvor og hvornår</li>
          <li>timer registreret ude på opgaven</li>
          <li>materialer og billeddokumentation</li>
        </ul>
      </div>
      <div class="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm">
        <h2 class="text-xl font-bold text-slate-900 mb-3">Det SimplySag hjælper med</h2>
        <ul class="space-y-3 text-sm text-slate-700 leading-relaxed">
          <li>sagsstyring på telefon, tablet og computer</li>
          <li>timeregistrering direkte fra marken</li>
          <li>billeder og noter samlet på sagen</li>
          <li>enkelt setup til små teams</li>
        </ul>
      </div>
    </section>
    <section class="bg-blue-950 text-white rounded-3xl p-8 sm:p-10">
      <h2 class="text-2xl font-bold mb-3">Vil du prøve SimplySag i din virksomhed?</h2>
      <p class="text-blue-100 max-w-2xl mb-6 leading-relaxed">Du kan oprette dig og teste systemet med dine egne kunder, sager og medarbejdere. Det tager ikke lang tid at finde ud af, om det passer til din hverdag.</p>
      <div class="flex flex-wrap gap-4">
        <a href="https://simplysag-app.web.app" class="inline-flex items-center justify-center rounded-xl bg-orange-500 hover:bg-orange-600 text-white font-semibold px-6 py-3">Start gratis i 30 dage</a>
      </div>
    </section>
  </main>
</body>
</html>
'''
    path.write_text(html)
    return path


def add_to_sitemap(slug: str):
    text = SITEMAP_PATH.read_text()
    loc = f"https://simplysag.dk/{slug}/"
    if loc in text:
        return False
    insertion = f"  <url>\n    <loc>{loc}</loc>\n    <lastmod>{date.today().isoformat()}</lastmod>\n    <changefreq>weekly</changefreq>\n    <priority>0.8</priority>\n  </url>\n"
    text = text.replace('</urlset>', insertion + '</urlset>')
    SITEMAP_PATH.write_text(text)
    return True


def add_to_llms(slug: str, title: str):
    line = f"- /{slug}/ — {title}"
    text = LLMS_PATH.read_text()
    if line in text:
        return False
    text += f"\n{line}\n"
    LLMS_PATH.write_text(text)
    return True


def main():
    parser = argparse.ArgumentParser(description='Semi-automatic SEO page workflow for simplysag.dk')
    sub = parser.add_subparsers(dest='command', required=True)

    q = sub.add_parser('queue-query', help='Map a search query and add it to the queue if missing')
    q.add_argument('query')

    p = sub.add_parser('publish-profession', help='Generate and register a profession page')
    p.add_argument('--slug', required=True)
    p.add_argument('--title', required=True)
    p.add_argument('--group', required=True)
    p.add_argument('--companies', required=True)
    p.add_argument('--examples', required=True)
    p.add_argument('--intro', required=True)

    args = parser.parse_args()

    if args.command == 'queue-query':
        item, info, created = ensure_queue_item(args.query)
        print(json.dumps({'created': created, 'queueItem': item, 'match': info}, ensure_ascii=False, indent=2))
        return

    if args.command == 'publish-profession':
        path = generate_page(args.slug, args.title, args.group, args.companies, args.examples, args.intro)
        add_to_sitemap(args.slug)
        add_to_llms(args.slug, args.title)
        print(json.dumps({'generated': str(path), 'slug': args.slug, 'title': args.title}, ensure_ascii=False, indent=2))
        return


if __name__ == '__main__':
    main()
