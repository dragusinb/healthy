#!/usr/bin/env python3
"""
Prospect Finder Tool for Analize.Online
Finds and enriches potential partners/buyers in Romanian health/medtech/insurance.
Uses public web sources only — no email scraping.

Usage:
    python sale/find_prospects.py                  # Full run: search + enrich + report
    python sale/find_prospects.py --enrich-only    # Skip search, enrich seed list only
    python sale/find_prospects.py --no-search      # Same as --enrich-only
    python sale/find_prospects.py --output report  # Output format: report (md) or json
"""

import argparse
import io
import json
import os
import re
import sys
import time

# Fix Windows console encoding for emoji/unicode
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SEARCH_QUERIES = [
    "health tech romania startup",
    "corporate wellness romania platforma",
    "asigurari sanatate romania digital",
    "platforme medicale romania",
    "telemedicina romania startup",
    "medtech romania",
    "digital health romania",
    "wellness angajati romania",
    "insurtech romania",
    "laborator analize romania online",
    "sanatate digitala romania",
    "health insurance romania innovation",
    "employee benefits romania platform",
    "clinic management software romania",
]

# Keywords that signal a good fit for partnership/integration
FIT_KEYWORDS = {
    5: ["analize", "laborator", "biomarker", "lab results", "rezultate analize",
        "agregare date medicale", "health data aggregation"],
    4: ["patient portal", "portal pacient", "wellness angajati", "employee wellness",
        "corporate wellness", "sanatate digitala", "digital health", "telemedicina",
        "telehealth"],
    3: ["asigurare sanatate", "health insurance", "insurtech", "medtech",
        "beneficii angajati", "employee benefits", "clinic", "spital", "hospital"],
    2: ["healthtech", "health tech", "preventie", "prevention", "fitness",
        "wearable", "monitoring sanatate"],
    1: ["startup romania", "investitii tech", "vc romania", "angel investor"],
}

PARTNERSHIP_SIGNALS = [
    "partners", "parteneri", "parteneriate",
    "api", "integrations", "integrari",
    "developers", "dezvoltatori",
    "white-label", "whitelabel", "b2b",
    "enterprise", "solutions",
]

CATEGORIES = {
    "healthcare_provider": ["medlife", "regina maria", "medicover", "sanador", "medpark",
                            "clinic", "spital", "hospital", "laborator", "lab"],
    "insurance": ["asigur", "insurance", "polita", "underwriting", "actuar"],
    "corporate_wellness": ["wellness", "beneficii", "benefits", "hr ", "angajat",
                           "employee", "sanopass", "7card"],
    "medtech": ["medtech", "healthtech", "health tech", "telemedicin", "telehealth",
                "digital health", "sanatate digital"],
    "vc_investor": ["venture", "capital", "invest", "angel", "fund", "fond",
                    "seedblink", "crowdfunding"],
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7",
}

OUTPUT_DIR = Path(__file__).parent


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Prospect:
    name: str
    website: str
    description: str = ""
    category: str = "unknown"
    fit_score: int = 0
    approach: str = ""
    contact_url: str = ""
    linkedin_url: str = ""
    team_page_url: str = ""
    key_people: list = field(default_factory=list)
    has_partner_page: bool = False
    partner_signals: list = field(default_factory=list)
    notes: str = ""
    source: str = "seed"  # seed | search

    def to_dict(self):
        return asdict(self)


# ---------------------------------------------------------------------------
# Seed list — from target-list-ro.md
# ---------------------------------------------------------------------------

SEED_PROSPECTS = [
    # Tier 1: Healthcare Providers
    Prospect("MedLife", "https://www.medlife.ro", category="healthcare_provider",
             approach="Licensing — crawler already works, integrate into their patient portal",
             notes="Cel mai mare grup privat de sănătate din RO. Crawler MedLife funcțional."),
    Prospect("Regina Maria", "https://www.reginamaria.ro", category="healthcare_provider",
             approach="Licensing — crawler functional, patient portal upgrade",
             notes="Al doilea cel mai mare. Crawler RM funcțional."),
    Prospect("Medicover", "https://www.medicover.ro", category="healthcare_provider",
             approach="Licensing — Nordic investor capital, digital expansion",
             notes="Investitor nordic, capital pentru achiziții tech."),
    Prospect("Sanador", "https://www.sanador.ro", category="healthcare_provider",
             approach="Licensing — premium positioning, luxury differentiator",
             notes="Crawler Sanador funcțional. Premium positioning."),
    Prospect("MedPark / Rețeaua Enayati", "https://www.medpark.ro", category="healthcare_provider",
             approach="Licensing — aggressive expansion, tech differentiation",
             notes="Expandare agresivă. Caută diferențiere prin tech."),

    # Tier 2: Insurance
    Prospect("NN Asigurări", "https://www.nn.ro", category="insurance",
             approach="Data licensing — predictive pricing, prevention programs",
             notes="Cel mai mare asigurător de viață din RO."),
    Prospect("Allianz-Țiriac", "https://www.allianztiriac.ro", category="insurance",
             approach="Data licensing — personalized health insurance offers",
             notes="Asigurări de sănătate. Date agregate = oferte personalizate."),
    Prospect("Generali România", "https://www.generali.ro", category="insurance",
             approach="Integration — prevention focus, corporate packages",
             notes="Focus pe prevenție, pachete corporate."),
    Prospect("Signal Iduna", "https://www.signaliduna.ro", category="insurance",
             approach="Integration — private health insurance addon",
             notes="Asigurări sănătate private."),
    Prospect("Groupama", "https://www.groupama.ro", category="insurance",
             approach="Integration — corporate health insurance segment",
             notes="Asigurări sănătate, segment corporate."),

    # Tier 3: Corporate Wellness
    Prospect("SanoPass", "https://www.sanopass.ro", category="corporate_wellness",
             approach="White-label — perfect fit, lab aggregation missing from their offer",
             notes="Platformă wellness angajați. Fit perfect pentru white-label."),
    Prospect("7card", "https://www.7card.ro", category="corporate_wellness",
             approach="Integration — employee benefits extension",
             notes="Beneficii angajați (fitness, medical)."),
    Prospect("Benefit Systems", "https://www.benefitsystems.ro", category="corporate_wellness",
             approach="Module integration — health module for benefits platform",
             notes="Platformă flexibilă de beneficii. Module medicale în expansiune."),
    Prospect("Smartree", "https://www.smartree.com", category="corporate_wellness",
             approach="White-label — health module for HR outsourcing clients",
             notes="HR outsourcing + beneficii."),

    # Tier 4: MedTech / VC
    Prospect("Doclandia", "https://www.doclandia.ro", category="medtech",
             approach="Partnership — lab results + telemedicine synergy",
             notes="MedTech startup RO (telemedicină). Sinergie directă."),
    Prospect("SeedBlink", "https://www.seedblink.com", category="vc_investor",
             approach="Investment — equity crowdfunding campaign",
             notes="Equity crowdfunding, focus tech/health."),
    Prospect("Sparking Capital", "https://www.sparkingcapital.com", category="vc_investor",
             approach="Investment — early-stage VC",
             notes="VC early-stage, investiții în RO."),
    Prospect("TechAngels România", "https://www.techangels.ro", category="vc_investor",
             approach="Investment — angel network",
             notes="Rețea de business angels, focus tech."),
    Prospect("GapMinder VC", "https://www.gapminder.vc", category="vc_investor",
             approach="Investment — regional VC, digital health focus",
             notes="VC regional, focus pe CEE."),
    Prospect("Catalyst România", "https://www.catalystromania.com", category="vc_investor",
             approach="Investment — local early-stage VC",
             notes="VC local, early stage."),

    # Additional from outreach templates
    Prospect("Cegeka Romania", "https://www.cegeka.com/ro", category="medtech",
             approach="Partnership — Health IT solutions provider",
             notes="Health IT solutions, potential tech partner."),
    Prospect("FintechOS", "https://www.fintechos.com", category="medtech",
             approach="Partnership — insurtech expansion into health",
             notes="Insure-tech expansion, could integrate health data."),
    Prospect("DIGI / RCS&RDS", "https://www.digi.ro", category="medtech",
             approach="Licensing — Digi Health vertical",
             notes="Exploring health vertical (Digi Health)."),
]


# ---------------------------------------------------------------------------
# Web fetching helpers
# ---------------------------------------------------------------------------

def fetch_page(url: str, client: httpx.Client, timeout: float = 15.0) -> Optional[str]:
    """Fetch a URL and return its HTML content, or None on failure."""
    try:
        resp = client.get(url, timeout=timeout, follow_redirects=True)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"  ⚠ Could not fetch {url}: {e}")
        return None


def extract_text(html: str) -> str:
    """Extract visible text from HTML."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
        tag.decompose()
    return soup.get_text(separator=" ", strip=True).lower()


def find_links(html: str, base_url: str) -> dict:
    """Find relevant links on a page (contact, about, partners, API, team)."""
    soup = BeautifulSoup(html, "html.parser")
    results = {
        "contact": [],
        "about": [],
        "team": [],
        "partners": [],
        "api": [],
        "linkedin": [],
    }

    link_patterns = {
        "contact": re.compile(r"contact|contacteaza|contactează", re.I),
        "about": re.compile(r"about|despre|who.we.are|cine.suntem", re.I),
        "team": re.compile(r"team|echipa|echipă|leadership|management", re.I),
        "partners": re.compile(r"partner|partener|parteneri|integration|integrari|integrar", re.I),
        "api": re.compile(r"\bapi\b|developer|dezvoltat", re.I),
    }

    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get("href", "")
        text = a_tag.get_text(strip=True).lower()
        combined = f"{href} {text}"

        # LinkedIn
        if "linkedin.com/company" in href:
            results["linkedin"].append(href)
            continue

        for category, pattern in link_patterns.items():
            if pattern.search(combined):
                full_url = urljoin(base_url, href)
                if full_url not in results[category]:
                    results[category].append(full_url)

    return results


def extract_meta_description(html: str) -> str:
    """Extract meta description from HTML."""
    soup = BeautifulSoup(html, "html.parser")
    meta = soup.find("meta", attrs={"name": "description"})
    if meta and meta.get("content"):
        return meta["content"].strip()
    og_desc = soup.find("meta", attrs={"property": "og:description"})
    if og_desc and og_desc.get("content"):
        return og_desc["content"].strip()
    return ""


def extract_people_from_team_page(html: str) -> list:
    """Try to extract names and roles from a team/about page."""
    soup = BeautifulSoup(html, "html.parser")
    people = []

    # Common patterns: cards with name + role
    role_keywords = re.compile(
        r"(CEO|CTO|CPO|COO|CFO|CMO|Director|Manager|Head|VP|Fondator|Founder|"
        r"Partner|Lead|Chief|President|Președinte)", re.I
    )

    # Look for structured team elements
    for container in soup.find_all(["div", "article", "li", "section"],
                                     class_=re.compile(r"team|member|person|staff|echipa", re.I)):
        texts = container.get_text(separator="\n", strip=True).split("\n")
        texts = [t.strip() for t in texts if t.strip() and len(t.strip()) > 2]
        for i, text in enumerate(texts):
            if role_keywords.search(text):
                # The name is usually right before the role
                name = texts[i - 1] if i > 0 and len(texts[i - 1]) < 60 else ""
                if name and not role_keywords.search(name):
                    people.append(f"{name} ({text})")
                else:
                    people.append(text)

    # Deduplicate
    seen = set()
    unique = []
    for p in people:
        if p not in seen:
            seen.add(p)
            unique.append(p)

    return unique[:10]  # Cap at 10


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def compute_fit_score(text: str, company_name: str) -> int:
    """Compute fit score 1-5 based on keyword matching."""
    text_lower = text.lower()
    max_score = 1

    for score, keywords in FIT_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                max_score = max(max_score, score)

    return max_score


def detect_category(text: str, current_category: str) -> str:
    """Detect company category from website text."""
    if current_category != "unknown":
        return current_category

    text_lower = text.lower()
    scores = {}
    for cat, keywords in CATEGORIES.items():
        scores[cat] = sum(1 for kw in keywords if kw in text_lower)

    best_cat = max(scores, key=scores.get)
    return best_cat if scores[best_cat] > 0 else "unknown"


def detect_partner_signals(text: str) -> list:
    """Check if company website mentions partnerships/APIs/integrations."""
    found = []
    text_lower = text.lower()
    for signal in PARTNERSHIP_SIGNALS:
        if signal in text_lower:
            found.append(signal)
    return found


# ---------------------------------------------------------------------------
# Google search via googlesearch-python
# ---------------------------------------------------------------------------

def search_duckduckgo(query: str, client: httpx.Client, max_results: int = 10) -> list:
    """Search DuckDuckGo HTML version. Returns list of URLs."""
    urls = []
    try:
        resp = client.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            timeout=15.0,
            follow_redirects=True,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for a_tag in soup.find_all("a", class_="result__a", href=True):
            href = a_tag["href"]
            # DuckDuckGo wraps URLs in redirects
            if "uddg=" in href:
                from urllib.parse import parse_qs
                parsed = parse_qs(urlparse(href).query)
                if "uddg" in parsed:
                    href = parsed["uddg"][0]
            if href.startswith("http"):
                urls.append(href)
            if len(urls) >= max_results:
                break
    except Exception as e:
        print(f"    ⚠ DuckDuckGo search failed: {e}")
    return urls


def search_google(queries: list, max_results_per_query: int = 10) -> list:
    """Search for companies using Google (primary) and DuckDuckGo (fallback).
    Returns list of (url, query) tuples."""
    google_available = False
    try:
        from googlesearch import search as gsearch
        google_available = True
    except ImportError:
        print("  ⚠ googlesearch-python not installed, using DuckDuckGo only.")

    results = []
    seen_domains = set()
    ddg_client = httpx.Client(headers=HEADERS, follow_redirects=True)

    for query in queries:
        print(f"  🔍 Searching: {query}")
        found_urls = []

        # Try Google first
        if google_available:
            try:
                for url in gsearch(query, num_results=max_results_per_query, lang="ro"):
                    found_urls.append(url)
                time.sleep(2)
            except Exception as e:
                print(f"    ⚠ Google failed: {e}")

        # Fallback to DuckDuckGo if Google returned nothing
        if not found_urls:
            found_urls = search_duckduckgo(query, ddg_client, max_results_per_query)
            if found_urls:
                print(f"    (via DuckDuckGo: {len(found_urls)} results)")
            time.sleep(1)

        for url in found_urls:
            domain = urlparse(url).netloc.replace("www.", "")
            if domain not in seen_domains:
                seen_domains.add(domain)
                results.append((url, query))

    ddg_client.close()
    return results


def url_to_prospect(url: str, query: str, client: httpx.Client) -> Optional[Prospect]:
    """Fetch a URL and create a Prospect from it."""
    domain = urlparse(url).netloc.replace("www.", "")

    # Skip irrelevant domains
    skip_domains = [
        "linkedin.com", "facebook.com", "twitter.com", "instagram.com",
        "youtube.com", "wikipedia.org", "google.com", "gov.ro",
        "reddit.com", "medium.com", "forbes.com", "zf.ro", "profit.ro",
        "wall-street.ro", "economica.net", "startupcafe.ro", "romania-insider.com",
        "analize.online",  # ourselves
    ]
    if any(skip in domain for skip in skip_domains):
        return None

    html = fetch_page(url, client)
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(strip=True) if soup.title else domain
    description = extract_meta_description(html)
    text = extract_text(html)

    # Skip if too short (likely blocked/redirect)
    if len(text) < 100:
        return None

    name = title.split("|")[0].split("-")[0].split("–")[0].strip()
    if len(name) > 80:
        name = domain.split(".")[0].capitalize()

    base_url = f"https://{urlparse(url).netloc}"

    prospect = Prospect(
        name=name,
        website=base_url,
        description=description[:300] if description else "",
        source="search",
    )

    # Categorize and score
    combined_text = f"{name} {description} {text[:2000]}"
    prospect.category = detect_category(combined_text, "unknown")
    prospect.fit_score = compute_fit_score(combined_text, name)
    prospect.partner_signals = detect_partner_signals(combined_text)
    prospect.has_partner_page = len(prospect.partner_signals) > 0

    return prospect


# ---------------------------------------------------------------------------
# Enrichment — fetch company websites and extract info
# ---------------------------------------------------------------------------

def enrich_prospect(prospect: Prospect, client: httpx.Client) -> Prospect:
    """Enrich a prospect by visiting their website."""
    print(f"  📋 Enriching: {prospect.name} ({prospect.website})")

    html = fetch_page(prospect.website, client)
    if not html:
        # Still apply minimum scores for seed prospects even if fetch failed
        if prospect.source == "seed":
            category_minimums = {
                "healthcare_provider": 4, "insurance": 3,
                "corporate_wellness": 3, "medtech": 3, "vc_investor": 2,
            }
            prospect.fit_score = max(prospect.fit_score,
                                     category_minimums.get(prospect.category, 2))
        return prospect

    text = extract_text(html)
    links = find_links(html, prospect.website)

    # Description
    if not prospect.description:
        prospect.description = extract_meta_description(html)

    # Contact page
    if links["contact"]:
        prospect.contact_url = links["contact"][0]

    # LinkedIn
    if links["linkedin"]:
        prospect.linkedin_url = links["linkedin"][0]

    # Team page
    if links["team"] or links["about"]:
        team_urls = links["team"] or links["about"]
        prospect.team_page_url = team_urls[0]

        # Try to extract people from team page
        team_html = fetch_page(team_urls[0], client)
        if team_html:
            people = extract_people_from_team_page(team_html)
            if people:
                prospect.key_people = people

    # Partner signals
    combined_text = f"{prospect.description} {text[:3000]}"
    signals = detect_partner_signals(combined_text)
    if signals:
        prospect.partner_signals = list(set(prospect.partner_signals + signals))
        prospect.has_partner_page = True

    # Update fit score with enriched data
    web_score = compute_fit_score(combined_text, prospect.name)
    if web_score > prospect.fit_score:
        prospect.fit_score = web_score

    # Seed prospects get a minimum score based on category (manually curated = higher trust)
    if prospect.source == "seed":
        category_minimums = {
            "healthcare_provider": 4,
            "insurance": 3,
            "corporate_wellness": 3,
            "medtech": 3,
            "vc_investor": 2,
        }
        min_score = category_minimums.get(prospect.category, 2)
        prospect.fit_score = max(prospect.fit_score, min_score)

    # Update category
    prospect.category = detect_category(combined_text, prospect.category)

    # Generate approach suggestion if missing
    if not prospect.approach:
        prospect.approach = suggest_approach(prospect)

    return prospect


def suggest_approach(prospect: Prospect) -> str:
    """Suggest an approach based on company category and signals."""
    approaches = {
        "healthcare_provider": "Licensing — white-label lab aggregation for their patient portal",
        "insurance": "Data licensing — health data insights for risk assessment and prevention",
        "corporate_wellness": "White-label — add lab result aggregation to employee wellness platform",
        "medtech": "Partnership — integrate lab data into their health tech solution",
        "vc_investor": "Investment — pitch for seed/pre-seed funding to scale",
        "unknown": "Exploratory — schedule discovery call to identify synergies",
    }
    return approaches.get(prospect.category, approaches["unknown"])


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

CATEGORY_LABELS = {
    "healthcare_provider": "Healthcare Providers",
    "insurance": "Insurance Companies",
    "corporate_wellness": "Corporate Wellness",
    "medtech": "MedTech / Digital Health",
    "vc_investor": "VC / Investors",
    "unknown": "Other / Unclassified",
}

CATEGORY_ORDER = [
    "healthcare_provider", "insurance", "corporate_wellness",
    "medtech", "vc_investor", "unknown",
]


def generate_markdown_report(prospects: list) -> str:
    """Generate a Markdown report from prospects."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        f"# Prospect Report — Analize.Online",
        f"",
        f"**Generated:** {now}",
        f"**Total prospects:** {len(prospects)}",
        f"",
        f"---",
        f"",
    ]

    # Summary table
    lines.append("## Summary\n")
    lines.append("| Category | Count | Avg Fit Score |")
    lines.append("|----------|-------|---------------|")

    by_category = {}
    for p in prospects:
        by_category.setdefault(p.category, []).append(p)

    for cat in CATEGORY_ORDER:
        if cat in by_category:
            plist = by_category[cat]
            avg = sum(p.fit_score for p in plist) / len(plist)
            label = CATEGORY_LABELS.get(cat, cat)
            lines.append(f"| {label} | {len(plist)} | {avg:.1f}/5 |")

    lines.append("")
    lines.append("---")
    lines.append("")

    # Detailed sections by category
    for cat in CATEGORY_ORDER:
        if cat not in by_category:
            continue

        label = CATEGORY_LABELS.get(cat, cat)
        plist = sorted(by_category[cat], key=lambda p: p.fit_score, reverse=True)

        lines.append(f"## {label}\n")

        for p in plist:
            stars = "⭐" * p.fit_score + "☆" * (5 - p.fit_score)
            lines.append(f"### {p.name}")
            lines.append(f"- **Website:** {p.website}")
            lines.append(f"- **Fit Score:** {stars} ({p.fit_score}/5)")

            if p.description:
                lines.append(f"- **Description:** {p.description}")

            lines.append(f"- **Approach:** {p.approach}")

            if p.contact_url:
                lines.append(f"- **Contact page:** {p.contact_url}")
            if p.linkedin_url:
                lines.append(f"- **LinkedIn:** {p.linkedin_url}")
            if p.team_page_url:
                lines.append(f"- **Team page:** {p.team_page_url}")
            if p.key_people:
                lines.append(f"- **Key people (public):** {', '.join(p.key_people[:5])}")
            if p.has_partner_page:
                lines.append(f"- **Partnership signals:** {', '.join(p.partner_signals)}")
            if p.notes:
                lines.append(f"- **Notes:** {p.notes}")

            lines.append(f"- **Source:** {p.source}")
            lines.append("")

        lines.append("---\n")

    # Action items
    lines.append("## Recommended Next Steps\n")
    lines.append("### Week 1-2: Warm Up")
    lines.append("1. Polish LinkedIn profile — add analize.online to experience")
    lines.append("2. Post 2-3 LinkedIn posts about the product (see `sale/linkedin-posts-ro.md`)")
    lines.append("3. Review this report and mark top 5 priority prospects")
    lines.append("")
    lines.append("### Week 3-4: Outreach Wave 1 — Warm Channels")
    lines.append("1. Send personalized LinkedIn DMs to CTOs/CPOs at Tier 1 companies")
    lines.append("2. Use templates from `sale/email-templates-ro.md`")
    lines.append("3. Ask personal connections for intros")
    lines.append("4. **Goal:** Book 3-5 demo calls")
    lines.append("")
    lines.append("### Week 5-6: Outreach Wave 2 — Cold Channels")
    lines.append("1. Email pitches via contact forms found above")
    lines.append("2. Attend Romanian health-tech meetups and startup events")
    lines.append("3. **Goal:** Book 3-5 more demo calls")
    lines.append("")
    lines.append("### Week 7-8: Demo & Negotiate")
    lines.append("1. Demo flow: pitch.html → live demo on analize.online → tech summary PDF")
    lines.append("2. Present 3 options: acquisition / licensing / revenue share")
    lines.append("3. Follow-up cadence: Day 1 → Day 3 → Day 7 → Day 14")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("*Report generated by `sale/find_prospects.py`*")

    return "\n".join(lines)


def generate_json_output(prospects: list) -> str:
    """Generate JSON output from prospects."""
    return json.dumps(
        [p.to_dict() for p in prospects],
        indent=2,
        ensure_ascii=False,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Prospect Finder for Analize.Online")
    parser.add_argument("--enrich-only", "--no-search", action="store_true",
                        help="Skip Google search, enrich seed list only")
    parser.add_argument("--output", choices=["report", "json", "both"], default="both",
                        help="Output format (default: both)")
    parser.add_argument("--max-search-results", type=int, default=8,
                        help="Max results per search query (default: 8)")
    args = parser.parse_args()

    print("=" * 60)
    print("  Prospect Finder — Analize.Online")
    print("=" * 60)

    prospects = list(SEED_PROSPECTS)  # Start with seed list
    seed_domains = {urlparse(p.website).netloc.replace("www.", "") for p in prospects}

    client = httpx.Client(headers=HEADERS, follow_redirects=True)

    # Step 1: Google search for new companies
    if not args.enrich_only:
        print(f"\n📡 Step 1: Searching for companies ({len(SEARCH_QUERIES)} queries)...")
        search_results = search_google(SEARCH_QUERIES, args.max_search_results)
        print(f"  Found {len(search_results)} unique URLs")

        new_count = 0
        for url, query in search_results:
            domain = urlparse(url).netloc.replace("www.", "")
            if domain in seed_domains:
                continue
            seed_domains.add(domain)

            prospect = url_to_prospect(url, query, client)
            if prospect and prospect.fit_score >= 2:
                prospects.append(prospect)
                new_count += 1
                print(f"    ✅ New prospect: {prospect.name} (score: {prospect.fit_score})")

            time.sleep(1)  # Be polite

        print(f"  Added {new_count} new prospects from search")
    else:
        print("\n>> Skipping search (--enrich-only mode)")

    # Step 2: Enrich all prospects
    print(f"\n📋 Step 2: Enriching {len(prospects)} prospects...")
    for i, prospect in enumerate(prospects):
        try:
            enrich_prospect(prospect, client)
        except Exception as e:
            print(f"  ⚠ Error enriching {prospect.name}: {e}")
        time.sleep(0.5)  # Be polite

    client.close()

    # Step 3: Sort by fit score
    prospects.sort(key=lambda p: (-p.fit_score, p.category, p.name))

    # Step 4: Generate outputs
    print(f"\n📄 Step 3: Generating reports...")

    if args.output in ("report", "both"):
        report = generate_markdown_report(prospects)
        report_path = OUTPUT_DIR / "prospects_report.md"
        report_path.write_text(report, encoding="utf-8")
        print(f"  ✅ Markdown report: {report_path}")

    if args.output in ("json", "both"):
        json_output = generate_json_output(prospects)
        json_path = OUTPUT_DIR / "prospects_data.json"
        json_path.write_text(json_output, encoding="utf-8")
        print(f"  ✅ JSON data: {json_path}")

    # Summary
    print(f"\n{'=' * 60}")
    print(f"  Done! {len(prospects)} prospects found and enriched.")
    print(f"{'=' * 60}")

    by_cat = {}
    for p in prospects:
        by_cat.setdefault(p.category, []).append(p)
    for cat in CATEGORY_ORDER:
        if cat in by_cat:
            label = CATEGORY_LABELS.get(cat, cat)
            print(f"  {label}: {len(by_cat[cat])}")

    high_fit = [p for p in prospects if p.fit_score >= 4]
    print(f"\n  🎯 High-fit prospects (score ≥ 4): {len(high_fit)}")
    for p in high_fit:
        print(f"    - {p.name} ({p.fit_score}/5) — {p.approach}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
