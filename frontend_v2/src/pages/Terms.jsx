import React from 'react';
import { useTranslation } from 'react-i18next';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, FileText, AlertTriangle, Shield, Scale } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Terms() {
  const { t, i18n } = useTranslation();
  const { user } = useAuth();
  const navigate = useNavigate();
  const isRomanian = i18n.language === 'ro';

  // Last updated date
  const lastUpdated = '2 Februarie 2026';
  const version = '1.0';

  const handleBack = () => {
    if (user) {
      navigate('/');
    } else {
      navigate(-1);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      <div className="max-w-4xl mx-auto px-4 py-12">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={handleBack}
            className="inline-flex items-center gap-2 text-slate-600 hover:text-primary-600 mb-4"
          >
            <ArrowLeft size={18} />
            {isRomanian ? 'Înapoi' : 'Back'}
          </button>
          <div className="flex items-center gap-3 mb-4">
            <div className="p-3 bg-primary-100 rounded-xl">
              <FileText className="w-8 h-8 text-primary-600" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-slate-800">
                {isRomanian ? 'Termeni și Condiții' : 'Terms and Conditions'}
              </h1>
              <p className="text-slate-500">
                {isRomanian ? `Versiunea ${version} • Ultima actualizare: ${lastUpdated}` : `Version ${version} • Last updated: February 2, 2026`}
              </p>
            </div>
          </div>
        </div>

        {/* Important Notice */}
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-6 mb-8">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-6 h-6 text-amber-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-amber-800 mb-2">
                {isRomanian ? 'Notificare Importantă' : 'Important Notice'}
              </h3>
              <p className="text-amber-700 text-sm">
                {isRomanian
                  ? 'Healthy.ai NU oferă sfaturi medicale. Serviciul nostru este exclusiv informativ și nu înlocuiește consultul medical profesionist. Întotdeauna consultați un medic pentru decizii privind sănătatea dumneavoastră.'
                  : 'Healthy.ai does NOT provide medical advice. Our service is for informational purposes only and does not replace professional medical consultation. Always consult a doctor for decisions about your health.'}
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
                  <span className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center text-primary-600 text-sm font-bold">1</span>
                  Acceptarea Termenilor
                </h2>
                <p className="text-slate-600 leading-relaxed">
                  Prin accesarea sau utilizarea serviciului Healthy.ai („Serviciul"), sunteți de acord să fiți obligat de acești Termeni și Condiții („Termenii"). Dacă nu sunteți de acord cu oricare parte a acestor Termeni, nu aveți dreptul să accesați Serviciul.
                </p>
              </section>

              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <span className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center text-primary-600 text-sm font-bold">2</span>
                  Descrierea Serviciului
                </h2>
                <p className="text-slate-600 leading-relaxed mb-4">
                  Healthy.ai este o platformă de agregare a datelor medicale care permite utilizatorilor să:
                </p>
                <ul className="list-disc list-inside text-slate-600 space-y-2 ml-4">
                  <li>Conecteze conturi de la furnizori de servicii medicale (laboratoare, clinici)</li>
                  <li>Stocheze și organizeze rezultatele analizelor medicale</li>
                  <li>Vizualizeze evoluția biomarkerilor în timp</li>
                  <li>Primească interpretări generate de inteligență artificială</li>
                </ul>
              </section>

              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <span className="w-8 h-8 bg-rose-100 rounded-lg flex items-center justify-center text-rose-600 text-sm font-bold">3</span>
                  Exonerare de Răspundere Medicală
                </h2>
                <div className="bg-rose-50 border border-rose-200 rounded-xl p-4 mb-4">
                  <p className="text-rose-800 font-medium">
                    IMPORTANT: CITIȚI CU ATENȚIE ACEASTĂ SECȚIUNE
                  </p>
                </div>
                <div className="space-y-4 text-slate-600 leading-relaxed">
                  <p>
                    <strong>3.1.</strong> Serviciul Healthy.ai NU oferă sfaturi medicale, diagnostic sau recomandări de tratament. Toate interpretările și analizele generate de inteligența artificială sunt exclusiv în scop informativ.
                  </p>
                  <p>
                    <strong>3.2.</strong> Interpretările AI pot conține erori, inexactități sau informații incomplete. Nu ne asumăm nicio responsabilitate pentru acuratețea, completitudinea sau utilitatea interpretărilor generate.
                  </p>
                  <p>
                    <strong>3.3.</strong> NU luați decizii medicale bazate exclusiv pe informațiile furnizate de acest Serviciu. Consultați întotdeauna un medic calificat pentru orice problemă de sănătate.
                  </p>
                  <p>
                    <strong>3.4.</strong> Serviciul nu înlocuiește relația pacient-medic. Rezultatele analizelor trebuie întotdeauna interpretate de un profesionist medical calificat în contextul istoricului dumneavoastră medical complet.
                  </p>
                  <p>
                    <strong>3.5.</strong> În caz de urgență medicală, sunați imediat la 112 sau prezentați-vă la cea mai apropiată unitate de urgențe.
                  </p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <span className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center text-primary-600 text-sm font-bold">4</span>
                  Responsabilitatea Utilizatorului pentru Date
                </h2>
                <div className="space-y-4 text-slate-600 leading-relaxed">
                  <p>
                    <strong>4.1.</strong> Sunteți singurul responsabil pentru securitatea și confidențialitatea datelor de autentificare (credențialele) pe care le furnizați pentru conectarea la furnizorii de servicii medicale.
                  </p>
                  <p>
                    <strong>4.2.</strong> Înțelegeți și acceptați că furnizați credențialele la furnizorii medicali pe propria răspundere. Serviciul stochează aceste credențiale în formă criptată, dar nu garantăm securitate absolută.
                  </p>
                  <p>
                    <strong>4.3.</strong> Sunteți responsabil pentru acuratețea și actualitatea informațiilor pe care le furnizați prin Serviciu.
                  </p>
                  <p>
                    <strong>4.4.</strong> Recomandăm utilizarea unor parole unice și puternice pentru fiecare cont conectat.
                  </p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <span className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center text-primary-600 text-sm font-bold">5</span>
                  Limitarea Răspunderii
                </h2>
                <div className="space-y-4 text-slate-600 leading-relaxed">
                  <p>
                    <strong>5.1.</strong> Serviciul este furnizat „CA ATARE" și „DUPĂ DISPONIBILITATE", fără garanții de niciun fel, explicite sau implicite.
                  </p>
                  <p>
                    <strong>5.2.</strong> Nu garantăm că Serviciul va fi neîntrerupt, sigur sau fără erori, sau că rezultatele obținute vor fi exacte sau de încredere.
                  </p>
                  <p>
                    <strong>5.3.</strong> În niciun caz nu vom fi răspunzători pentru daune directe, indirecte, incidentale, speciale, consecvente sau exemplare, inclusiv, dar fără a se limita la, daune pentru pierderea de profituri, bunăvoință, utilizare, date sau alte pierderi intangibile.
                  </p>
                  <p>
                    <strong>5.4.</strong> Răspunderea noastră totală față de dumneavoastră pentru toate revendicările legate de Serviciu nu va depăși suma pe care ați plătit-o pentru Serviciu în ultimele 12 luni.
                  </p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <span className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center text-primary-600 text-sm font-bold">6</span>
                  Abonamente și Plăți
                </h2>
                <div className="space-y-4 text-slate-600 leading-relaxed">
                  <p>
                    <strong>6.1.</strong> Serviciul oferă atât funcționalități gratuite cât și abonamente plătite (Premium și Family).
                  </p>
                  <p>
                    <strong>6.2.</strong> Plățile sunt procesate prin Netopia și sunt supuse termenilor și condițiilor acestora.
                  </p>
                  <p>
                    <strong>6.3.</strong> Abonamentele se reînnoiesc automat la sfârșitul perioadei de facturare, cu excepția cazului în care anulați înainte de data de reînnoire.
                  </p>
                  <p>
                    <strong>6.4.</strong> Puteți anula abonamentul în orice moment. Anularea va intra în vigoare la sfârșitul perioadei de facturare curente.
                  </p>
                  <p>
                    <strong>6.5.</strong> Nu oferim rambursări pentru perioade parțiale de utilizare sau pentru funcționalități neutilizate.
                  </p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <span className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center text-primary-600 text-sm font-bold">7</span>
                  Proprietate Intelectuală
                </h2>
                <p className="text-slate-600 leading-relaxed">
                  Serviciul și conținutul său original, caracteristicile și funcționalitățile sunt și vor rămâne proprietatea exclusivă a Healthy.ai. Serviciul este protejat de legile privind drepturile de autor, mărcile comerciale și alte legi.
                </p>
              </section>

              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <span className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center text-primary-600 text-sm font-bold">8</span>
                  Încetarea
                </h2>
                <div className="space-y-4 text-slate-600 leading-relaxed">
                  <p>
                    <strong>8.1.</strong> Puteți înceta utilizarea Serviciului în orice moment prin ștergerea contului dumneavoastră.
                  </p>
                  <p>
                    <strong>8.2.</strong> Ne rezervăm dreptul de a suspenda sau închide contul dumneavoastră imediat, fără notificare prealabilă, pentru orice motiv, inclusiv, dar fără a se limita la, încălcarea acestor Termeni.
                  </p>
                  <p>
                    <strong>8.3.</strong> La încetare, dreptul dumneavoastră de a utiliza Serviciul va înceta imediat.
                  </p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <span className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center text-primary-600 text-sm font-bold">9</span>
                  Modificări ale Termenilor
                </h2>
                <p className="text-slate-600 leading-relaxed">
                  Ne rezervăm dreptul de a modifica sau înlocui acești Termeni în orice moment. Vă vom notifica despre orice modificări prin postarea noilor Termeni pe această pagină și actualizarea datei „Ultima actualizare". Utilizarea continuă a Serviciului după astfel de modificări constituie acceptarea noilor Termeni.
                </p>
              </section>

              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <span className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center text-primary-600 text-sm font-bold">10</span>
                  Legea Aplicabilă
                </h2>
                <p className="text-slate-600 leading-relaxed">
                  Acești Termeni vor fi guvernați și interpretați în conformitate cu legile din România, fără a ține cont de conflictele de prevederi legale. Orice litigiu va fi soluționat de instanțele competente din București, România.
                </p>
              </section>

              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <span className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center text-primary-600 text-sm font-bold">11</span>
                  Contact
                </h2>
                <p className="text-slate-600 leading-relaxed">
                  Pentru întrebări despre acești Termeni, ne puteți contacta la: <a href="mailto:contact@analize.online" className="text-primary-600 hover:underline">contact@analize.online</a>
                </p>
              </section>
            </>
          ) : (
            <>
              {/* English Version */}
              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <span className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center text-primary-600 text-sm font-bold">1</span>
                  Acceptance of Terms
                </h2>
                <p className="text-slate-600 leading-relaxed">
                  By accessing or using the Healthy.ai service ("Service"), you agree to be bound by these Terms and Conditions ("Terms"). If you do not agree with any part of these Terms, you may not access the Service.
                </p>
              </section>

              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <span className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center text-primary-600 text-sm font-bold">2</span>
                  Description of Service
                </h2>
                <p className="text-slate-600 leading-relaxed mb-4">
                  Healthy.ai is a medical data aggregation platform that allows users to:
                </p>
                <ul className="list-disc list-inside text-slate-600 space-y-2 ml-4">
                  <li>Connect accounts from medical service providers (laboratories, clinics)</li>
                  <li>Store and organize medical test results</li>
                  <li>View biomarker evolution over time</li>
                  <li>Receive AI-generated interpretations</li>
                </ul>
              </section>

              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <span className="w-8 h-8 bg-rose-100 rounded-lg flex items-center justify-center text-rose-600 text-sm font-bold">3</span>
                  Medical Disclaimer
                </h2>
                <div className="bg-rose-50 border border-rose-200 rounded-xl p-4 mb-4">
                  <p className="text-rose-800 font-medium">
                    IMPORTANT: PLEASE READ THIS SECTION CAREFULLY
                  </p>
                </div>
                <div className="space-y-4 text-slate-600 leading-relaxed">
                  <p>
                    <strong>3.1.</strong> The Healthy.ai Service does NOT provide medical advice, diagnosis, or treatment recommendations. All AI-generated interpretations and analyses are for informational purposes only.
                  </p>
                  <p>
                    <strong>3.2.</strong> AI interpretations may contain errors, inaccuracies, or incomplete information. We assume no responsibility for the accuracy, completeness, or usefulness of generated interpretations.
                  </p>
                  <p>
                    <strong>3.3.</strong> DO NOT make medical decisions based solely on information provided by this Service. Always consult a qualified physician for any health concerns.
                  </p>
                  <p>
                    <strong>3.4.</strong> The Service does not replace the patient-doctor relationship. Test results should always be interpreted by a qualified medical professional in the context of your complete medical history.
                  </p>
                  <p>
                    <strong>3.5.</strong> In case of medical emergency, call emergency services immediately or go to the nearest emergency room.
                  </p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <span className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center text-primary-600 text-sm font-bold">4</span>
                  User Responsibility for Data
                </h2>
                <div className="space-y-4 text-slate-600 leading-relaxed">
                  <p>
                    <strong>4.1.</strong> You are solely responsible for the security and confidentiality of the authentication data (credentials) you provide for connecting to medical service providers.
                  </p>
                  <p>
                    <strong>4.2.</strong> You understand and accept that you provide credentials to medical providers at your own risk. The Service stores these credentials in encrypted form, but we do not guarantee absolute security.
                  </p>
                  <p>
                    <strong>4.3.</strong> You are responsible for the accuracy and timeliness of the information you provide through the Service.
                  </p>
                  <p>
                    <strong>4.4.</strong> We recommend using unique and strong passwords for each connected account.
                  </p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <span className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center text-primary-600 text-sm font-bold">5</span>
                  Limitation of Liability
                </h2>
                <div className="space-y-4 text-slate-600 leading-relaxed">
                  <p>
                    <strong>5.1.</strong> The Service is provided "AS IS" and "AS AVAILABLE" without warranties of any kind, express or implied.
                  </p>
                  <p>
                    <strong>5.2.</strong> We do not guarantee that the Service will be uninterrupted, secure, or error-free, or that the results obtained will be accurate or reliable.
                  </p>
                  <p>
                    <strong>5.3.</strong> In no event shall we be liable for any direct, indirect, incidental, special, consequential, or exemplary damages, including but not limited to damages for loss of profits, goodwill, use, data, or other intangible losses.
                  </p>
                  <p>
                    <strong>5.4.</strong> Our total liability to you for all claims relating to the Service shall not exceed the amount you have paid for the Service in the past 12 months.
                  </p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <span className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center text-primary-600 text-sm font-bold">6</span>
                  Subscriptions and Payments
                </h2>
                <div className="space-y-4 text-slate-600 leading-relaxed">
                  <p>
                    <strong>6.1.</strong> The Service offers both free features and paid subscriptions (Premium and Family).
                  </p>
                  <p>
                    <strong>6.2.</strong> Payments are processed through Netopia and are subject to their terms and conditions.
                  </p>
                  <p>
                    <strong>6.3.</strong> Subscriptions automatically renew at the end of the billing period unless you cancel before the renewal date.
                  </p>
                  <p>
                    <strong>6.4.</strong> You may cancel your subscription at any time. Cancellation will take effect at the end of the current billing period.
                  </p>
                  <p>
                    <strong>6.5.</strong> We do not offer refunds for partial usage periods or unused features.
                  </p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <span className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center text-primary-600 text-sm font-bold">7</span>
                  Intellectual Property
                </h2>
                <p className="text-slate-600 leading-relaxed">
                  The Service and its original content, features, and functionality are and will remain the exclusive property of Healthy.ai. The Service is protected by copyright, trademark, and other laws.
                </p>
              </section>

              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <span className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center text-primary-600 text-sm font-bold">8</span>
                  Termination
                </h2>
                <div className="space-y-4 text-slate-600 leading-relaxed">
                  <p>
                    <strong>8.1.</strong> You may terminate your use of the Service at any time by deleting your account.
                  </p>
                  <p>
                    <strong>8.2.</strong> We reserve the right to suspend or terminate your account immediately, without prior notice, for any reason, including but not limited to breach of these Terms.
                  </p>
                  <p>
                    <strong>8.3.</strong> Upon termination, your right to use the Service will cease immediately.
                  </p>
                </div>
              </section>

              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <span className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center text-primary-600 text-sm font-bold">9</span>
                  Changes to Terms
                </h2>
                <p className="text-slate-600 leading-relaxed">
                  We reserve the right to modify or replace these Terms at any time. We will notify you of any changes by posting the new Terms on this page and updating the "Last updated" date. Continued use of the Service after such modifications constitutes acceptance of the new Terms.
                </p>
              </section>

              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <span className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center text-primary-600 text-sm font-bold">10</span>
                  Governing Law
                </h2>
                <p className="text-slate-600 leading-relaxed">
                  These Terms shall be governed and construed in accordance with the laws of Romania, without regard to conflict of law provisions. Any disputes will be resolved by the competent courts in Bucharest, Romania.
                </p>
              </section>

              <section>
                <h2 className="text-xl font-bold text-slate-800 mb-4 flex items-center gap-2">
                  <span className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center text-primary-600 text-sm font-bold">11</span>
                  Contact
                </h2>
                <p className="text-slate-600 leading-relaxed">
                  For questions about these Terms, you can contact us at: <a href="mailto:contact@analize.online" className="text-primary-600 hover:underline">contact@analize.online</a>
                </p>
              </section>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-slate-500">
          <p>Healthy.ai - {isRomanian ? 'Toate drepturile rezervate' : 'All rights reserved'} © 2026</p>
          <div className="mt-2 space-x-4">
            <Link to="/privacy" className="text-primary-600 hover:underline">
              {isRomanian ? 'Politica de Confidențialitate' : 'Privacy Policy'}
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
