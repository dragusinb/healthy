import React from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { ArrowLeft, Shield, Database, Lock, UserCheck, Trash2, Mail, Globe } from 'lucide-react';

export default function Privacy() {
  const { t, i18n } = useTranslation();
  const isRomanian = i18n.language === 'ro';

  const lastUpdated = '2 Februarie 2026';
  const version = '1.0';

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="max-w-4xl mx-auto px-4 py-12">
        {/* Header */}
        <div className="mb-8">
          <Link
            to="/login"
            className="inline-flex items-center gap-2 text-slate-600 hover:text-primary-600 mb-4"
          >
            <ArrowLeft size={18} />
            {isRomanian ? 'Înapoi' : 'Back'}
          </Link>
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 bg-primary-100 rounded-xl">
              <Shield className="w-8 h-8 text-primary-600" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-slate-800">
                {isRomanian ? 'Politica de Confidențialitate' : 'Privacy Policy'}
              </h1>
              <p className="text-slate-500">
                {isRomanian ? `Versiunea ${version} • Ultima actualizare: ${lastUpdated}` : `Version ${version} • Last updated: February 2, 2026`}
              </p>
            </div>
          </div>
        </div>

        {/* GDPR Badge */}
        <div className="bg-green-50 border border-green-200 rounded-xl p-6 mb-8">
          <div className="flex items-start gap-3">
            <Shield className="w-6 h-6 text-green-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-green-800 mb-2">
                {isRomanian ? 'Conformitate GDPR' : 'GDPR Compliance'}
              </h3>
              <p className="text-green-700 text-sm">
                {isRomanian
                  ? 'Această politică este conformă cu Regulamentul General privind Protecția Datelor (GDPR) al Uniunii Europene. Respectăm drepturile dumneavoastră privind datele personale.'
                  : 'This policy complies with the European Union General Data Protection Regulation (GDPR). We respect your rights regarding personal data.'}
              </p>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-8 space-y-8">
          {isRomanian ? (
            <>
              {/* Romanian Version */}
              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <Database className="w-5 h-5 text-primary-600" />
                  1. Date Colectate
                </h2>
                <p className="text-slate-600 leading-relaxed mb-4">
                  Colectăm următoarele categorii de date personale:
                </p>

                <h3 className="font-semibold text-slate-700 mb-2">1.1. Date de Cont</h3>
                <ul className="list-disc list-inside text-slate-600 space-y-1 ml-4 mb-4">
                  <li>Adresa de email</li>
                  <li>Parola (stocată criptat)</li>
                  <li>Preferințe de limbă</li>
                </ul>

                <h3 className="font-semibold text-slate-700 mb-2">1.2. Date de Profil (opțional)</h3>
                <ul className="list-disc list-inside text-slate-600 space-y-1 ml-4 mb-4">
                  <li>Nume complet</li>
                  <li>Data nașterii</li>
                  <li>Gen</li>
                  <li>Înălțime și greutate</li>
                  <li>Grupa sanguină</li>
                  <li>Alergii și afecțiuni cronice</li>
                </ul>

                <h3 className="font-semibold text-slate-700 mb-2">1.3. Credențiale Furnizori Medicali</h3>
                <ul className="list-disc list-inside text-slate-600 space-y-1 ml-4 mb-4">
                  <li>Nume utilizator și parole pentru conturile furnizorilor medicali</li>
                  <li>Aceste date sunt criptate și stocate în siguranță</li>
                </ul>

                <h3 className="font-semibold text-slate-700 mb-2">1.4. Date Medicale</h3>
                <ul className="list-disc list-inside text-slate-600 space-y-1 ml-4 mb-4">
                  <li>Documente cu analize medicale (PDF-uri)</li>
                  <li>Rezultate ale testelor și biomarkeri extrași</li>
                  <li>Rapoarte de sănătate generate de AI</li>
                </ul>

                <h3 className="font-semibold text-slate-700 mb-2">1.5. Date Tehnice</h3>
                <ul className="list-disc list-inside text-slate-600 space-y-1 ml-4">
                  <li>Adresă IP</li>
                  <li>Tip de browser și dispozitiv</li>
                  <li>Loguri de acces și utilizare</li>
                </ul>
              </section>

              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <Lock className="w-5 h-5 text-primary-600" />
                  2. Cum Folosim Datele
                </h2>
                <div className="space-y-4 text-slate-600 leading-relaxed">
                  <p><strong>2.1.</strong> Furnizarea Serviciului - pentru a vă permite accesul la funcționalitățile platformei.</p>
                  <p><strong>2.2.</strong> Sincronizarea datelor medicale - pentru a descărca automat rezultatele de la furnizorii conectați.</p>
                  <p><strong>2.3.</strong> Generarea rapoartelor AI - pentru a oferi interpretări ale rezultatelor analizelor.</p>
                  <p><strong>2.4.</strong> Comunicări - pentru a vă trimite notificări despre rezultate noi sau alerte de sănătate.</p>
                  <p><strong>2.5.</strong> Îmbunătățirea serviciului - pentru a analiza modul de utilizare și a îmbunătăți platforma.</p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <Globe className="w-5 h-5 text-primary-600" />
                  3. Partajarea Datelor cu Terți
                </h2>
                <div className="space-y-4 text-slate-600 leading-relaxed">
                  <p><strong>3.1. Furnizori de servicii AI</strong> - Folosim OpenAI pentru procesarea și interpretarea documentelor medicale. Datele sunt trimise în formă anonimizată sau pseudonimizată când este posibil.</p>
                  <p><strong>3.2. Procesatori de plăți</strong> - Netopia procesează plățile. Nu stocăm datele cardurilor de credit.</p>
                  <p><strong>3.3. Furnizori de hosting</strong> - Datele sunt stocate pe servere securizate.</p>
                  <p><strong>3.4.</strong> Nu vindem și nu partajăm datele dumneavoastră cu terți în scopuri de marketing.</p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <UserCheck className="w-5 h-5 text-primary-600" />
                  4. Drepturile Dumneavoastră (GDPR)
                </h2>
                <p className="text-slate-600 leading-relaxed mb-4">
                  Conform GDPR, aveți următoarele drepturi:
                </p>
                <div className="space-y-3">
                  <div className="bg-slate-50 p-4 rounded-lg">
                    <p className="font-medium text-slate-700">Dreptul de acces</p>
                    <p className="text-sm text-slate-600">Puteți solicita o copie a tuturor datelor personale pe care le deținem despre dumneavoastră.</p>
                  </div>
                  <div className="bg-slate-50 p-4 rounded-lg">
                    <p className="font-medium text-slate-700">Dreptul la rectificare</p>
                    <p className="text-sm text-slate-600">Puteți solicita corectarea datelor inexacte sau incomplete.</p>
                  </div>
                  <div className="bg-slate-50 p-4 rounded-lg">
                    <p className="font-medium text-slate-700">Dreptul la ștergere („dreptul de a fi uitat")</p>
                    <p className="text-sm text-slate-600">Puteți solicita ștergerea tuturor datelor dumneavoastră personale.</p>
                  </div>
                  <div className="bg-slate-50 p-4 rounded-lg">
                    <p className="font-medium text-slate-700">Dreptul la portabilitatea datelor</p>
                    <p className="text-sm text-slate-600">Puteți solicita exportul datelor într-un format structurat și utilizabil.</p>
                  </div>
                  <div className="bg-slate-50 p-4 rounded-lg">
                    <p className="font-medium text-slate-700">Dreptul de opoziție</p>
                    <p className="text-sm text-slate-600">Puteți să vă opuneți prelucrării datelor în anumite circumstanțe.</p>
                  </div>
                  <div className="bg-slate-50 p-4 rounded-lg">
                    <p className="font-medium text-slate-700">Dreptul de a depune plângere</p>
                    <p className="text-sm text-slate-600">Puteți depune o plângere la ANSPDCP (Autoritatea Națională de Supraveghere a Prelucrării Datelor cu Caracter Personal).</p>
                  </div>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <Lock className="w-5 h-5 text-primary-600" />
                  5. Securitatea Datelor
                </h2>
                <div className="space-y-4 text-slate-600 leading-relaxed">
                  <p><strong>5.1.</strong> Datele sensibile (credențiale, rezultate medicale) sunt criptate folosind algoritmi puternici de criptare.</p>
                  <p><strong>5.2.</strong> Folosim conexiuni HTTPS pentru toate comunicațiile.</p>
                  <p><strong>5.3.</strong> Accesul la baza de date este restricționat și monitorizat.</p>
                  <p><strong>5.4.</strong> Cu toate acestea, nicio metodă de transmitere prin internet sau stocare electronică nu este 100% sigură. Nu putem garanta securitate absolută.</p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <Trash2 className="w-5 h-5 text-primary-600" />
                  6. Retenția Datelor
                </h2>
                <div className="space-y-4 text-slate-600 leading-relaxed">
                  <p><strong>6.1.</strong> Păstrăm datele dumneavoastră atât timp cât contul este activ.</p>
                  <p><strong>6.2.</strong> La ștergerea contului, toate datele personale vor fi șterse în termen de 30 de zile.</p>
                  <p><strong>6.3.</strong> Anumite date pot fi păstrate mai mult timp dacă există obligații legale de arhivare.</p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <Database className="w-5 h-5 text-primary-600" />
                  7. Cookie-uri
                </h2>
                <div className="space-y-4 text-slate-600 leading-relaxed">
                  <p><strong>7.1.</strong> Folosim cookie-uri esențiale pentru funcționarea serviciului (autentificare, preferințe).</p>
                  <p><strong>7.2.</strong> Nu folosim cookie-uri de tracking sau publicitate.</p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <UserCheck className="w-5 h-5 text-primary-600" />
                  8. Minori
                </h2>
                <p className="text-slate-600 leading-relaxed">
                  Serviciul nu este destinat persoanelor sub 16 ani. Nu colectăm cu bună știință date de la minori. Dacă sunteți părinte și credeți că copilul dumneavoastră ne-a furnizat date personale, contactați-ne pentru ștergere.
                </p>
              </section>

              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <Globe className="w-5 h-5 text-primary-600" />
                  9. Transferuri Internaționale
                </h2>
                <p className="text-slate-600 leading-relaxed">
                  Datele pot fi procesate în afara României (ex: servere cloud, servicii AI). Asigurăm că astfel de transferuri respectă cerințele GDPR și sunt protejate prin clauze contractuale standard sau alte mecanisme legale.
                </p>
              </section>

              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <Mail className="w-5 h-5 text-primary-600" />
                  10. Contact
                </h2>
                <p className="text-slate-600 leading-relaxed mb-4">
                  Pentru exercitarea drepturilor dumneavoastră sau întrebări despre această politică:
                </p>
                <div className="bg-slate-50 p-4 rounded-lg">
                  <p className="text-slate-700">
                    <strong>Email:</strong> <a href="mailto:privacy@analize.online" className="text-primary-600 hover:underline">privacy@analize.online</a>
                  </p>
                  <p className="text-slate-700 mt-2">
                    <strong>Responsabil protecția datelor (DPO):</strong> <a href="mailto:dpo@analize.online" className="text-primary-600 hover:underline">dpo@analize.online</a>
                  </p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4">
                  11. Modificări ale Politicii
                </h2>
                <p className="text-slate-600 leading-relaxed">
                  Ne rezervăm dreptul de a actualiza această politică. Vă vom notifica despre modificări semnificative prin email sau notificare în aplicație. Vă încurajăm să revizuiți periodic această pagină.
                </p>
              </section>
            </>
          ) : (
            <>
              {/* English Version */}
              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <Database className="w-5 h-5 text-primary-600" />
                  1. Data We Collect
                </h2>
                <p className="text-slate-600 leading-relaxed mb-4">
                  We collect the following categories of personal data:
                </p>

                <h3 className="font-semibold text-slate-700 mb-2">1.1. Account Data</h3>
                <ul className="list-disc list-inside text-slate-600 space-y-1 ml-4 mb-4">
                  <li>Email address</li>
                  <li>Password (stored encrypted)</li>
                  <li>Language preferences</li>
                </ul>

                <h3 className="font-semibold text-slate-700 mb-2">1.2. Profile Data (optional)</h3>
                <ul className="list-disc list-inside text-slate-600 space-y-1 ml-4 mb-4">
                  <li>Full name</li>
                  <li>Date of birth</li>
                  <li>Gender</li>
                  <li>Height and weight</li>
                  <li>Blood type</li>
                  <li>Allergies and chronic conditions</li>
                </ul>

                <h3 className="font-semibold text-slate-700 mb-2">1.3. Medical Provider Credentials</h3>
                <ul className="list-disc list-inside text-slate-600 space-y-1 ml-4 mb-4">
                  <li>Usernames and passwords for medical provider accounts</li>
                  <li>This data is encrypted and stored securely</li>
                </ul>

                <h3 className="font-semibold text-slate-700 mb-2">1.4. Medical Data</h3>
                <ul className="list-disc list-inside text-slate-600 space-y-1 ml-4 mb-4">
                  <li>Medical test documents (PDFs)</li>
                  <li>Extracted test results and biomarkers</li>
                  <li>AI-generated health reports</li>
                </ul>

                <h3 className="font-semibold text-slate-700 mb-2">1.5. Technical Data</h3>
                <ul className="list-disc list-inside text-slate-600 space-y-1 ml-4">
                  <li>IP address</li>
                  <li>Browser and device type</li>
                  <li>Access and usage logs</li>
                </ul>
              </section>

              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <Lock className="w-5 h-5 text-primary-600" />
                  2. How We Use Your Data
                </h2>
                <div className="space-y-4 text-slate-600 leading-relaxed">
                  <p><strong>2.1.</strong> Service Provision - to enable access to platform features.</p>
                  <p><strong>2.2.</strong> Medical data synchronization - to automatically download results from connected providers.</p>
                  <p><strong>2.3.</strong> AI report generation - to provide interpretations of test results.</p>
                  <p><strong>2.4.</strong> Communications - to send notifications about new results or health alerts.</p>
                  <p><strong>2.5.</strong> Service improvement - to analyze usage patterns and improve the platform.</p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <Globe className="w-5 h-5 text-primary-600" />
                  3. Third-Party Data Sharing
                </h2>
                <div className="space-y-4 text-slate-600 leading-relaxed">
                  <p><strong>3.1. AI service providers</strong> - We use OpenAI for processing and interpreting medical documents. Data is sent in anonymized or pseudonymized form when possible.</p>
                  <p><strong>3.2. Payment processors</strong> - Netopia processes payments. We do not store credit card data.</p>
                  <p><strong>3.3. Hosting providers</strong> - Data is stored on secure servers.</p>
                  <p><strong>3.4.</strong> We do not sell or share your data with third parties for marketing purposes.</p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <UserCheck className="w-5 h-5 text-primary-600" />
                  4. Your Rights (GDPR)
                </h2>
                <p className="text-slate-600 leading-relaxed mb-4">
                  Under GDPR, you have the following rights:
                </p>
                <div className="space-y-3">
                  <div className="bg-slate-50 p-4 rounded-lg">
                    <p className="font-medium text-slate-700">Right of Access</p>
                    <p className="text-sm text-slate-600">You can request a copy of all personal data we hold about you.</p>
                  </div>
                  <div className="bg-slate-50 p-4 rounded-lg">
                    <p className="font-medium text-slate-700">Right to Rectification</p>
                    <p className="text-sm text-slate-600">You can request correction of inaccurate or incomplete data.</p>
                  </div>
                  <div className="bg-slate-50 p-4 rounded-lg">
                    <p className="font-medium text-slate-700">Right to Erasure ("Right to be Forgotten")</p>
                    <p className="text-sm text-slate-600">You can request deletion of all your personal data.</p>
                  </div>
                  <div className="bg-slate-50 p-4 rounded-lg">
                    <p className="font-medium text-slate-700">Right to Data Portability</p>
                    <p className="text-sm text-slate-600">You can request export of your data in a structured, usable format.</p>
                  </div>
                  <div className="bg-slate-50 p-4 rounded-lg">
                    <p className="font-medium text-slate-700">Right to Object</p>
                    <p className="text-sm text-slate-600">You can object to data processing in certain circumstances.</p>
                  </div>
                  <div className="bg-slate-50 p-4 rounded-lg">
                    <p className="font-medium text-slate-700">Right to Lodge a Complaint</p>
                    <p className="text-sm text-slate-600">You can file a complaint with your national data protection authority.</p>
                  </div>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <Lock className="w-5 h-5 text-primary-600" />
                  5. Data Security
                </h2>
                <div className="space-y-4 text-slate-600 leading-relaxed">
                  <p><strong>5.1.</strong> Sensitive data (credentials, medical results) is encrypted using strong encryption algorithms.</p>
                  <p><strong>5.2.</strong> We use HTTPS connections for all communications.</p>
                  <p><strong>5.3.</strong> Database access is restricted and monitored.</p>
                  <p><strong>5.4.</strong> However, no method of transmission over the internet or electronic storage is 100% secure. We cannot guarantee absolute security.</p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <Trash2 className="w-5 h-5 text-primary-600" />
                  6. Data Retention
                </h2>
                <div className="space-y-4 text-slate-600 leading-relaxed">
                  <p><strong>6.1.</strong> We retain your data as long as your account is active.</p>
                  <p><strong>6.2.</strong> Upon account deletion, all personal data will be deleted within 30 days.</p>
                  <p><strong>6.3.</strong> Some data may be retained longer if there are legal archiving obligations.</p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <Database className="w-5 h-5 text-primary-600" />
                  7. Cookies
                </h2>
                <div className="space-y-4 text-slate-600 leading-relaxed">
                  <p><strong>7.1.</strong> We use essential cookies for service operation (authentication, preferences).</p>
                  <p><strong>7.2.</strong> We do not use tracking or advertising cookies.</p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <UserCheck className="w-5 h-5 text-primary-600" />
                  8. Minors
                </h2>
                <p className="text-slate-600 leading-relaxed">
                  The Service is not intended for persons under 16 years of age. We do not knowingly collect data from minors. If you are a parent and believe your child has provided us with personal data, contact us for deletion.
                </p>
              </section>

              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <Globe className="w-5 h-5 text-primary-600" />
                  9. International Transfers
                </h2>
                <p className="text-slate-600 leading-relaxed">
                  Data may be processed outside Romania (e.g., cloud servers, AI services). We ensure that such transfers comply with GDPR requirements and are protected by standard contractual clauses or other legal mechanisms.
                </p>
              </section>

              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <Mail className="w-5 h-5 text-primary-600" />
                  10. Contact
                </h2>
                <p className="text-slate-600 leading-relaxed mb-4">
                  To exercise your rights or for questions about this policy:
                </p>
                <div className="bg-slate-50 p-4 rounded-lg">
                  <p className="text-slate-700">
                    <strong>Email:</strong> <a href="mailto:privacy@analize.online" className="text-primary-600 hover:underline">privacy@analize.online</a>
                  </p>
                  <p className="text-slate-700 mt-2">
                    <strong>Data Protection Officer (DPO):</strong> <a href="mailto:dpo@analize.online" className="text-primary-600 hover:underline">dpo@analize.online</a>
                  </p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4">
                  11. Policy Changes
                </h2>
                <p className="text-slate-600 leading-relaxed">
                  We reserve the right to update this policy. We will notify you of significant changes via email or in-app notification. We encourage you to periodically review this page.
                </p>
              </section>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-slate-500">
          <p>Healthy.ai - {isRomanian ? 'Toate drepturile rezervate' : 'All rights reserved'} © 2026</p>
          <div className="mt-2 space-x-4">
            <Link to="/terms" className="text-primary-600 hover:underline">
              {isRomanian ? 'Termeni și Condiții' : 'Terms and Conditions'}
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
