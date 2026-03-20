# LinkedIn Posts — analize.online (Romanian)

---

## Post 1: Lansare / Awareness

**Platforma pe care pacienții din România ar fi meritat-o de mult timp.**

Milioane de români au analize de sânge la Regina Maria, Synevo, MedLife sau Sanador. Fiecare pe alt portal, cu alt login, alt format. Când medicul întreabă „cum a evoluat fierul în ultimii doi ani?", răspunsul e de cele mai multe ori: „nu știu, trebuie să caut prin trei conturi diferite."

Analize.Online rezolvă această problemă. Este prima platformă din România care agregă rezultatele medicale din mai multe laboratoare într-un singur loc. Utilizatorii își conectează conturile de laborator, iar platforma descarcă automat documentele, extrage biomarkerii și arată evoluția fiecărui parametru în timp.

În plus, un motor AI bazat pe GPT-4o analizează rezultatele prin prisma mai multor specialități medicale — cardiologie, endocrinologie, hematologie — și generează un raport cu observații și recomandări. Nu înlocuiește medicul, dar pregătește pacientul pentru consultație.

Toate datele sunt criptate cu cheie unică per utilizator (AES-256-GCM). Nimeni din echipă, inclusiv administratorii, nu are acces la datele medicale ale utilizatorilor.

Încearcă gratuit: https://analize.online

#DigitalHealth #HealthTech #SănătateDigitală #România #analizeonline

---

## Post 2: Abordare tehnică

**Ce presupune construirea unei platforme de sănătate digitală în România, fără API-uri publice?**

Răspunsul scurt: crawlere, răbdare și o obsesie pentru securitate.

Laboratoarele din România nu oferă API-uri publice pentru accesul la rezultate. Am dezvoltat web crawlere cu Playwright care se autentifică pe portalurile pacienților, navighează interfețele (inclusiv reCAPTCHA) și descarcă PDF-urile cu rezultate. Fiecare laborator reprezintă o provocare separată — structuri diferite, fluxuri de autentificare diferite, formate de documente diferite.

Odată descărcate, un pipeline AI bazat pe GPT-4o extrage biomarkerii din PDF-uri: denumire, valoare, unitate de măsură, interval de referință. Apoi, agenți AI specializați pe cardiologie, endocrinologie, hematologie, hepatologie și nefrologie analizează datele și generează rapoarte.

Securitatea a fost prioritatea noastră principală. Fiecare utilizator are propriul vault criptat cu AES-256-GCM, derivat din parola sa. Cheia de criptare nu e stocată nicăieri în clar. Nici cu acces direct la baza de date nu pot fi citite datele medicale ale unui utilizator.

Stiva tehnologică: FastAPI, React, PostgreSQL, Playwright, OpenAI API.

Platforma e live: https://analize.online

#HealthTech #Python #FastAPI #AI #CyberSecurity

---

## Post 3: Oportunitate de piață / Parteneriate

**România are 18 milioane de oameni și zero infrastructură pentru agregarea datelor medicale personale.**

Directiva europeană EHDS (European Health Data Space) impune statelor membre să faciliteze accesul cetățenilor la propriile date de sănătate, în format digital, interoperabil. Termenul se apropie, iar România pornește de la zero.

Analize.Online este prima platformă românească care agregă rezultate medicale din laboratoare (Regina Maria, Synevo, MedLife, Sanador), extrage biomarkeri automat cu AI și oferă rapoarte de interpretare pe specialități medicale. Platforma e live, funcțională, conformă GDPR, bilingvă RO/EN, cu criptare per utilizator.

Piața e neocupată. Nu există un concurent direct în România. Laboratoarele nu oferă această funcționalitate, iar pacienții își gestionează datele medicale în PDF-uri dispersate pe mai multe portaluri.

Căutăm parteneri strategici — fie din zona de sănătate (clinici, laboratoare, asigurători), fie din zona de tehnologie (investitori, acceleratoare) — pentru a scala platforma. Infrastructura tehnică există. Ce lipsește: distribuție, parteneriate cu furnizori medicali și capital pentru creștere.

Dacă lucrați în healthtech, digital health sau investiții early-stage, ne-ar face plăcere să discutăm.

https://analize.online

#HealthTech #EHDS #DigitalHealth #StartupRomânia #InvestițiiSănătate
