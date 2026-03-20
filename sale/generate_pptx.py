"""Generate the Analize.Online Romanian sales pitch PowerPoint."""

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# Brand colors
DARK_BG = RGBColor(0x0F, 0x17, 0x2A)
CARD_BG = RGBColor(0x1E, 0x29, 0x3B)
CYAN = RGBColor(0x06, 0xB6, 0xD4)
TEAL = RGBColor(0x14, 0xB8, 0xA6)
WHITE = RGBColor(0xF1, 0xF5, 0xF9)
LIGHT_GRAY = RGBColor(0x94, 0xA3, 0xB8)
MID_GRAY = RGBColor(0x64, 0x74, 0x8B)
GREEN = RGBColor(0x22, 0xC5, 0x5E)
AMBER = RGBColor(0xFB, 0xBF, 0x24)
RED = RGBColor(0xEF, 0x44, 0x44)
VIOLET = RGBColor(0xA7, 0x8B, 0xFA)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)

# Layout constants
MARGIN = Inches(0.6)
CONTENT_W = Inches(12.1)  # 13.333 - 2*0.6
TAG_TOP = Inches(0.85)
TITLE_TOP = Inches(1.4)
BODY_TOP = Inches(2.5)
SAFE_BOTTOM = Inches(7.0)  # leave room for slide number


def set_slide_bg(slide, color=DARK_BG):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_text_box(slide, left, top, width, height, text, font_size=18,
                 color=WHITE, bold=False, alignment=PP_ALIGN.LEFT, font_name="Calibri"):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    tf.margin_left = Pt(2)
    tf.margin_right = Pt(2)
    tf.margin_top = Pt(1)
    tf.margin_bottom = Pt(1)
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.font.name = font_name
    p.alignment = alignment
    return tf


def add_paragraph(tf, text, font_size=18, color=WHITE, bold=False, alignment=PP_ALIGN.LEFT,
                  space_before=Pt(4), space_after=Pt(1)):
    p = tf.add_paragraph()
    p.text = text
    p.font.size = Pt(font_size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.font.name = "Calibri"
    p.alignment = alignment
    p.space_before = space_before
    p.space_after = space_after
    return p


def add_rounded_rect(slide, left, top, width, height, fill_color=CARD_BG):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    shape.line.fill.background()
    shape.shadow.inherit = False
    return shape


def add_tag(slide, left, top, text, color=CYAN):
    w, h = Inches(2.8), Inches(0.35)
    c = str(color)
    r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    shape = add_rounded_rect(slide, left, top, w, h, fill_color=RGBColor(
        r // 6, g // 6, b // 6,
    ))
    shape.text_frame.word_wrap = False
    p = shape.text_frame.paragraphs[0]
    p.text = text
    p.font.size = Pt(11)
    p.font.color.rgb = color
    p.font.bold = True
    p.font.name = "Calibri"
    p.alignment = PP_ALIGN.CENTER
    shape.text_frame.margin_top = Pt(3)
    shape.text_frame.margin_bottom = Pt(3)


def slide_number(slide, num, total=14):
    add_text_box(slide, SLIDE_W - Inches(1.2), SLIDE_H - Inches(0.45), Inches(1), Inches(0.35),
                 f"{num} / {total}", font_size=10, color=MID_GRAY, alignment=PP_ALIGN.RIGHT)


def logo_bar(slide):
    add_text_box(slide, MARGIN, Inches(0.25), Inches(3), Inches(0.35),
                 "Analize.Online", font_size=13, color=LIGHT_GRAY, bold=True)


# ============================================================
# SLIDE 1: Title
# ============================================================
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(sl)

add_text_box(sl, Inches(1), Inches(1.5), Inches(11.3), Inches(1.0),
             "Analize.Online", font_size=54, color=CYAN, bold=True, alignment=PP_ALIGN.CENTER)

add_text_box(sl, Inches(1.5), Inches(2.7), Inches(10.3), Inches(1.2),
             "Prima platformă din România care unifică\ntoate analizele medicale cu inteligență artificială",
             font_size=28, color=WHITE, bold=False, alignment=PP_ALIGN.CENTER)

add_text_box(sl, Inches(2), Inches(4.5), Inches(9.3), Inches(0.4),
             "Pitch de vânzare / licențiere — Martie 2026",
             font_size=15, color=MID_GRAY, alignment=PP_ALIGN.CENTER)

add_text_box(sl, Inches(2), Inches(5.5), Inches(9.3), Inches(0.4),
             "Confidențial  •  contact@analize.online  •  analize.online",
             font_size=13, color=MID_GRAY, alignment=PP_ALIGN.CENTER)

slide_number(sl, 1)

# ============================================================
# SLIDE 2: Problema
# ============================================================
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(sl)
logo_bar(sl)
add_tag(sl, MARGIN, TAG_TOP, "PROBLEMA", CYAN)

add_text_box(sl, MARGIN, TITLE_TOP, Inches(7.5), Inches(0.9),
             "Datele medicale din România\nsunt fragmentate și inaccesibile",
             font_size=34, color=WHITE, bold=True)

bullets = [
    "Rezultatele sunt blocate în portaluri separate (Regina Maria, Synevo, MedLife, Sanador)",
    "Nicio vedere unificată — pacienții uită rezultatele anterioare",
    "PDF-uri cu sute de valori — imposibil de interpretat fără medic",
    "Zero urmărire tendințe — colesterolul a crescut sau scăzut?",
    "Vizite reactive, nu preventive — pacienții merg doar când sunt bolnavi",
]
tf = add_text_box(sl, MARGIN, Inches(2.8), Inches(7.2), Inches(3.8), "", font_size=16, color=LIGHT_GRAY)
tf.paragraphs[0].text = ""
for b in bullets:
    add_paragraph(tf, f"→  {b}", font_size=16, color=LIGHT_GRAY, space_before=Pt(8))

# Stats card (right side)
card = add_rounded_rect(sl, Inches(8.4), Inches(1.8), Inches(4.3), Inches(4.5), CARD_BG)
add_text_box(sl, Inches(8.7), Inches(2.2), Inches(3.7), Inches(0.9), "19M+",
             font_size=56, color=CYAN, bold=True, alignment=PP_ALIGN.CENTER)
add_text_box(sl, Inches(8.7), Inches(3.2), Inches(3.7), Inches(0.4), "români",
             font_size=20, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)
stats_lines = "4 furnizori mari de analize\n0 platforme unificate\nMilioane de rezultate în silozuri"
add_text_box(sl, Inches(8.7), Inches(4.0), Inches(3.7), Inches(1.8), stats_lines,
             font_size=15, color=MID_GRAY, alignment=PP_ALIGN.CENTER)

slide_number(sl, 2)

# ============================================================
# SLIDE 3: Soluția
# ============================================================
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(sl)
logo_bar(sl)
add_tag(sl, MARGIN, TAG_TOP, "SOLUȚIA", TEAL)

add_text_box(sl, MARGIN, TITLE_TOP, Inches(11), Inches(0.7),
             "Un singur loc. Toate analizele. AI care le explică.",
             font_size=34, color=WHITE, bold=True)

steps = [
    ("1", "Conectezi conturile medicale", "Regina Maria, Synevo, MedLife, Sanador — credențiale criptate AES-256"),
    ("2", "Sincronizare automată", "Crawlere Playwright descarcă toate PDF-urile, gestionare CAPTCHA inclusă"),
    ("3", "Extracție AI", "GPT-4o extrage 150+ tipuri de biomarkeri: nume, valoare, unitate, referință"),
    ("4", "Specialiști AI dinamici", "Generalistul analizează, apoi recomandă specialiștii relevanți — orice specialitate, automat"),
    ("5", "Grafice și alerte", "Evoluție în timp, valori anormale evidențiate, screening-uri preventive"),
]
y = BODY_TOP
for num, title, desc in steps:
    # Number circle
    circ = sl.shapes.add_shape(MSO_SHAPE.OVAL, Inches(0.8), y, Inches(0.5), Inches(0.5))
    circ.fill.solid()
    circ.fill.fore_color.rgb = TEAL
    circ.line.fill.background()
    p = circ.text_frame.paragraphs[0]
    p.text = num
    p.font.size = Pt(17)
    p.font.color.rgb = WHITE
    p.font.bold = True
    p.alignment = PP_ALIGN.CENTER
    circ.text_frame.margin_top = Pt(2)

    add_text_box(sl, Inches(1.55), y - Inches(0.02), Inches(4.5), Inches(0.35),
                 title, font_size=18, color=WHITE, bold=True)
    add_text_box(sl, Inches(1.55), y + Inches(0.32), Inches(11), Inches(0.35),
                 desc, font_size=14, color=LIGHT_GRAY)
    y += Inches(0.85)

slide_number(sl, 3)

# ============================================================
# SLIDE 4: Ce include platforma
# ============================================================
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(sl)
logo_bar(sl)
add_tag(sl, MARGIN, TAG_TOP, "INVENTAR", VIOLET)

add_text_box(sl, MARGIN, TITLE_TOP, Inches(11), Inches(0.7),
             "Ce include platforma (cuantificat)",
             font_size=34, color=WHITE, bold=True)

items_left = [
    ("28", "Servicii backend", "~11.000 linii Python"),
    ("50+", "Endpoint-uri API", "16 routere"),
    ("30+", "Modele bază de date", "PostgreSQL"),
    ("20+", "Pagini frontend", "React + Tailwind"),
    ("4", "Crawlere furnizori", "Playwright + CAPTCHA"),
    ("6", "Agenți AI", "GPT-4o specialiști"),
]
items_right = [
    ("150+", "Tipuri biomarkeri", "Normalizați"),
    ("2", "Limbi", "RO + EN (i18next)"),
    ("AES-256", "Criptare per user", "Vault + recovery key"),
    ("GDPR", "Conformitate", "Export, ștergere, consent"),
    ("Netopia", "Plăți integrate", "29/49 RON/lună"),
    ("Prometheus", "Monitorizare", "Grafana + Sentry"),
]

y_start = BODY_TOP
for col_idx, items in enumerate([items_left, items_right]):
    x_base = MARGIN if col_idx == 0 else Inches(6.8)
    y = y_start
    for val, label, detail in items:
        add_text_box(sl, x_base, y, Inches(1.6), Inches(0.4),
                     val, font_size=18, color=CYAN, bold=True)
        add_text_box(sl, x_base + Inches(1.7), y, Inches(2.4), Inches(0.4),
                     label, font_size=15, color=WHITE, bold=True)
        add_text_box(sl, x_base + Inches(4.2), y, Inches(2.0), Inches(0.4),
                     detail, font_size=13, color=MID_GRAY)
        y += Inches(0.55)

slide_number(sl, 4)

# ============================================================
# SLIDE 5: Crawlere — Moat tehnic
# ============================================================
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(sl)
logo_bar(sl)
add_tag(sl, MARGIN, TAG_TOP, "MOAT TEHNIC", CYAN)

add_text_box(sl, MARGIN, TITLE_TOP, Inches(11), Inches(0.7),
             "4 crawlere. Cel mai greu de replicat.",
             font_size=34, color=WHITE, bold=True)

providers = [
    ("Regina Maria", "CAPTCHA handling\nVisible browser fallback"),
    ("Synevo", "Full headless mode\nMulti-page navigation"),
    ("MedLife", "CAPTCHA detection\nAuto-retry logic"),
    ("Sanador", "Headless automation\nSession management"),
]
x = MARGIN
card_w = Inches(2.85)
card_gap = Inches(0.2)
for name, details in providers:
    card = add_rounded_rect(sl, x, BODY_TOP, card_w, Inches(1.6), CARD_BG)
    add_text_box(sl, x + Inches(0.15), BODY_TOP + Inches(0.1), Inches(2.55), Inches(0.4),
                 name, font_size=18, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)
    add_text_box(sl, x + Inches(0.15), BODY_TOP + Inches(0.55), Inches(2.55), Inches(0.8),
                 details, font_size=12, color=MID_GRAY, alignment=PP_ALIGN.CENTER)
    x += card_w + card_gap

# Why it's a moat
moat_top = Inches(4.4)
moat_h = Inches(2.4)
card2 = add_rounded_rect(sl, MARGIN, moat_top, CONTENT_W, moat_h, CARD_BG)
tf = add_text_box(sl, Inches(0.9), moat_top + Inches(0.15), Inches(11.3), Inches(0.35),
                  "De ce este o barieră de intrare:", font_size=17, color=WHITE, bold=True)
moat_bullets = [
    "Fără API-uri publice — automatizare browser obligatorie (Playwright)",
    "Fiecare furnizor = flux unic de login, CAPTCHA, sesiune, navigare",
    "Gestionare concurență: max 2 sincronizări simultane, retry, cleanup",
    "Un concurent ar avea nevoie de 6-12 luni doar pentru crawlere",
]
for b in moat_bullets:
    add_paragraph(tf, f"→  {b}", font_size=15, color=LIGHT_GRAY, space_before=Pt(7))

slide_number(sl, 5)

# ============================================================
# SLIDE 6: AI Pipeline
# ============================================================
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(sl)
logo_bar(sl)
add_tag(sl, MARGIN, TAG_TOP, "INTELIGENȚĂ ARTIFICIALĂ", VIOLET)

add_text_box(sl, MARGIN, TITLE_TOP, Inches(11), Inches(0.7),
             "Specialiști AI dinamici. Powered by GPT-4o.",
             font_size=34, color=WHITE, bold=True)

# Left column: flow
flow_items = [
    ("1. Generalist", "Evaluează toate rezultatele, identifică probleme"),
    ("2. Recomandă", "Pe baza rezultatelor, nu o listă fixă — orice specialitate"),
    ("3. Analizează", "Fiecare specialist primește biomarkerii relevanți"),
    ("Exemple:", "Cardiolog, Endocrinolog, Hematolog, Nefrolog..."),
    ("Dinamic:", "Probleme dermatologice → Dermatolog AI"),
]
y = BODY_TOP
row_h = Inches(0.5)
row_gap = Inches(0.08)
for label, desc in flow_items:
    add_rounded_rect(sl, MARGIN, y, Inches(5.8), row_h, CARD_BG)
    add_text_box(sl, Inches(0.75), y + Inches(0.06), Inches(1.8), Inches(0.38),
                 label, font_size=14, color=TEAL, bold=True)
    add_text_box(sl, Inches(2.6), y + Inches(0.06), Inches(3.6), Inches(0.38),
                 desc, font_size=13, color=LIGHT_GRAY)
    y += row_h + row_gap

# Right column: features card
features_top = BODY_TOP
features_h = Inches(4.0)
card = add_rounded_rect(sl, Inches(6.7), features_top, Inches(6.0), features_h, CARD_BG)
tf = add_text_box(sl, Inches(7.0), features_top + Inches(0.15), Inches(5.4), Inches(3.6),
                  "Funcționalități AI pipeline:", font_size=17, color=WHITE, bold=True)
features = [
    "Extrage 150+ tipuri biomarkeri din PDF-uri românești",
    "Normalizează denumiri între furnizori",
    "Detectează tendințe pe date istorice",
    "Output bilingv (Română + Engleză)",
    "Recomandări lifestyle bazate pe rezultate",
    "Screening-uri preventive recomandate",
]
for f in features:
    add_paragraph(tf, f"✓  {f}", font_size=14, color=LIGHT_GRAY, space_before=Pt(7))

slide_number(sl, 6)

# ============================================================
# SLIDE 7: Securitate & Conformitate
# ============================================================
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(sl)
logo_bar(sl)
add_tag(sl, MARGIN, TAG_TOP, "SECURITATE", GREEN)

add_text_box(sl, MARGIN, TITLE_TOP, Inches(12), Inches(0.7),
             "Criptare per utilizator. Nici admin-ul nu vede datele.",
             font_size=34, color=WHITE, bold=True)

sec_cards = [
    ("Vault per utilizator", "AES-256-GCM",
     "Fiecare user are propria cheie\nderivată din parolă\n(PBKDF2, 600K iterații)"),
    ("Recovery key", "Generat la înregistrare",
     "Singura metodă de recuperare\ndacă parola e pierdută.\nAdmin-ul NU poate ajuta."),
    ("GDPR complet", "Export + Ștergere",
     "Export toate datele (JSON)\nȘtergere cont permanentă\nConsimțământ cookies"),
    ("Autentificare", "JWT + Google OAuth",
     "Rate limiting pe auth\nAudit logging\nHTTPS + security headers"),
]
card_w = Inches(2.9)
card_gap = Inches(0.15)
x = MARGIN
for title, subtitle, desc in sec_cards:
    card = add_rounded_rect(sl, x, BODY_TOP, card_w, Inches(3.2), CARD_BG)
    add_text_box(sl, x + Inches(0.15), BODY_TOP + Inches(0.15), card_w - Inches(0.3), Inches(0.35),
                 title, font_size=16, color=GREEN, bold=True, alignment=PP_ALIGN.CENTER)
    add_text_box(sl, x + Inches(0.15), BODY_TOP + Inches(0.55), card_w - Inches(0.3), Inches(0.35),
                 subtitle, font_size=13, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)
    add_text_box(sl, x + Inches(0.15), BODY_TOP + Inches(1.05), card_w - Inches(0.3), Inches(1.9),
                 desc, font_size=12, color=MID_GRAY, alignment=PP_ALIGN.CENTER)
    x += card_w + card_gap

slide_number(sl, 7)

# ============================================================
# SLIDE 8: Avantaj competitiv — 3 perspective
# ============================================================
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(sl)
logo_bar(sl)
add_tag(sl, MARGIN, TAG_TOP, "AVANTAJ COMPETITIV", AMBER)

add_text_box(sl, MARGIN, TITLE_TOP, Inches(11), Inches(0.7),
             "Trei perspective de expert",
             font_size=34, color=WHITE, bold=True)

perspectives = [
    ("Expert SaaS", CYAN,
     "First-mover pe o piață fără\nconcurenți. Crawlerele sunt\nbariera de intrare — 6-12 luni\nde replicat. Time-to-market\nsavings: 12+ luni și €50-150K."),
    ("Expert Sănătate Digitală", TEAL,
     "Directiva EU EHDS impune\ndigitalizare date medicale.\nCorporate wellness în explozie.\nAsigurătorii caută date\nlongitudinale pentru pricing."),
    ("Expert Evaluare Startup", AMBER,
     "Build vs Buy: 2-3 seniori ×\n12 luni = €72K-180K + risc.\nCu achiziția: produs funcțional\nimediat, fără risc de eșec.\nValoarea e în execuție."),
]
card_w = Inches(3.9)
card_gap = Inches(0.2)
x = MARGIN
for title, color, text in perspectives:
    card = add_rounded_rect(sl, x, BODY_TOP, card_w, Inches(4.0), CARD_BG)
    add_text_box(sl, x + Inches(0.25), BODY_TOP + Inches(0.2), card_w - Inches(0.5), Inches(0.4),
                 title, font_size=19, color=color, bold=True)
    add_text_box(sl, x + Inches(0.25), BODY_TOP + Inches(0.75), card_w - Inches(0.5), Inches(3.0),
                 text, font_size=15, color=LIGHT_GRAY)
    x += card_w + card_gap

slide_number(sl, 8)

# ============================================================
# SLIDE 9: Model de preț incremental
# ============================================================
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(sl)
logo_bar(sl)
add_tag(sl, MARGIN, TAG_TOP, "EVALUARE", AMBER)

add_text_box(sl, MARGIN, TITLE_TOP, Inches(11), Inches(0.6),
             "Model de preț incremental",
             font_size=34, color=WHITE, bold=True)

add_text_box(sl, MARGIN, Inches(2.1), Inches(11), Inches(0.4),
             "Prețul crește cu fiecare etapă de maturitate. Platforma se află în Etapa 2.",
             font_size=16, color=LIGHT_GRAY)

stages = [
    ("Etapa 1", "Funcțional,\nnelansat", "15.000 –\n30.000 €",
     "Cod sursă, crawlere,\nAI pipeline. 50% risk\ndiscount.", MID_GRAY),
    ("Etapa 2", "Lansat, primii\nutilizatori", "35.000 –\n60.000 €",
     "Live, 8 users, infra\ncompletă. 3-6 luni\nsuport tranziție.", TEAL),
    ("Etapa 3", "Tracțiune\n100+ plătitori", "60.000 –\n120.000 €",
     "Venituri recurente,\n2-4x ARR +\nvaloare active.", CYAN),
    ("Etapa 4", "Scale\n1000+ plătitori", "150.000 –\n300.000 €",
     "Achiziție strategică,\n5-8x ARR, brand\nrecunoscut.", AMBER),
]
card_w = Inches(3.0)
card_h = Inches(4.2)
card_gap = Inches(0.1)
cards_top = Inches(2.7)
x = MARGIN
for name, subtitle, price, desc, color in stages:
    is_current = name == "Etapa 2"
    card = add_rounded_rect(sl, x, cards_top, card_w, card_h, CARD_BG)
    if is_current:
        highlight = add_rounded_rect(sl, x - Inches(0.03), cards_top - Inches(0.03),
                                     card_w + Inches(0.06), card_h + Inches(0.06), TEAL)
        highlight.fill.background()
        highlight.line.color.rgb = TEAL
        highlight.line.width = Pt(2.5)

    tag_text = name + ("  ← ACUM" if is_current else "")
    add_text_box(sl, x + Inches(0.1), cards_top + Inches(0.15), card_w - Inches(0.2), Inches(0.3),
                 tag_text, font_size=13, color=color, bold=True, alignment=PP_ALIGN.CENTER)
    add_text_box(sl, x + Inches(0.1), cards_top + Inches(0.5), card_w - Inches(0.2), Inches(0.55),
                 subtitle, font_size=12, color=MID_GRAY, alignment=PP_ALIGN.CENTER)
    add_text_box(sl, x + Inches(0.1), cards_top + Inches(1.15), card_w - Inches(0.2), Inches(0.9),
                 price, font_size=24, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)
    add_text_box(sl, x + Inches(0.1), cards_top + Inches(2.3), card_w - Inches(0.2), Inches(1.6),
                 desc, font_size=12, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)
    x += card_w + card_gap

slide_number(sl, 9)

# ============================================================
# SLIDE 10: Build vs Buy
# ============================================================
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(sl)
logo_bar(sl)
add_tag(sl, MARGIN, TAG_TOP, "BUILD VS BUY", CYAN)

add_text_box(sl, MARGIN, TITLE_TOP, Inches(11), Inches(0.7),
             "De ce să cumperi, nu să construiești?",
             font_size=34, color=WHITE, bold=True)

col_w = Inches(3.8)
col_gap = Inches(0.25)
col_h = Inches(4.2)
col_top = BODY_TOP
cols = [
    (MARGIN, "DACĂ CONSTRUIEȘTI", "€72.000 – 180.000", "+ 12 luni minim",
     "2-3 programatori seniori\nReverse-engineering crawlere\nPipeline AI de la zero\nSecuritate & GDPR\nNicio garanție de succes",
     RED, False),
    (MARGIN + col_w + col_gap, "DACĂ CUMPERI", "€35.000 – 60.000", "Imediat",
     "Produs funcțional azi\n4 crawlere deja construite\nPipeline AI operațional\nGDPR conformant\nUtilizatori reali",
     TEAL, True),
    (MARGIN + 2 * (col_w + col_gap), "ALTERNATIV: LICENȚĂ", "€500 – 2.000", "Per lună, per client",
     "White-label sub brand-ul tău\nDomeniu propriu\nMentenanță inclusă\nFără cost inițial mare\nOpțiune revenue share",
     VIOLET, False),
]
for x, header, price, time_label, items, color, bordered in cols:
    card = add_rounded_rect(sl, x, col_top, col_w, col_h, CARD_BG)
    if bordered:
        card.line.color.rgb = color
        card.line.width = Pt(2)
    add_text_box(sl, x + Inches(0.15), col_top + Inches(0.15), col_w - Inches(0.3), Inches(0.3),
                 header, font_size=13, color=color, bold=True, alignment=PP_ALIGN.CENTER)
    add_text_box(sl, x + Inches(0.15), col_top + Inches(0.55), col_w - Inches(0.3), Inches(0.6),
                 price, font_size=30, color=color, bold=True, alignment=PP_ALIGN.CENTER)
    add_text_box(sl, x + Inches(0.15), col_top + Inches(1.25), col_w - Inches(0.3), Inches(0.35),
                 time_label, font_size=16, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)
    add_text_box(sl, x + Inches(0.15), col_top + Inches(1.8), col_w - Inches(0.3), Inches(2.2),
                 items, font_size=13, color=MID_GRAY, alignment=PP_ALIGN.CENTER)

slide_number(sl, 10)

# ============================================================
# SLIDE 11: Modele de tranzacție
# ============================================================
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(sl)
logo_bar(sl)
add_tag(sl, MARGIN, TAG_TOP, "OPȚIUNI", TEAL)

add_text_box(sl, MARGIN, TITLE_TOP, Inches(11), Inches(0.7),
             "Trei modele de tranzacție",
             font_size=34, color=WHITE, bold=True)

models = [
    ("A", "Vânzare de active", "35.000 – 60.000 EUR",
     "Preț unic. Cod sursă complet,\ndomeniu, infrastructură, bază de\ndate, documentație.\n3-6 luni suport tranziție.\n\nIdeal: companii cu echipă\ntehnică proprie.",
     CYAN),
    ("B", "Licență White-Label", "500 – 2.000 EUR / lună",
     "Platformă sub brand-ul tău,\ndomeniu propriu. Mentenanță\ncrawlere, actualizări, hosting,\nsuport tehnic incluse.\n\nIdeal: clinici, asigurători,\nwellness.",
     VIOLET),
    ("C", "Parteneriat Revenue Share", "10K–20K EUR + 20-40%",
     "Investiție inițială redusă.\nAcces complet la platformă.\nDezvoltare continuă.\n\nIdeal: investitori care vor\nupside pe termen lung.",
     AMBER),
]
card_w = Inches(3.9)
card_gap = Inches(0.2)
card_h = Inches(4.4)
x = MARGIN
for letter, title, price, desc, color in models:
    card = add_rounded_rect(sl, x, BODY_TOP, card_w, card_h, CARD_BG)
    # Letter circle
    circ_size = Inches(0.55)
    circ = sl.shapes.add_shape(MSO_SHAPE.OVAL,
                               x + (card_w - circ_size) // 2, BODY_TOP + Inches(0.15),
                               circ_size, circ_size)
    circ.fill.solid()
    circ.fill.fore_color.rgb = color
    circ.line.fill.background()
    p = circ.text_frame.paragraphs[0]
    p.text = letter
    p.font.size = Pt(20)
    p.font.color.rgb = WHITE
    p.font.bold = True
    p.alignment = PP_ALIGN.CENTER
    circ.text_frame.margin_top = Pt(1)

    add_text_box(sl, x + Inches(0.15), BODY_TOP + Inches(0.85), card_w - Inches(0.3), Inches(0.35),
                 title, font_size=17, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)
    add_text_box(sl, x + Inches(0.15), BODY_TOP + Inches(1.25), card_w - Inches(0.3), Inches(0.35),
                 price, font_size=14, color=color, bold=True, alignment=PP_ALIGN.CENTER)
    add_text_box(sl, x + Inches(0.15), BODY_TOP + Inches(1.75), card_w - Inches(0.3), Inches(2.4),
                 desc, font_size=12, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)
    x += card_w + card_gap

slide_number(sl, 11)

# ============================================================
# SLIDE 12: Tracțiune actuală
# ============================================================
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(sl)
logo_bar(sl)
add_tag(sl, MARGIN, TAG_TOP, "TRACȚIUNE", GREEN)

add_text_box(sl, MARGIN, TITLE_TOP, Inches(11), Inches(0.6),
             "Early, dar real",
             font_size=34, color=WHITE, bold=True)

stats = [
    ("8", "Utilizatori\nînregistrați"),
    ("59", "Documente\nprocesate"),
    ("731", "Biomarkeri\nextrași"),
    ("100%", "Uptime\n(3 luni)"),
]
stat_w = Inches(2.9)
stat_gap = Inches(0.15)
x = MARGIN
for val, label in stats:
    card = add_rounded_rect(sl, x, BODY_TOP, stat_w, Inches(1.6), CARD_BG)
    add_text_box(sl, x + Inches(0.1), BODY_TOP + Inches(0.1), stat_w - Inches(0.2), Inches(0.7),
                 val, font_size=40, color=CYAN, bold=True, alignment=PP_ALIGN.CENTER)
    add_text_box(sl, x + Inches(0.1), BODY_TOP + Inches(0.85), stat_w - Inches(0.2), Inches(0.6),
                 label, font_size=14, color=LIGHT_GRAY, alignment=PP_ALIGN.CENTER)
    x += stat_w + stat_gap

# What's included
inc_top = Inches(4.4)
inc_h = Inches(2.5)
card = add_rounded_rect(sl, MARGIN, inc_top, CONTENT_W, inc_h, CARD_BG)
add_text_box(sl, Inches(0.85), inc_top + Inches(0.12), Inches(5), Inches(0.35),
             "Ce primește cumpărătorul:", font_size=17, color=WHITE, bold=True)

left_items = [
    "✓  Cod sursă complet (frontend + backend)",
    "✓  4 crawlere funcționale",
    "✓  Agenți AI specialiști dinamici",
    "✓  Domeniu: analize.online",
    "✓  Certificat SSL (valid Apr 2026)",
    "✓  Infrastructură VPS producție",
]
right_items = [
    "✓  Bază de date PostgreSQL",
    "✓  Monitorizare Prometheus + Grafana",
    "✓  Email AWS SES configurat",
    "✓  Plăți Netopia integrate",
    "✓  Documentație completă",
    "✓  3-6 luni suport tranziție",
]

tf = add_text_box(sl, Inches(0.85), inc_top + Inches(0.5), Inches(5.5), Inches(1.8),
                  "", font_size=13, color=LIGHT_GRAY)
tf.paragraphs[0].text = ""
for item in left_items:
    add_paragraph(tf, item, font_size=13, color=LIGHT_GRAY, space_before=Pt(2), space_after=Pt(1))

tf2 = add_text_box(sl, Inches(6.5), inc_top + Inches(0.5), Inches(5.8), Inches(1.8),
                   "", font_size=13, color=LIGHT_GRAY)
tf2.paragraphs[0].text = ""
for item in right_items:
    add_paragraph(tf2, item, font_size=13, color=LIGHT_GRAY, space_before=Pt(2), space_after=Pt(1))

slide_number(sl, 12)

# ============================================================
# SLIDE 13: Riscuri (transparență)
# ============================================================
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(sl)
logo_bar(sl)
add_tag(sl, MARGIN, TAG_TOP, "TRANSPARENȚĂ", AMBER)

add_text_box(sl, MARGIN, TITLE_TOP, Inches(11), Inches(0.6),
             "Riscuri și cum le adresăm",
             font_size=34, color=WHITE, bold=True)

risks = [
    ("Crawlerele se pot strica", "Medie",
     "Cod modular, documentat. Update tipic: 1-3 zile per crawler"),
    ("Bus factor = 1", "Medie",
     "Cod curat, documentație completă, tranziție asistată 3-6 luni"),
    ("Dependență OpenAI", "Scăzută",
     "Pipeline modular — înlocuibil cu Claude, Gemini, sau model local"),
    ("GDPR / date medicale", "Scăzută",
     "Criptare per user, export date, ștergere cont funcționale"),
    ("Scalare", "Scăzută",
     "PostgreSQL, async architecture, concurrency limits"),
]

row_h = Inches(0.75)
row_gap = Inches(0.1)
y = BODY_TOP
for risk, severity, mitigation in risks:
    card = add_rounded_rect(sl, MARGIN, y, CONTENT_W, row_h, CARD_BG)
    sev_color = AMBER if severity == "Medie" else GREEN
    add_text_box(sl, Inches(0.85), y + Inches(0.05), Inches(3.0), Inches(0.3),
                 risk, font_size=15, color=WHITE, bold=True)
    add_text_box(sl, Inches(0.85), y + Inches(0.38), Inches(1.5), Inches(0.25),
                 severity, font_size=12, color=sev_color, bold=True)
    add_text_box(sl, Inches(4.2), y + Inches(0.15), Inches(8.2), Inches(0.45),
                 mitigation, font_size=14, color=LIGHT_GRAY)
    y += row_h + row_gap

slide_number(sl, 13)

# ============================================================
# SLIDE 14: Contact / CTA
# ============================================================
sl = prs.slides.add_slide(prs.slide_layouts[6])
set_slide_bg(sl)

add_text_box(sl, Inches(1), Inches(1.2), Inches(11.3), Inches(1.2),
             "Programează un demo live\nde 15 minute.",
             font_size=42, color=WHITE, bold=True, alignment=PP_ALIGN.CENTER)

# CTA card
cta_w = Inches(7)
cta_h = Inches(2.8)
cta_left = (SLIDE_W - cta_w) // 2
cta = add_rounded_rect(sl, cta_left, Inches(3.0), cta_w, cta_h, TEAL)
add_text_box(sl, cta_left + Inches(0.3), Inches(3.2), cta_w - Inches(0.6), Inches(0.35),
             "Contact", font_size=16, color=RGBColor(0xFF, 0xFF, 0xFF), alignment=PP_ALIGN.CENTER)
add_text_box(sl, cta_left + Inches(0.3), Inches(3.65), cta_w - Inches(0.6), Inches(0.55),
             "Bogdan Drăgușin", font_size=30, color=RGBColor(0xFF, 0xFF, 0xFF), bold=True,
             alignment=PP_ALIGN.CENTER)
add_text_box(sl, cta_left + Inches(0.3), Inches(4.3), cta_w - Inches(0.6), Inches(0.35),
             "contact@analize.online", font_size=18, color=RGBColor(0xFF, 0xFF, 0xFF),
             alignment=PP_ALIGN.CENTER)
add_text_box(sl, cta_left + Inches(0.3), Inches(4.85), cta_w - Inches(0.6), Inches(0.35),
             "Demo live:  analize.online", font_size=15, color=RGBColor(0xE0, 0xFF, 0xF0),
             alignment=PP_ALIGN.CENTER)

add_text_box(sl, Inches(1), Inches(6.4), Inches(11.3), Inches(0.4),
             "Prețul nu va fi niciodată mai mic decât astăzi.",
             font_size=17, color=AMBER, bold=True, alignment=PP_ALIGN.CENTER)

slide_number(sl, 14)

# ============================================================
# SAVE
# ============================================================
out_path = "C:/OldD/_Projects/Healthy/sale/AnalizeOnline-Pitch-RO.pptx"
prs.save(out_path)
print(f"Saved: {out_path}")
