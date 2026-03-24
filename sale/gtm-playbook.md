# Go-To-Market Playbook — Analize.Online

**Last updated:** 2026-03-24
**Status:** 8 users, 0 paying. Feature-complete, deployed at analize.online.

---

## Current Assets

| Asset | Status | Location |
|-------|--------|----------|
| Product (live) | Deployed | analize.online |
| Pitch deck (HTML) | Ready | `sale/pitch-deck.html` |
| Tech summary | Ready | `sale/tech-summary.md` |
| Email templates (RO) | Ready | `sale/email-templates-ro.md` |
| Outreach templates (EN) | Ready | `sale/outreach-templates.md` |
| LinkedIn posts (RO) | Ready | `sale/linkedin-posts-ro.md` |
| Target list (RO) | Ready | `sale/target-list-ro.md` |
| Prospect report | Auto-generated | `sale/prospects_report.md` |

---

## 8-Week Execution Plan

### Week 1-2: Warm Up (Credibility + Prep)

**LinkedIn presence:**
1. Update LinkedIn profile — add "Founder, analize.online" to headline
2. Post article #1: "Am construit o platforma care conecteaza Regina Maria, Synevo, MedLife si Sanador" (see `linkedin-posts-ro.md`)
3. Post article #2: Technical deep-dive on per-user encryption
4. Connect with 20-30 people in Romanian health-tech/medtech

**Credibility gaps to fix:**
- [ ] Get Netopia payments out of sandbox mode
- [ ] Add proper meta tags and Open Graph images for link sharing
- [ ] Ensure analize.online loads fast and looks polished on mobile
- [ ] Add a "For Business" or "Partnerships" page on the website

**Prospect research:**
- [ ] Run `python sale/find_prospects.py` to generate enriched prospect list
- [ ] Review `sale/prospects_report.md` — mark your top 10 priority targets
- [ ] For top 10: find specific people on LinkedIn (CTO, Head of Digital, VP Product)

---

### Week 3-4: Outreach Wave 1 — Warm Channels

**Strategy:** Warm intros > cold emails. Personal network first.

**Actions:**
1. **Personal network** — Message anyone you know at or connected to target companies
   - Ask: "Do you know anyone at [Company] who works on digital/tech/product?"
   - Even a weak intro converts 5-10x better than cold outreach

2. **LinkedIn DMs to Tier 1** (healthcare providers — highest fit):
   - MedLife: Find CTO / VP Digital → Template #1 from `outreach-templates.md`
   - Regina Maria: Fady Chreih (CEO) or Olimpia Enache (COO) — found on team page
   - SanoPass: Oana Craioveanu (CEO) — direct fit, wellness platform
   - Medicover: Country Manager RO / Head of Digital

3. **Personalization checklist** for each message:
   - [ ] Reference something specific about their company/product
   - [ ] Explain exactly how analize.online fits their business
   - [ ] Offer a 15-minute live demo, not a generic "let's chat"
   - [ ] Attach or link to the pitch deck

**Goal:** Book 3-5 demo calls.

---

### Week 5-6: Outreach Wave 2 — Cold Channels

**Strategy:** Broaden reach. Use contact forms, press emails, events.

**Actions:**
1. **Email pitches** to companies where LinkedIn didn't work:
   - Use contact form URLs from `prospects_report.md`
   - Send formal Template #2 from `outreach-templates.md`
   - Try patterns: parteneriate@company.ro, press@company.ro, contact@company.ro

2. **Insurance companies** (Tier 2):
   - NN Asigurari, Allianz-Tiriac, Generali — use Template #3 (insurer-specific)
   - Frame as: "health data for better risk assessment and prevention programs"

3. **Events and meetups:**
   - Search for upcoming Romanian health-tech / startup events
   - Rubik Hub HealthTech accelerator (found in search results — 41 startups selected)
   - TechAngels Romania meetups
   - How To Web conference (if timing works)
   - Bring business cards + have demo ready on phone

4. **Corporate wellness** (Tier 3):
   - SanoPass, 7card, Benefit Systems — use Template #4 (white-label)
   - Frame as: "add lab result aggregation to your existing benefits platform"

**Goal:** Book 3-5 more demo calls.

---

### Week 7-8: Demo & Negotiate

**Demo flow:**
1. Open `sale/pitch-deck.html` — 3-minute pitch (problem → solution → demo → moat → ask)
2. Live demo on analize.online — show real data, real AI analysis
3. Share `sale/tech-summary.md` as PDF follow-up

**Offer structure — always present 3 options:**

| Option | Price Range | What They Get |
|--------|------------|---------------|
| **Acquisition** | €30-80K | Full source code, domain, infrastructure, 6 months support |
| **Licensing** | €500-2,000/mo | White-label deployment, ongoing maintenance, updates |
| **Revenue share** | 20-30% of revenue | We run everything, they provide distribution |

Let them choose. Most will pick licensing or revenue share (lower risk). Acquisition is the anchor that makes licensing look cheap.

**Follow-up cadence:**
- **Day 0:** Demo call
- **Day 1:** Thank-you email + pitch deck + tech summary PDF
- **Day 3:** "Any questions? Happy to do a deeper technical walkthrough"
- **Day 7:** "Wanted to check in — would it help to involve your tech team?"
- **Day 14:** "Last follow-up — the offer stands. Let me know if timing is better later"

---

## Closing Tactics

### Urgency
> "The crawlers break when providers update their portals — I maintain them continuously. This maintenance is included in licensing but not available à la carte."

### Social proof
> "We have 8 active users and have processed 700+ biomarkers. The platform is production-proven, not a prototype."

### Risk reduction
> "3-6 months of transition support is included. I'll train your team and be available for questions."

### Competition framing
> "Nobody else in Romania has working crawlers for all 4 major providers. Building this from scratch would take 6-12 months and significant investment."

### Multiple options
Always present acquisition AND licensing — let them self-select. If they say "too expensive", switch to revenue share.

---

## Metrics to Track

| Metric | Target | Tool |
|--------|--------|------|
| LinkedIn profile views | 100+/week | LinkedIn analytics |
| Connection requests sent | 30/week | Manual tracking |
| DMs/emails sent | 10/week | Spreadsheet |
| Response rate | >20% | Spreadsheet |
| Demo calls booked | 6-10 total | Calendar |
| Offers sent | 3-5 | Email |
| Deals closed | 1+ | 🎉 |

---

## Quick Reference: Key Files

```
sale/
├── find_prospects.py       # Run to discover and enrich prospects
├── prospects_report.md     # Generated prospect report with contacts
├── prospects_data.json     # Machine-readable prospect data
├── target-list-ro.md       # Manually curated target list
├── email-templates-ro.md   # Romanian email templates
├── outreach-templates.md   # English outreach templates
├── linkedin-posts-ro.md    # LinkedIn post drafts
├── pitch-deck.html         # Interactive pitch deck
├── tech-summary.md         # Technical summary for buyers
└── gtm-playbook.md         # This file
```

---

*Playbook created 2026-03-24. Update after each outreach wave with results.*
