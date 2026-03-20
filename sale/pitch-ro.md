# Analize.Online — Pitch de Vânzare

**Prima platformă din România care unifică toate analizele medicale cu inteligență artificială**

*Confidențial — Martie 2026*

---

## 1. Problema

### Datele medicale din România sunt fragmentate și inaccesibile

România are **19 milioane de locuitori** și **4 furnizori majori de analize medicale**: Regina Maria, Synevo, MedLife și Sanador. Fiecare furnizor are propriul portal, propriul format de rezultate, propria experiență de utilizator.

**Ce se întâmplă în realitate:**
- Pacienții își fac analize la furnizori diferiți pe parcursul vieții
- Rezultatele rămân blocate în portaluri separate — nimeni nu vede imaginea de ansamblu
- PDF-urile conțin sute de valori — imposibil de interpretat fără medic
- Nu există urmărirea tendințelor — colesterolul a crescut sau a scăzut față de anul trecut?
- Vizitele la medic sunt reactive, nu preventive — pacienții merg doar când sunt deja bolnavi

**Dimensiunea problemei:**
- 19M+ persoane potențiale
- 4 furnizori mari + zeci de laboratoare mici
- **Zero platforme** care agregă datele între furnizori
- Zero interoperabilitate între sistemele medicale

### Context european: Directiva EHDS

Uniunea Europeană a adoptat **European Health Data Space (EHDS)** — o directivă care obligă statele membre să faciliteze accesul cetățenilor la propriile date medicale digitale. România va trebui să se conformeze, iar piața de soluții digitale de sănătate va exploda.

---

## 2. Soluția: Analize.Online

### Un singur loc pentru toate analizele tale, cu AI care le explică

**Fluxul complet:**

```
Conectezi conturile     →  Crawlerele descarcă    →  AI-ul extrage      →  Specialiștii     →  Grafice și
(Regina Maria, Synevo,     automat toate PDF-urile    fiecare biomarker     AI analizează       alerte în
MedLife, Sanador)          din fiecare furnizor       din fiecare PDF       rezultatele          timp real
```

**Cum funcționează:**

1. **Conectare conturi** — Utilizatorul își adaugă conturile de la furnizorii medicali. Credențialele sunt criptate cu AES-256-GCM, pe cheie derivată din parola utilizatorului. Nici administratorul platformei nu le poate vedea.

2. **Sincronizare automată** — Crawlere Playwright (automatizare browser) descarcă automat toate documentele PDF. Gestionare CAPTCHA inclusă, retry automat, detectare erori.

3. **Extracție AI** — GPT-4o citește fiecare PDF și extrage toți biomarkerii: nume, valoare, unitate, interval de referință. Peste 150 de tipuri de biomarkeri normalizați.

4. **Analiză specialist** — 6 agenți AI specialiști interpretează rezultatele:
   - **Generalist** — Evaluare completă, identifică probleme
   - **Cardiolog** — Profil lipidic, markeri cardiaci
   - **Endocrinolog** — Tiroidă, diabet, hormoni
   - **Hematolog** — Hemoleucogramă, anemie, coagulare
   - **Hepatolog** — Enzime hepatice, funcție hepatică
   - **Nefrolog** — Funcție renală, creatinină

5. **Vizualizare și alerte** — Grafice interactive cu evoluția fiecărui biomarker în timp. Alerte vizuale pentru valori anormale (HIGH/LOW). Recomandări de screening preventiv.

---

## 3. Ce include platforma (Inventar cuantificat)

| Categorie | Cantitate | Detalii |
|-----------|-----------|---------|
| **Servicii backend** | 28 | ~11.000 linii Python (FastAPI) |
| **Endpoint-uri API** | 50+ | 16 routere |
| **Modele bază de date** | 30+ | Schema relațională completă (PostgreSQL) |
| **Pagini frontend** | 20+ | React 18 + Vite + Tailwind CSS |
| **Crawlere furnizori** | 4 | Playwright cu gestionare CAPTCHA |
| **Agenți AI specialiști** | 6 | GPT-4o cu prompt-uri specializate |
| **Tipuri biomarkeri** | 150+ | Normalizați, categorizați, cu urmărire tendințe |
| **Limbi** | 2 | Română + Engleză (i18next) |
| **Criptare** | AES-256-GCM | Vault per utilizator, cheie derivată din parolă |
| **Plăți** | Netopia | Integrare completă (29 RON/lună Premium, 49 RON/lună Family) |
| **Email** | AWS SES | Verificare email, notificări |
| **Monitorizare** | Prometheus + Grafana | Dashboard-uri, alerte automate |
| **GDPR** | Complet | Export date, ștergere cont, consimțământ, cookies |
| **Autentificare** | JWT + Google OAuth | Rate limiting, audit logging |

### Ce nu se vede, dar contează

- **Sistem de criptare per utilizator** — Fiecare utilizator are propria cheie de criptare derivată din parolă (PBKDF2, 600.000 iterații). Cheia vault este criptată cu cheia derivată. Cheia de recuperare (recovery key) este generată la înregistrare. Nici administratorul platformei nu poate accesa datele utilizatorilor.

- **Gestionare concurență** — Maximum 2 sincronizări simultane, maximum 3 procesări documente simultane, timeout-uri, cleanup automat, limită de eșecuri consecutive.

- **Infrastructură producție** — Domeniu analize.online, SSL Let's Encrypt, Nginx reverse proxy, servicii systemd, backup scripts, runbook-uri de operare.

---

## 4. Avantaj competitiv — Trei perspective de expert

### Expert SaaS: "First-mover cu moat tehnic"

> **Crawlerele sunt bariera de intrare.** Furnizorii medicali din România nu au API-uri publice. Fiecare crawler a necesitat luni de reverse-engineering: fluxuri de login unice, gestionare CAPTCHA, sesiuni, navigare multi-pagină. Un concurent ar avea nevoie de **6-12 luni** doar pentru crawlere.
>
> **Time-to-market savings:** O echipă de 2-3 seniori ar avea nevoie de 12+ luni și €50-150K să construiască de la zero. Cu achiziția, un cumpărător este pe piață **imediat**.
>
> **Moat acumulativ:** Cu fiecare utilizator nou, platforma acumulează date despre structura PDF-urilor, edge cases, tipuri de biomarkeri — know-how imposibil de replicat fără utilizatori reali.

### Expert sănătate digitală: "Timing-ul perfect"

> **Directiva EU EHDS** (European Health Data Space) obligă statele membre să faciliteze accesul la date medicale. România va trebui să se conformeze — iar companiile care au deja infrastructura vor fi în avantaj masiv.
>
> **Corporate wellness în explozie:** Companiile mari din România oferă deja pachete de sănătate angajaților (7card, SanoPass, Benefit). Un add-on care agregă și interpretează analizele medicale = diferențiator puternic.
>
> **Asigurări preventive:** Asigurătorii caută date longitudinale de sănătate pentru pricing predictiv. O platformă care centralizează analizele = partener strategic natural.

### Expert evaluare startup: "Build vs. Buy clar în favoarea Buy"

> **Cost de reconstrucție:**
> - 2-3 programatori seniori × 12 luni × €3.000-5.000/lună = **€72.000-180.000**
> - Plus costuri de management, QA, infrastructură, domeniu, SSL, monitoring
> - Plus **risc de eșec** — crawlerele pot să nu funcționeze, AI-ul poate să nu extragă corect
>
> **Ce cumperi vs. ce construiești:**
> - Cumperi: produs funcțional, testat, live, cu utilizatori reali — **imediat**
> - Construiești: speranța că peste 12 luni vei avea ceva similar — **poate**
>
> **Valoarea este în execuție**, nu în idee. Ideea de "agregare analize" este simplă. Execuția (crawlere, AI, criptare, GDPR, plăți) este complexă și dovedită.

---

## 5. Model de preț incremental

### Prețul crește cu fiecare etapă de maturitate

Platforma se află în **Etapa 2** — lansată, cu utilizatori reali, dar fără venituri semnificative. Prețul reflectă stadiul actual și potențialul demonstrat.

---

### Etapa 1: Funcțional, nelansat
**Preț: 15.000 – 30.000 EUR**

| Element | Detalii |
|---------|---------|
| Ce cumperi | Cod sursă, crawlere, AI pipeline, frontend |
| Stare | Funcțional local, netestat pe piață |
| Risc | Mare — nu se știe dacă piața plătește |
| Discount | ~50% reducere pentru risc (vs. cost reconstrucție) |
| Justificare | Economisești 6-12 luni de dezvoltare |
| Model | Vânzare de active (asset sale) |

---

### Etapa 2: Lansat, primii utilizatori ← **STADIUL ACTUAL**
**Preț: 35.000 – 60.000 EUR**

| Element | Detalii |
|---------|---------|
| Ce cumperi | Tot de la Etapa 1 + infrastructură producție + domeniu + utilizatori |
| Stare | Live la analize.online, 8 utilizatori, 731 biomarkeri extrași |
| Risc | Mediu — produsul funcționează, piața nu e validată complet |
| Premium | +20-30% față de Etapa 1 (validare reală) |
| Justificare | Produs dovedit, nu prototip |
| Include | Domeniu analize.online, SSL, VPS, Prometheus/Grafana, AWS SES |
| Suport tranziție | 3-6 luni asistență de la dezvoltator |

**De ce merită prețul:**
- Funcționează **acum** — demo live disponibil
- 4 crawlere testate cu date reale
- Criptare per utilizator implementată complet
- Conformitate GDPR completă
- Integrare plăți Netopia gata
- Monitorizare și alerte active

---

### Etapa 3: Tracțiune, 100+ clienți plătitori
**Preț: 60.000 – 120.000 EUR**

| Element | Detalii |
|---------|---------|
| Ce cumperi | Platformă cu venituri recurente dovedite |
| Stare | 100+ clienți plătitori, venituri recurente lunare |
| Calcul | 2-4x ARR (Annual Recurring Revenue) + valoare active |
| Exemplu | 200 clienți × 29 RON/lună = ~€14.000 ARR → evaluare €28.000-56.000 + active |
| Risc | Scăzut — modelul de business este validat |

---

### Etapa 4: Scale, 1.000+ clienți plătitori
**Preț: 150.000 – 300.000 EUR**

| Element | Detalii |
|---------|---------|
| Ce cumperi | Platformă scalabilă cu bază solidă de clienți |
| Stare | 1.000+ clienți, brand recunoscut, venituri stabile |
| Calcul | 5-8x ARR + primă strategică |
| Exemplu | 1.000 clienți × 29 RON/lună = ~€70.000 ARR → evaluare €350.000-560.000 |
| Cumpărători tipici | MedLife, Regina Maria, Medicover — achiziție strategică |

---

### Vizual: Traiectoria prețului

```
EUR
300K ┤                                          ╭────── Etapa 4
     │                                    ╭─────╯      (Scale)
150K ┤                              ╭─────╯
     │                        ╭─────╯
120K ┤                  ╭─────╯  Etapa 3
     │            ╭─────╯       (Tracțiune)
 60K ┤      ╭─────╯
     │ ╭────╯  Etapa 2 ← ACUM
 35K ┤─╯      (Lansat)
     │
 15K ┤  Etapa 1
     │  (Funcțional)
   0 ┼────────────────────────────────────────────→ Timp/Maturitate
```

> **Prețul nu va fi niciodată mai mic decât astăzi.** Fiecare utilizator nou, fiecare lună de uptime, fiecare crawler actualizat crește valoarea platformei.

---

## 6. Modele de tranzacție

### Opțiunea A: Vânzare de active (Asset Sale)
- **Preț unic:** 35.000 – 60.000 EUR (stadiul actual)
- **Ce primești:** Cod sursă complet, domeniu, infrastructură, bază de date, documentație
- **Suport:** 3-6 luni asistență de la dezvoltator pentru tranziție
- **Ideal pentru:** Companii care vor control total și au echipă tehnică proprie

### Opțiunea B: Licență White-Label
- **Preț lunar:** 500 – 2.000 EUR/lună (în funcție de volum)
- **Ce primești:** Platformă sub brand-ul tău, domeniu propriu, personalizare vizuală
- **Include:** Mentenanță crawlere, actualizări, hosting, suport tehnic
- **Ideal pentru:** Clinici, asigurători, companii wellness care nu vor să gestioneze tehnologia

### Opțiunea C: Parteneriat Revenue Share
- **Investiție inițială:** Redusă (10.000 – 20.000 EUR)
- **Revenue share:** 20-40% din veniturile generate
- **Ce primești:** Acces complet la platformă, dezvoltare continuă
- **Ideal pentru:** Investitori care vor upside pe termen lung

---

## 7. Ce riscuri există (și cum le adresăm)

### Transparență completă

| Risc | Severitate | Mitigare |
|------|-----------|----------|
| **Crawlerele se pot strica** dacă furnizorii își schimbă site-urile | Medie | Cod modular, documentat. Actualizare tipică: 1-3 zile de muncă per crawler |
| **Bus factor = 1** (un singur dezvoltator) | Medie | Cod curat, documentație completă (CLAUDE.md, MAINTENANCE.md, runbook-uri). Tranziție asistată 3-6 luni |
| **Dependență de OpenAI** (GPT-4o) | Scăzută | Pipeline modular — se poate înlocui cu Claude, Gemini, sau model local |
| **GDPR / date medicale** | Scăzută | Criptare per utilizator implementată. Export date, ștergere cont funcționale |
| **Scalare** | Scăzută | PostgreSQL, architecture async, concurrency limits — scalabil orizontal |

---

## 8. Prețuri abonamente pentru utilizatori finali

Prețurile actuale implementate în platformă:

| Plan | Preț | Include |
|------|------|---------|
| **Gratuit** | 0 RON | 50 documente, 3 analize AI/lună, 2 conturi furnizori |
| **Premium** | 29 RON/lună (sau 199 RON/an) | 500 documente, 30 analize AI/lună, toți specialiștii, export PDF |
| **Family** | 49 RON/lună | Tot din Premium + până la 5 membri de familie |

**Potențial de monetizare:**
- La **1.000 utilizatori plătitori** (Premium): ~€7.000/lună = **€84.000/an**
- La **5.000 utilizatori plătitori**: ~€35.000/lună = **€420.000/an**
- **B2B licensing** adaugă €500-2.000/lună per client corporativ

---

## 9. Call to Action

### Programează un demo live de 15 minute

Ți-arăt platforma funcțională — de la autentificare, la sincronizare automată, la rapoarte AI de specialitate.

**Contact:**
- **Bogdan Drăgușin**
- **Email:** contact@analize.online
- **Platformă live:** https://analize.online

> *Platforma funcționează acum. Fiecare zi care trece fără un partener strategic este o zi pierdută pe o piață fără concurență.*

---

*Document generat: Martie 2026 | Confidențial*
