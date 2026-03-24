#!/usr/bin/env python3
"""
Prospect Finder Tool for Analize.Online — People-First Edition

Finds real decision-makers (CTOs, CEOs, Heads of Digital/Product) at Romanian
health/medtech/insurance/wellness companies. Outputs actionable contact lists
with LinkedIn profiles, not generic company pages.

Sources: DuckDuckGo search, company team pages, LinkedIn public profiles.

Usage:
    python sale/find_prospects.py                  # Full run
    python sale/find_prospects.py --enrich-only    # Enrich seed list only
    python sale/find_prospects.py --people-only    # Only search for people (skip company discovery)
"""

import argparse
import io
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin, urlparse, parse_qs, quote_plus

import httpx
from bs4 import BeautifulSoup

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

OUTPUT_DIR = Path(__file__).parent

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "ro-RO,ro;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# ---------------------------------------------------------------------------
# Data models — people-first
# ---------------------------------------------------------------------------

@dataclass
class Person:
    """A real decision-maker who can be contacted."""
    name: str
    title: str                    # CEO, CTO, Head of Digital, etc.
    company: str                  # Company they work at
    linkedin_url: str = ""        # Direct LinkedIn profile URL
    source: str = ""              # Where we found them (team page, search, manual)
    relevance: str = ""           # Why talk to THIS person specifically
    message_angle: str = ""       # Personalized opening line idea
    verified: bool = False        # Manually confirmed as accurate

    def to_dict(self):
        return asdict(self)


@dataclass
class Company:
    """A target company with its people."""
    name: str
    website: str
    category: str = "unknown"     # healthcare_provider, insurance, wellness, medtech, vc
    fit_score: int = 0            # 1-5
    why_fit: str = ""             # One sentence: why this company specifically
    approach: str = ""            # licensing / acquisition / partnership / investment
    people: list = field(default_factory=list)  # List of Person dicts
    linkedin_company: str = ""    # Company LinkedIn page
    contact_url: str = ""
    description: str = ""
    notes: str = ""

    def to_dict(self):
        d = asdict(self)
        return d


# ---------------------------------------------------------------------------
# Seed data — real companies with known people
# ---------------------------------------------------------------------------

SEED_COMPANIES = [
    # === TIER 1: Healthcare Providers (crawlers already work) ===
    Company(
        "MedLife", "https://www.medlife.ro",
        category="healthcare_provider", fit_score=5,
        why_fit="Crawler MedLife already functional. Largest private health group in RO.",
        approach="licensing",
        linkedin_company="https://www.linkedin.com/company/sc-medlife-sa/",
        people=[
            Person("Mihai Marcu", "CEO & President", "MedLife",
                   linkedin_url="https://www.linkedin.com/in/mihaimarcu/",
                   source="public", relevance="Final decision maker for tech acquisitions",
                   message_angle="MedLife patients already use our crawlers — we aggregate their lab results automatically"),
            Person("Dorin Preda", "CTO", "MedLife",
                   source="team page", relevance="Technical decision maker, evaluates integrations",
                   message_angle="I built working crawlers for your patient portal — interested in a technical deep-dive?"),
        ],
    ),
    Company(
        "Regina Maria", "https://www.reginamaria.ro",
        category="healthcare_provider", fit_score=5,
        why_fit="Crawler RM functional. Second largest. Owned by Mehilainen (Finnish, tech-forward).",
        approach="licensing",
        linkedin_company="https://www.linkedin.com/company/unirea-medical-center/",
        people=[
            Person("Fady Chreih", "CEO", "Regina Maria",
                   linkedin_url="https://www.linkedin.com/in/fady-chreih-71bb2122/",
                   source="team page", relevance="CEO since 2015, drives digital transformation",
                   message_angle="Your patient portal is good — imagine if it also showed Synevo and MedLife results in one place"),
            Person("Olimpia Enache", "COO", "Regina Maria",
                   source="team page", relevance="Operations leader, oversees patient experience",
                   message_angle="Per-user encryption means even we can't see patient data — built for your compliance standards"),
        ],
    ),
    Company(
        "Medicover", "https://www.medicover.ro",
        category="healthcare_provider", fit_score=5,
        why_fit="Nordic investor capital, aggressive digital expansion. Crawler potential.",
        approach="licensing",
        linkedin_company="https://www.linkedin.com/company/medicoverromania/",
        people=[
            Person("Calin Ghinea", "CEO Medicover Romania", "Medicover",
                   source="search", relevance="Country lead, decides on tech partnerships",
                   message_angle="Medicover patients want to see all their results in one place, not just Medicover's"),
        ],
    ),
    Company(
        "Sanador", "https://www.sanador.ro",
        category="healthcare_provider", fit_score=5,
        why_fit="Crawler Sanador functional. Premium positioning — tech differentiator.",
        approach="licensing",
        linkedin_company="https://www.linkedin.com/company/sanador-romania/",
        people=[
            Person("Ovidiu Palea", "CEO & Founder", "Sanador",
                   source="public", relevance="Founder-CEO, personally invested in brand differentiation",
                   message_angle="A luxury health experience includes seeing all your lab history in one place, with AI analysis"),
        ],
    ),
    Company(
        "MedPark / Enayati", "https://www.medpark.ro",
        category="healthcare_provider", fit_score=4,
        why_fit="Aggressive expansion, looking for tech differentiation.",
        approach="licensing",
        people=[
            Person("Wargha Enayati", "Founder & President", "Enayati Group",
                   linkedin_url="https://www.linkedin.com/in/wargha-enayati-7a83611a/",
                   source="public", relevance="Visionary founder, open to innovation partnerships",
                   message_angle="Your network is growing fast — give patients a reason to stay: unified health data with AI insights"),
        ],
    ),

    # === TIER 2: Insurance (health data = better risk assessment) ===
    Company(
        "NN Asigurari", "https://www.nn.ro",
        category="insurance", fit_score=4,
        why_fit="Largest life insurer in RO. Health data = predictive pricing + prevention programs.",
        approach="licensing",
        linkedin_company="https://www.linkedin.com/company/nn-romania/",
        people=[
            Person("Omer Tetik", "CEO NN Romania", "NN Asigurari",
                   linkedin_url="https://www.linkedin.com/in/omer-tetik-21199a28/",
                   source="public", relevance="Drives innovation strategy for NN Romania",
                   message_angle="Your policyholders' lab results predict risk better than questionnaires — we aggregate them automatically"),
        ],
    ),
    Company(
        "Allianz-Tiriac", "https://www.allianztiriac.ro",
        category="insurance", fit_score=3,
        why_fit="Health insurance products. Aggregated health data = personalized offers.",
        approach="licensing",
        linkedin_company="https://www.linkedin.com/company/allianz-tiriac/",
        people=[
            Person("Virgil Soncutean", "CEO Allianz-Tiriac", "Allianz-Tiriac",
                   linkedin_url="https://www.linkedin.com/in/virgil-soncutean-51b21a12/",
                   source="public", relevance="Leads digital transformation at Allianz Romania",
                   message_angle="Health insurers in the Nordics already use lab data for pricing — Romania has zero tools for this. Until now."),
        ],
    ),
    Company(
        "Generali Romania", "https://www.generali.ro",
        category="insurance", fit_score=3,
        why_fit="Prevention focus, corporate packages. Lab data enhances wellness programs.",
        approach="partnership",
        linkedin_company="https://www.linkedin.com/company/generali-romania/",
        people=[],
    ),
    Company(
        "Signal Iduna", "https://www.signaliduna.ro",
        category="insurance", fit_score=3,
        why_fit="Private health insurance — add value with lab aggregation for policyholders.",
        approach="partnership",
        people=[],
    ),

    # === TIER 3: Corporate Wellness (white-label opportunity) ===
    Company(
        "SanoPass", "https://www.sanopass.ro",
        category="wellness", fit_score=5,
        why_fit="Employee wellness platform. Lab aggregation is the #1 missing feature. PERFECT white-label fit.",
        approach="licensing",
        linkedin_company="https://www.linkedin.com/company/sanopass/",
        people=[
            Person("Oana Craioveanu", "CEO & Co-Founder", "SanoPass",
                   linkedin_url="https://www.linkedin.com/in/oana-craioveanu/",
                   source="public", relevance="Founded SanoPass, decides on product direction and partnerships",
                   message_angle="Your users already get lab tests through SanoPass — now show them results + AI analysis, under your brand"),
            Person("Teodor Blidarus", "Co-Founder", "SanoPass",
                   linkedin_url="https://www.linkedin.com/in/teodorblidarus/",
                   source="public", relevance="Tech co-founder, evaluates integration feasibility",
                   message_angle="We have working crawlers for Regina Maria, Synevo, MedLife, Sanador — plug them into SanoPass in weeks, not months"),
        ],
    ),
    Company(
        "7card", "https://www.7card.ro",
        category="wellness", fit_score=3,
        why_fit="Employee benefits (fitness + medical). Lab aggregation = natural extension.",
        approach="partnership",
        linkedin_company="https://www.linkedin.com/company/7card/",
        people=[
            Person("Florin Filote", "CEO", "7card",
                   source="search", relevance="Leads product strategy for benefits platform",
                   message_angle="7card does fitness and medical — adding lab result tracking closes the loop on employee health"),
        ],
    ),
    Company(
        "Benefit Systems", "https://www.benefitsystems.ro",
        category="wellness", fit_score=3,
        why_fit="Flexible benefits platform expanding into health modules.",
        approach="partnership",
        people=[],
    ),

    # === TIER 4: MedTech / Digital Health ===
    Company(
        "Doclandia", "https://www.doclandia.ro",
        category="medtech", fit_score=5,
        why_fit="Telemedicine startup. Lab results + consultations = complete health experience.",
        approach="partnership",
        people=[
            Person("Tudor Ciuleanu", "CEO & Co-Founder", "Doclandia",
                   source="search", relevance="Doctor-turned-founder, understands clinical value of lab data",
                   message_angle="Your doctors consult patients who have lab results elsewhere — what if they saw all results in Doclandia?"),
        ],
    ),
    Company(
        "Cegeka Romania", "https://www.cegeka.com/ro",
        category="medtech", fit_score=3,
        why_fit="Health IT solutions provider. Could resell or integrate lab aggregation.",
        approach="partnership",
        linkedin_company="https://www.linkedin.com/company/cegeka/",
        people=[],
    ),
    Company(
        "FintechOS", "https://www.fintechos.com",
        category="medtech", fit_score=3,
        why_fit="Insurtech expanding into health. Lab data enriches insurance products.",
        approach="partnership",
        linkedin_company="https://www.linkedin.com/company/fintechos/",
        people=[
            Person("Teodor Blidarus", "CEO & Co-Founder", "FintechOS",
                   linkedin_url="https://www.linkedin.com/in/teodorblidarus/",
                   source="public", relevance="Built FintechOS from scratch, understands platform plays",
                   message_angle="You digitize insurance — we digitize health data. Together: automated health underwriting."),
            Person("Sergiu Negut", "Co-Founder", "FintechOS",
                   linkedin_url="https://www.linkedin.com/in/sergiunegut/",
                   source="public", relevance="Business strategy, partnerships",
                   message_angle="Health data is the missing piece in insurtech — we already aggregate it from 4 major RO providers"),
        ],
    ),

    # === TIER 5: VC / Investors ===
    Company(
        "GapMinder VC", "https://www.gapminder.vc",
        category="vc", fit_score=3,
        why_fit="Invested in FintechOS, TypingDNA. Digital health is in their thesis.",
        approach="investment",
        linkedin_company="https://www.linkedin.com/company/gapminder-vc/",
        people=[
            Person("Dan Mihaescu", "Founding Partner", "GapMinder VC",
                   linkedin_url="https://www.linkedin.com/in/danmihaescu/",
                   source="team page", relevance="Leads B2B/AI investments. Invested in FintechOS.",
                   message_angle="You backed FintechOS for digitizing insurance — we digitize the health data that feeds it"),
            Person("Sergiu Rosca", "Founding Partner", "GapMinder VC",
                   linkedin_url="https://www.linkedin.com/in/sergiurosca/",
                   source="team page", relevance="Co-leads deal flow, enterprise SaaS focus",
                   message_angle="Romania's health data is locked in 4 portals. We're the only ones who cracked all 4."),
        ],
    ),
    Company(
        "Sparking Capital", "https://www.sparkingcapital.com",
        category="vc", fit_score=2,
        why_fit="Early-stage VC, tech focus. Could fund growth.",
        approach="investment",
        linkedin_company="https://www.linkedin.com/company/sparking-capital/",
        people=[
            Person("Vlad Panait", "Managing Partner & Founder", "Sparking Capital",
                   linkedin_url="https://www.linkedin.com/in/vladpanait/",
                   source="team page", relevance="Leads investment decisions",
                   message_angle="19M Romanians, 4 major lab providers, zero aggregation. We built it. Looking for growth capital."),
            Person("Cristian Negrutiu", "Founding Partner", "Sparking Capital",
                   linkedin_url="https://www.linkedin.com/in/cristiannegrutiu/",
                   source="team page", relevance="Co-leads fund",
                   message_angle="Health tech is underserved in CEE. We have product-market fit and working crawlers."),
        ],
    ),
    Company(
        "SeedBlink", "https://www.seedblink.com",
        category="vc", fit_score=2,
        why_fit="Equity crowdfunding — could run public campaign for visibility + funding.",
        approach="investment",
        linkedin_company="https://www.linkedin.com/company/seedblink/",
        people=[
            Person("Andrei Dudoiu", "CEO & Co-Founder", "SeedBlink",
                   linkedin_url="https://www.linkedin.com/in/andreidudoiu/",
                   source="public", relevance="Decides which startups get listed on SeedBlink",
                   message_angle="Health tech + Romania + working product = strong campaign. Interested in listing us?"),
        ],
    ),
    Company(
        "Catalyst Romania", "https://www.catalystromania.com",
        category="vc", fit_score=2,
        why_fit="First tech VC fund in Romania. Growth capital.",
        approach="investment",
        linkedin_company="https://www.linkedin.com/company/catalyst-romania/",
        people=[
            Person("Marius Ghenea", "Managing Partner", "Catalyst Romania",
                   linkedin_url="https://www.linkedin.com/in/mariusghenea/",
                   source="team page", relevance="30+ years experience, leads investment decisions",
                   message_angle="You've seen Romanian tech grow for decades — health data aggregation is the next unlock"),
        ],
    ),
    Company(
        "TechAngels Romania", "https://www.techangels.ro",
        category="vc", fit_score=2,
        why_fit="Angel network. Could connect with strategic investors.",
        approach="investment",
        people=[],
    ),
]


# ---------------------------------------------------------------------------
# People search — find real decision-makers via DuckDuckGo + LinkedIn
# ---------------------------------------------------------------------------

# Queries designed to find actual people, not company pages
PEOPLE_SEARCH_QUERIES = [
    # Direct LinkedIn profile searches
    'site:linkedin.com/in/ "MedLife" CTO OR "Chief Technology"',
    'site:linkedin.com/in/ "MedLife" "Head of Digital" OR "VP Digital" OR "Director IT"',
    'site:linkedin.com/in/ "Regina Maria" CTO OR "Director Digital" OR "Head of Product"',
    'site:linkedin.com/in/ "Medicover" Romania CTO OR CEO OR "Head of Digital"',
    'site:linkedin.com/in/ "SanoPass" CTO OR CEO OR "Head of Product"',
    'site:linkedin.com/in/ "NN Romania" OR "NN Asigurari" "Head of Innovation" OR "Director Digital" OR CTO',
    'site:linkedin.com/in/ "Allianz" Romania "Head of Digital" OR CTO OR "Director Innovation"',
    'site:linkedin.com/in/ "7card" CEO OR CTO OR "Head of Product"',
    'site:linkedin.com/in/ "Doclandia" CEO OR CTO OR founder',
    'site:linkedin.com/in/ "Benefit Systems" Romania CEO OR CTO OR "Director"',
    'site:linkedin.com/in/ "health tech" Romania CEO OR CTO OR founder',
    'site:linkedin.com/in/ "digital health" Romania CEO OR founder OR CTO',
    'site:linkedin.com/in/ "wellness" Romania CEO OR CTO OR "Head of Product"',
    'site:linkedin.com/in/ "telemedicina" OR "telehealth" Romania CEO OR founder',
    # Romanian business press — often names decision-makers
    '"MedLife" "CTO" OR "director IT" OR "director digital" site:zf.ro OR site:profit.ro OR site:startupcafe.ro',
    '"Regina Maria" "CTO" OR "director digital" site:zf.ro OR site:profit.ro',
    '"SanoPass" CEO OR "fondator" site:startupcafe.ro OR site:zf.ro OR site:profit.ro',
    'health tech Romania CEO founder startup site:startupcafe.ro',
    'corporate wellness Romania CEO CTO site:startupcafe.ro OR site:zf.ro',
]


def search_ddg(query: str, client: httpx.Client, max_results: int = 10) -> list:
    """Search DuckDuckGo HTML. Returns list of (url, title, snippet) tuples."""
    results = []
    try:
        resp = client.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            timeout=15.0,
            follow_redirects=True,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        for result in soup.find_all("div", class_="result"):
            a_tag = result.find("a", class_="result__a")
            snippet_tag = result.find("a", class_="result__snippet")
            if not a_tag:
                continue

            href = a_tag.get("href", "")
            if "uddg=" in href:
                parsed = parse_qs(urlparse(href).query)
                if "uddg" in parsed:
                    href = parsed["uddg"][0]

            title = a_tag.get_text(strip=True)
            snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""

            if href.startswith("http"):
                results.append((href, title, snippet))
            if len(results) >= max_results:
                break
    except Exception as e:
        print(f"    ! DDG failed: {e}")
    return results


def extract_person_from_linkedin_result(url: str, title: str, snippet: str, company_hint: str = "") -> Optional[Person]:
    """Parse a LinkedIn search result into a Person."""
    if "linkedin.com/in/" not in url:
        return None

    # LinkedIn titles look like: "John Doe - CTO at MedLife | LinkedIn"
    # Or: "John Doe | LinkedIn"
    title_clean = title.replace(" | LinkedIn", "").replace(" - LinkedIn", "").strip()

    parts = re.split(r"\s*[-–|]\s*", title_clean, maxsplit=1)
    name = parts[0].strip()
    role_company = parts[1].strip() if len(parts) > 1 else ""

    # Skip if name looks wrong
    if len(name) < 3 or len(name) > 60:
        return None
    if any(kw in name.lower() for kw in ["linkedin", "http", "www", "view"]):
        return None

    # Parse role and company from the second part
    role = role_company
    company = ""
    if " at " in role_company:
        role, company = role_company.rsplit(" at ", 1)
    elif " la " in role_company:  # Romanian
        role, company = role_company.rsplit(" la ", 1)
    elif " @ " in role_company:
        role, company = role_company.rsplit(" @ ", 1)

    role = role.strip()
    company = company.strip()

    # Use hint if no company found
    if not company and company_hint:
        company = company_hint

    # Clean up the LinkedIn URL
    url_clean = url.split("?")[0].rstrip("/")

    return Person(
        name=name,
        title=role,
        company=company,
        linkedin_url=url_clean,
        source="linkedin_search",
    )


def extract_person_from_article(url: str, title: str, snippet: str) -> list:
    """Extract person mentions from business press articles."""
    people = []
    combined = f"{title} {snippet}"

    # Pattern: "Name, Title at/la Company" or "Name (Title, Company)"
    patterns = [
        re.compile(r'([A-Z][a-z]+ [A-Z][a-z]+(?:\s[A-Z][a-z]+)?),?\s+(CEO|CTO|COO|CFO|CPO|CMO|'
                   r'[Ff]ondator|[Ff]ounder|[Dd]irector\s+\w+|Head of \w+|VP \w+)'
                   r'(?:\s+(?:al|la|at|@)\s+(.+?)(?:[,.]|$))?', re.UNICODE),
    ]

    for pattern in patterns:
        for match in pattern.finditer(combined):
            name = match.group(1).strip()
            role = match.group(2).strip()
            company = match.group(3).strip() if match.group(3) else ""
            if len(name) > 3 and not any(kw in name.lower() for kw in ["linkedin", "http"]):
                people.append(Person(
                    name=name,
                    title=role,
                    company=company,
                    source=f"article: {urlparse(url).netloc}",
                ))

    return people


def find_people_for_company(company: Company, client: httpx.Client) -> list:
    """Search for decision-makers at a specific company."""
    people = []
    name = company.name.split("/")[0].strip()  # "MedPark / Enayati" -> "MedPark"

    queries = [
        f'site:linkedin.com/in/ "{name}" CTO OR CEO OR "Head of Digital" OR "Director IT"',
        f'site:linkedin.com/in/ "{name}" "Head of Product" OR CPO OR "VP" OR founder',
        f'"{name}" CTO OR "director digital" OR "head of innovation" Romania',
    ]

    for query in queries:
        print(f"      Searching: {query[:80]}...")
        results = search_ddg(query, client, max_results=5)

        for url, title, snippet in results:
            if "linkedin.com/in/" in url:
                person = extract_person_from_linkedin_result(url, title, snippet, name)
                if person and person.name:
                    # Check if this person is likely at the right company
                    combined = f"{person.company} {title} {snippet}".lower()
                    if name.lower() in combined or not person.company:
                        person.company = name
                        people.append(person)
            else:
                # Business press article — might mention people
                article_people = extract_person_from_article(url, title, snippet)
                for p in article_people:
                    if name.lower() in p.company.lower() or not p.company:
                        p.company = name
                        people.append(p)

        time.sleep(1.5)  # Respect rate limits

    # Deduplicate by name
    seen_names = set()
    unique = []
    for p in people:
        key = p.name.lower().strip()
        if key not in seen_names:
            seen_names.add(key)
            unique.append(p)

    return unique


def search_for_new_people(client: httpx.Client) -> dict:
    """Run broad people searches. Returns dict of company_name -> [Person]."""
    people_by_company = {}

    for query in PEOPLE_SEARCH_QUERIES:
        print(f"  Searching: {query[:80]}...")
        results = search_ddg(query, client, max_results=8)

        for url, title, snippet in results:
            if "linkedin.com/in/" in url:
                person = extract_person_from_linkedin_result(url, title, snippet)
                if person and person.name and person.company:
                    people_by_company.setdefault(person.company, []).append(person)
            else:
                article_people = extract_person_from_article(url, title, snippet)
                for p in article_people:
                    if p.company:
                        people_by_company.setdefault(p.company, []).append(p)

        time.sleep(1.5)

    return people_by_company


# ---------------------------------------------------------------------------
# Team page scraping (improved)
# ---------------------------------------------------------------------------

def fetch_page(url: str, client: httpx.Client, timeout: float = 15.0) -> Optional[str]:
    try:
        resp = client.get(url, timeout=timeout, follow_redirects=True)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"    ! Could not fetch {url}: {type(e).__name__}")
        return None


def scrape_team_page(company: Company, client: httpx.Client) -> list:
    """Scrape a company's website for team/leadership pages and extract people."""
    people = []
    html = fetch_page(company.website, client)
    if not html:
        return people

    soup = BeautifulSoup(html, "html.parser")

    # Find team/about/leadership page links
    team_urls = []
    for a in soup.find_all("a", href=True):
        href = a.get("href", "").lower()
        text = a.get_text(strip=True).lower()
        combined = f"{href} {text}"
        if re.search(r"team|echipa|leadership|management|about.*us|despre.*noi|conducere", combined):
            full_url = urljoin(company.website, a["href"])
            if full_url not in team_urls and company.website.split("//")[1].split("/")[0] in full_url:
                team_urls.append(full_url)

    # Also check common paths
    base = company.website.rstrip("/")
    for path in ["/about", "/team", "/despre-noi", "/echipa", "/leadership", "/management",
                 "/about-us", "/about/team", "/despre/echipa", "/conducere"]:
        team_urls.append(f"{base}{path}")

    # Also look for LinkedIn profile links on the homepage
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "linkedin.com/in/" in href:
            text = a.get_text(strip=True)
            if text and len(text) > 3:
                people.append(Person(
                    name=text, title="(from website)", company=company.name,
                    linkedin_url=href.split("?")[0], source="website_link",
                ))

    # Visit team pages
    seen_urls = set()
    for url in team_urls[:5]:  # Cap at 5 pages
        if url in seen_urls:
            continue
        seen_urls.add(url)

        team_html = fetch_page(url, client)
        if not team_html:
            continue

        team_soup = BeautifulSoup(team_html, "html.parser")
        page_text = team_soup.get_text(separator="\n", strip=True)

        # Method 1: LinkedIn links on team page
        for a in team_soup.find_all("a", href=True):
            href = a["href"]
            if "linkedin.com/in/" in href:
                # Try to find the associated name
                parent = a.find_parent(["div", "li", "article", "section"])
                if parent:
                    parent_text = parent.get_text(separator="\n", strip=True)
                    lines = [l.strip() for l in parent_text.split("\n") if l.strip()]
                    name = lines[0] if lines and len(lines[0]) < 60 else ""
                    role = ""
                    role_kw = re.compile(r"(CEO|CTO|COO|CFO|CPO|CMO|Director|Manager|Head|VP|"
                                        r"Fondator|Founder|Partner|Lead|Chief|President)", re.I)
                    for line in lines[1:4]:
                        if role_kw.search(line):
                            role = line
                            break
                    if name:
                        people.append(Person(
                            name=name, title=role, company=company.name,
                            linkedin_url=href.split("?")[0], source="team_page",
                        ))

        # Method 2: Structured team cards (divs with class containing team/member)
        role_kw = re.compile(r"(CEO|CTO|COO|CFO|CPO|CMO|Director|Manager|Head of|VP |"
                             r"Fondator|Founder|Managing Partner|Chief|President|Presedinte)", re.I)
        for container in team_soup.find_all(["div", "article", "li", "section"],
                                            class_=re.compile(r"team|member|person|staff|echipa|leadership", re.I)):
            texts = container.get_text(separator="\n", strip=True).split("\n")
            texts = [t.strip() for t in texts if t.strip() and 3 < len(t.strip()) < 80]
            for i, text in enumerate(texts):
                if role_kw.search(text):
                    name = texts[i - 1] if i > 0 and not role_kw.search(texts[i - 1]) else ""
                    if name and len(name) > 3:
                        # Check for LinkedIn link nearby
                        li_link = container.find("a", href=re.compile(r"linkedin.com/in/"))
                        li_url = li_link["href"].split("?")[0] if li_link else ""
                        people.append(Person(
                            name=name, title=text, company=company.name,
                            linkedin_url=li_url, source="team_page",
                        ))

        time.sleep(0.5)

    # Deduplicate
    seen = set()
    unique = []
    for p in people:
        key = p.name.lower().strip()
        if key not in seen and len(key) > 3:
            seen.add(key)
            unique.append(p)

    return unique


# ---------------------------------------------------------------------------
# Merge people into companies
# ---------------------------------------------------------------------------

def merge_people(existing: list, new_people: list) -> list:
    """Merge new people into existing list, preferring records with LinkedIn URLs."""
    by_name = {}
    for p in existing:
        by_name[p["name"].lower() if isinstance(p, dict) else p.name.lower()] = p

    for p in new_people:
        key = p.name.lower()
        if key in by_name:
            old = by_name[key]
            old_dict = old if isinstance(old, dict) else old.to_dict()
            # Keep the one with more info
            if p.linkedin_url and not old_dict.get("linkedin_url"):
                by_name[key] = p
        else:
            by_name[key] = p

    result = []
    for v in by_name.values():
        result.append(v.to_dict() if isinstance(v, Person) else v)
    return result


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

CATEGORY_LABELS = {
    "healthcare_provider": "Healthcare Providers",
    "insurance": "Insurance Companies",
    "wellness": "Corporate Wellness",
    "medtech": "MedTech / Digital Health",
    "vc": "VC / Investors",
    "unknown": "Other",
}

CATEGORY_ORDER = ["healthcare_provider", "insurance", "wellness", "medtech", "vc", "unknown"]


def generate_report(companies: list) -> str:
    """Generate a people-focused Markdown report."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    total_people = sum(len(c.get("people", []) if isinstance(c, dict) else c.people) for c in companies)

    lines = [
        f"# Prospect Report — Analize.Online",
        f"",
        f"**Generated:** {now}",
        f"**Companies:** {len(companies)} | **Decision-makers found:** {total_people}",
        f"",
        f"---",
        f"",
    ]

    # Group by category
    by_cat = {}
    for c in companies:
        cat = c["category"] if isinstance(c, dict) else c.category
        by_cat.setdefault(cat, []).append(c)

    for cat in CATEGORY_ORDER:
        if cat not in by_cat:
            continue

        label = CATEGORY_LABELS.get(cat, cat)
        clist = by_cat[cat]
        clist.sort(key=lambda c: -(c["fit_score"] if isinstance(c, dict) else c.fit_score))

        lines.append(f"## {label}")
        lines.append("")

        for c in clist:
            d = c if isinstance(c, dict) else c.to_dict()
            score = d["fit_score"]
            stars = "+" * score + "." * (5 - score)

            lines.append(f"### {d['name']} [{stars}] — {d.get('approach', '').upper()}")
            lines.append(f"_{d.get('why_fit', '')}_")
            lines.append("")

            people = d.get("people", [])
            if people:
                lines.append("| Who | Title | LinkedIn | Angle |")
                lines.append("|-----|-------|----------|-------|")
                for p in people:
                    li = f"[Profile]({p['linkedin_url']})" if p.get("linkedin_url") else "-"
                    angle = p.get("message_angle", "") or p.get("relevance", "")
                    lines.append(f"| **{p['name']}** | {p.get('title', '')} | {li} | {angle[:80]} |")
                lines.append("")
            else:
                lines.append("_No decision-makers found yet — search LinkedIn manually._")
                lines.append("")

            if d.get("linkedin_company"):
                lines.append(f"Company LinkedIn: {d['linkedin_company']}")
            if d.get("website"):
                lines.append(f"Website: {d['website']}")
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Prospect Finder — People-First Edition")
    parser.add_argument("--enrich-only", "--no-search", action="store_true",
                        help="Only enrich seed list (team pages), skip broad search")
    parser.add_argument("--people-only", action="store_true",
                        help="Only search for people (skip company discovery)")
    parser.add_argument("--skip-team-pages", action="store_true",
                        help="Skip team page scraping (faster)")
    args = parser.parse_args()

    print("=" * 60)
    print("  Prospect Finder — People-First Edition")
    print("=" * 60)

    client = httpx.Client(headers=HEADERS, follow_redirects=True, timeout=15.0)
    companies = list(SEED_COMPANIES)

    # Step 1: Scrape team pages for each company
    if not args.skip_team_pages:
        print(f"\n[1/3] Scraping team pages for {len(companies)} companies...")
        for comp in companies:
            print(f"  {comp.name}...")
            try:
                new_people = scrape_team_page(comp, client)
                if new_people:
                    comp.people = merge_people(
                        [p.to_dict() if isinstance(p, Person) else p for p in comp.people],
                        new_people
                    )
                    print(f"    Found {len(new_people)} people on team pages")
            except Exception as e:
                print(f"    ! Error: {e}")
            time.sleep(0.5)
    else:
        print("\n[1/3] Skipping team pages")

    # Step 2: Search for people at companies that have few/no contacts
    if not args.enrich_only:
        companies_needing_people = [c for c in companies if len(c.people) < 2]
        if companies_needing_people:
            print(f"\n[2/3] Searching for decision-makers at {len(companies_needing_people)} companies...")
            for comp in companies_needing_people:
                print(f"  {comp.name}...")
                try:
                    new_people = find_people_for_company(comp, client)
                    if new_people:
                        comp.people = merge_people(
                            [p.to_dict() if isinstance(p, Person) else p for p in comp.people],
                            new_people
                        )
                        print(f"    Found {len(new_people)} people via search")
                except Exception as e:
                    print(f"    ! Error: {e}")
                time.sleep(1)

        # Step 3: Broad search for new people/companies
        if not args.people_only:
            print(f"\n[3/3] Broad people search ({len(PEOPLE_SEARCH_QUERIES)} queries)...")
            new_people_map = search_for_new_people(client)

            for company_name, people_list in new_people_map.items():
                # Try to match to existing company
                matched = None
                for comp in companies:
                    if company_name.lower() in comp.name.lower() or comp.name.lower() in company_name.lower():
                        matched = comp
                        break

                if matched:
                    matched.people = merge_people(
                        [p.to_dict() if isinstance(p, Person) else p for p in matched.people],
                        people_list
                    )
                else:
                    # New company discovered via people search
                    print(f"  New company via people: {company_name}")
        else:
            print("\n[3/3] Skipping broad search")
    else:
        print("\n[2/3] Skipping people search (enrich-only mode)")
        print("[3/3] Skipping broad search (enrich-only mode)")

    client.close()

    # Convert people to dicts for serialization
    for comp in companies:
        if comp.people and isinstance(comp.people[0], Person):
            comp.people = [p.to_dict() for p in comp.people]

    # Sort by fit score
    companies.sort(key=lambda c: (-c.fit_score, c.category, c.name))

    # Save outputs
    print(f"\nSaving outputs...")

    # JSON
    json_data = [c.to_dict() for c in companies]
    json_path = OUTPUT_DIR / "prospects_data.json"
    json_path.write_text(json.dumps(json_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  JSON: {json_path}")

    # Markdown
    report = generate_report(companies)
    report_path = OUTPUT_DIR / "prospects_report.md"
    report_path.write_text(report, encoding="utf-8")
    print(f"  Report: {report_path}")

    # Summary
    total_people = sum(len(c.people) for c in companies)
    with_linkedin = sum(1 for c in companies for p in c.people if p.get("linkedin_url"))

    print(f"\n{'=' * 60}")
    print(f"  {len(companies)} companies | {total_people} decision-makers | {with_linkedin} with LinkedIn")
    print(f"{'=' * 60}")

    for cat in CATEGORY_ORDER:
        cat_comps = [c for c in companies if c.category == cat]
        if cat_comps:
            cat_people = sum(len(c.people) for c in cat_comps)
            print(f"  {CATEGORY_LABELS.get(cat, cat)}: {len(cat_comps)} companies, {cat_people} people")

    print(f"\n  Top contacts to reach out to:")
    for c in companies:
        if c.fit_score >= 4:
            for p in c.people[:2]:
                p_dict = p if isinstance(p, dict) else p.to_dict()
                li = p_dict.get("linkedin_url", "")
                li_short = li.split("linkedin.com")[1] if "linkedin.com" in li else "(no LinkedIn)"
                print(f"    {p_dict['name']:25s} {p_dict.get('title', ''):30s} @ {c.name:20s} {li_short}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
