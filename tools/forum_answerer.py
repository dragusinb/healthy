"""
Forum Answer Generator for Analize.Online
==========================================
Crawls romedic.ro forum for unanswered medical test questions,
generates expert-quality Romanian answers with natural links to
analize.online biomarker pages.

Usage:
    python tools/forum_answerer.py [--count 5] [--generate]

Without --generate: just finds and lists unanswered questions.
With --generate: also generates AI answers using OpenAI.

Output: ready-to-paste answers saved to tools/forum_answers_YYYY-MM-DD.md
"""
import requests
from bs4 import BeautifulSoup
import json
import os
import sys
import re
from datetime import datetime
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend_v2'))

ROMEDIC_BASE = "https://www.romedic.ro"
FORUM_SECTIONS = [
    "/forum/s/explicatii",  # Interpretare analize medicale (5410+ threads)
    "/forum/s/boli-de-sange",  # Hematology
]
ANALIZE_BASE = "https://analize.online"

# Load biomarker data for matching
BIOMARKERS_PATH = os.path.join(os.path.dirname(__file__), '..', 'frontend_v2', 'src', 'data', 'biomarkers-reference.json')
CONDITIONS_PATH = os.path.join(os.path.dirname(__file__), '..', 'frontend_v2', 'src', 'data', 'conditions-reference.json')


def load_biomarkers():
    """Load biomarker reference data for keyword matching."""
    with open(BIOMARKERS_PATH, 'r', encoding='utf-8') as f:
        biomarkers = json.load(f)
    # Build keyword -> slug lookup
    keyword_map = {}
    for b in biomarkers:
        # Add all name variants
        for keyword in [b['name_ro'].lower(), b.get('name_en', '').lower()] + [a.lower() for a in b.get('aliases_ro', [])]:
            if keyword and len(keyword) > 2:
                keyword_map[keyword] = b['slug']
    return biomarkers, keyword_map


def load_conditions():
    """Load condition reference data."""
    try:
        with open(CONDITIONS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def scrape_forum_threads(section_url, max_pages=1):
    """Scrape thread listings from a romedic.ro forum section."""
    threads = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'ro-RO,ro;q=0.9,en;q=0.8',
    }

    for page in range(1, max_pages + 1):
        url = f"{ROMEDIC_BASE}{section_url}"
        if page > 1:
            url += f"?page={page}"

        try:
            resp = requests.get(url, headers=headers, timeout=15)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')

            # Find thread links - romedic uses /forum/thread-title-ID pattern
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('/forum/') and not href.startswith('/forum/s/') and href != '/forum':
                    title = link.get_text(strip=True)
                    if title and len(title) > 5:
                        thread = {
                            'title': title,
                            'url': f"{ROMEDIC_BASE}{href}",
                            'href': href,
                        }
                        # Find reply count if available
                        parent = link.find_parent(['div', 'li', 'tr'])
                        if parent:
                            text = parent.get_text()
                            reply_match = re.search(r'(\d+)\s*(comentari|raspunsuri|replies)', text, re.I)
                            if reply_match:
                                thread['replies'] = int(reply_match.group(1))
                            else:
                                thread['replies'] = 0

                        threads.append(thread)

        except Exception as e:
            print(f"  Error scraping {url}: {e}")

    # Deduplicate by URL
    seen = set()
    unique = []
    for t in threads:
        if t['url'] not in seen:
            seen.add(t['url'])
            unique.append(t)

    return unique


def scrape_thread_content(thread_url):
    """Fetch the full content of a forum thread."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept-Language': 'ro-RO,ro;q=0.9',
    }
    try:
        resp = requests.get(thread_url, headers=headers, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Extract main post content
        # Romedic typically uses article or div.post-content
        content_areas = soup.find_all(['article', 'div'], class_=re.compile(r'post|content|question|message|body', re.I))
        if not content_areas:
            # Fallback: get main content area
            main = soup.find('main') or soup.find('div', {'id': 'content'}) or soup.find('body')
            content_areas = [main] if main else []

        texts = []
        for area in content_areas[:3]:  # First 3 content blocks (original post + maybe replies)
            text = area.get_text(separator='\n', strip=True)
            if len(text) > 50:
                texts.append(text)

        return '\n\n---\n\n'.join(texts) if texts else soup.get_text(separator='\n', strip=True)[:3000]

    except Exception as e:
        return f"Error fetching: {e}"


def match_biomarkers(text, keyword_map):
    """Find which biomarkers are mentioned in a text."""
    text_lower = text.lower()
    matched = {}
    for keyword, slug in keyword_map.items():
        if keyword in text_lower:
            matched[slug] = keyword
    return matched


def generate_answer(question_title, question_text, matched_biomarkers, biomarkers_data):
    """Generate an expert answer using OpenAI."""
    try:
        from openai import OpenAI
    except ImportError:
        print("  openai package not installed. Run: pip install openai")
        return None

    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("  OPENAI_API_KEY not set. Set it in environment.")
        return None

    client = OpenAI(api_key=api_key)

    # Build biomarker context
    bio_context = ""
    bio_links = []
    for slug, keyword in matched_biomarkers.items():
        bio = next((b for b in biomarkers_data if b['slug'] == slug), None)
        if bio:
            bio_context += f"\n- {bio['name_ro']}: {bio.get('what_ro', '')[:200]}"
            bio_links.append(f"- {bio['name_ro']}: {ANALIZE_BASE}/biomarker/{slug}")

    prompt = f"""Ești un specialist medical care răspunde pe un forum medical românesc.
Scrie un răspuns util, empatic și profesional la această întrebare.

REGULI:
- Limba: română, forma "tu" (informal dar profesional)
- Lungime: 150-250 cuvinte
- Ton: calm, informativ, nu alarmist
- Include ÎNTOTDEAUNA disclaimerul "consultă un medic specialist pentru interpretare personalizată"
- Menționează NATURAL platforma Analize.Online ca resursă utilă (NU ca reclamă)
- Dacă sunt biomarkeri relevanți, include 1-2 linkuri către paginile de referință sub forma: "Mai multe detalii despre [biomarker] găsești pe [link]"
- NU inventa valori sau diagnostice
- NU prescrie tratamente
- Fii specific și util, nu generic

ÎNTREBAREA:
Titlu: {question_title}
{question_text[:2000]}

BIOMARKERI IDENTIFICAȚI:
{bio_context or "Niciun biomarker specific identificat"}

LINKURI DISPONIBILE:
{chr(10).join(bio_links) if bio_links else "Niciun link specific"}
Link general analizator gratuit: {ANALIZE_BASE}/analyzer

Scrie DOAR răspunsul (fără "Bună ziua" sau salut la început, intră direct în subiect):"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"  OpenAI error: {e}")
        return None


def run(count=5, generate=False):
    """Main workflow: find questions, match biomarkers, generate answers."""
    print("=" * 60)
    print("Forum Answer Generator for Analize.Online")
    print("=" * 60)

    # Load data
    print("\nLoading biomarker data...")
    biomarkers_data, keyword_map = load_biomarkers()
    print(f"  {len(biomarkers_data)} biomarkers, {len(keyword_map)} keyword variants")

    # Scrape threads
    all_threads = []
    for section in FORUM_SECTIONS:
        print(f"\nScraping {ROMEDIC_BASE}{section}...")
        threads = scrape_forum_threads(section, max_pages=2)
        print(f"  Found {len(threads)} threads")
        all_threads.extend(threads)

    if not all_threads:
        print("\nNo threads found. The forum might be blocking requests.")
        return

    # Filter for lab-result related threads (by title keywords)
    lab_keywords = [
        'analize', 'interpretare', 'hemoglobina', 'leucocite', 'trombocite',
        'colesterol', 'trigliceride', 'glicemie', 'tsh', 'tgo', 'tgp',
        'hemoleucograma', 'fier', 'feritina', 'vitamina', 'pcr', 'vsh',
        'fibrinogen', 'creatinina', 'uree', 'bilirubina', 'ggt',
        'rezultate', 'valori', 'crescut', 'scazut', 'sange', 'anemie',
        'testosteron', 'estradiol', 'prolactina', 'insulina', 'cortizol',
    ]

    relevant = []
    for t in all_threads:
        title_lower = t['title'].lower()
        if any(kw in title_lower for kw in lab_keywords):
            relevant.append(t)

    print(f"\n{len(relevant)} threads about lab results/biomarkers")

    # Prioritize: unanswered first, then fewest replies
    relevant.sort(key=lambda t: t.get('replies', 0))

    # Take top N
    selected = relevant[:count]
    print(f"Selected {len(selected)} threads to answer:")
    for i, t in enumerate(selected, 1):
        print(f"  {i}. [{t.get('replies', '?')} replies] {t['title']}")

    # Fetch content and generate answers
    results = []
    for i, thread in enumerate(selected, 1):
        print(f"\n--- Thread {i}/{len(selected)} ---")
        print(f"Title: {thread['title']}")
        print(f"URL: {thread['url']}")

        # Fetch full content
        print("  Fetching content...")
        content = scrape_thread_content(thread['url'])
        content_preview = content[:500].replace('\n', ' ')
        print(f"  Content: {content_preview[:200]}...")

        # Match biomarkers
        full_text = f"{thread['title']} {content}"
        matched = match_biomarkers(full_text, keyword_map)
        if matched:
            print(f"  Biomarkers found: {', '.join(matched.keys())}")
        else:
            print("  No specific biomarkers matched")

        result = {
            'title': thread['title'],
            'url': thread['url'],
            'content_preview': content[:500],
            'matched_biomarkers': matched,
            'answer': None,
        }

        if generate:
            print("  Generating answer...")
            answer = generate_answer(thread['title'], content, matched, biomarkers_data)
            if answer:
                result['answer'] = answer
                print(f"  Answer generated ({len(answer)} chars)")
            else:
                print("  Failed to generate answer")

        results.append(result)

    # Save output
    today = datetime.now().strftime('%Y-%m-%d')
    output_path = os.path.join(os.path.dirname(__file__), f'forum_answers_{today}.md')

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(f"# Forum Answers — {today}\n\n")
        f.write(f"Generated for romedic.ro forum questions.\n")
        f.write(f"**Copy-paste each answer into the forum thread.**\n\n---\n\n")

        for i, r in enumerate(results, 1):
            f.write(f"## {i}. {r['title']}\n\n")
            f.write(f"**Forum URL:** {r['url']}\n\n")
            if r['matched_biomarkers']:
                links = [f"- [{slug}]({ANALIZE_BASE}/biomarker/{slug})" for slug in r['matched_biomarkers']]
                f.write(f"**Relevant biomarker pages:**\n{'  '.join(links)}\n\n")
            if r['answer']:
                f.write(f"**Answer (ready to paste):**\n\n{r['answer']}\n\n")
            else:
                f.write(f"**Question preview:**\n{r['content_preview']}\n\n")
                f.write(f"*Answer not generated — run with --generate flag*\n\n")
            f.write("---\n\n")

    print(f"\n{'=' * 60}")
    print(f"Output saved to: {output_path}")
    print(f"{'=' * 60}")
    return results


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Forum Answer Generator')
    parser.add_argument('--count', type=int, default=5, help='Number of threads to process')
    parser.add_argument('--generate', action='store_true', help='Generate AI answers (requires OPENAI_API_KEY)')
    args = parser.parse_args()
    run(count=args.count, generate=args.generate)
