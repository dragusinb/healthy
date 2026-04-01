import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useLocation } from 'react-router-dom';

const SITE_ORIGIN = 'https://analize.online';
const SITE_NAME = 'Analize.Online';
const OG_IMAGE = 'https://analize.online/og-image.png';

const DEFAULT_META = {
    ro: {
        title: 'Analize.Online — Toate analizele tale medicale într-un singur loc',
        description: 'Prima platformă din România care agregă analizele medicale de la Regina Maria, Synevo, MedLife și Sanador. Interpretare AI cu 6 specialiști virtuali. Criptare AES-256 per utilizator.',
    },
    en: {
        title: 'Analize.Online — All your medical tests in one place',
        description: 'Romania\'s first platform that aggregates lab results from Regina Maria, Synevo, MedLife and Sanador. AI analysis with 6 virtual specialists. Per-user AES-256 encryption.',
    },
};

// Page-specific SEO metadata
const PAGE_META = {
    '/': {
        ro: {
            title: 'Analize.Online — Toate analizele tale medicale într-un singur loc',
            description: 'Prima platformă din România care agregă analizele de la Regina Maria, Synevo, MedLife și Sanador. Analiza AI cu 6 specialiști virtuali. Criptare per utilizator. Gratis.',
        },
        en: {
            title: 'Analize.Online — All your medical tests in one place',
            description: 'Romania\'s first platform aggregating lab results from Regina Maria, Synevo, MedLife and Sanador. AI analysis with 6 virtual specialists. Per-user encryption. Free.',
        },
    },
    '/pricing': {
        ro: {
            title: 'Prețuri — Analize.Online | De la 0 RON/lună',
            description: 'Planuri de abonament Analize.Online: Gratuit (1 furnizor, 2 analize AI/lună), Premium (29 RON/lună, furnizori nelimitați, 30 analize AI), Familie (49 RON/lună, până la 5 membri).',
        },
        en: {
            title: 'Pricing — Analize.Online | From 0 RON/month',
            description: 'Analize.Online plans: Free (1 provider, 2 AI analyses/month), Premium (29 RON/month, unlimited providers, 30 AI analyses), Family (49 RON/month, up to 5 members).',
        },
    },
    '/login': {
        ro: {
            title: 'Autentificare — Analize.Online',
            description: 'Conectează-te la contul tău Analize.Online pentru a vedea analizele medicale, biomarkerii și rapoartele AI de sănătate.',
        },
        en: {
            title: 'Login — Analize.Online',
            description: 'Sign in to your Analize.Online account to view lab results, biomarkers and AI health reports.',
        },
    },
    '/register': {
        ro: {
            title: 'Creează cont gratuit — Analize.Online',
            description: 'Înregistrează-te gratuit pe Analize.Online. Conectează-ți conturile de la Regina Maria, Synevo, MedLife sau Sanador și primește analize AI gratuite.',
        },
        en: {
            title: 'Create free account — Analize.Online',
            description: 'Sign up free on Analize.Online. Connect your Regina Maria, Synevo, MedLife or Sanador accounts and get free AI health analyses.',
        },
    },
    '/terms': {
        ro: { title: 'Termeni și condiții — Analize.Online', description: 'Termeni și condiții de utilizare a platformei Analize.Online.' },
        en: { title: 'Terms of Service — Analize.Online', description: 'Terms and conditions for using the Analize.Online platform.' },
    },
    '/privacy': {
        ro: { title: 'Politica de confidențialitate — Analize.Online', description: 'Politica de confidențialitate și protecția datelor personale pe Analize.Online. Conform GDPR.' },
        en: { title: 'Privacy Policy — Analize.Online', description: 'Privacy policy and personal data protection on Analize.Online. GDPR compliant.' },
    },
    '/despre-noi': {
        ro: { title: 'Despre noi — Echipa Analize.Online', description: 'Misiunea Analize.Online: digitalizarea sănătății în România. Agregare analize medicale, interpretare AI, criptare per utilizator.' },
        en: { title: 'About Us — Analize.Online Team', description: 'Analize.Online mission: digitalizing healthcare in Romania. Medical test aggregation, AI interpretation, per-user encryption.' },
    },
    '/contact': {
        ro: { title: 'Contact — Analize.Online', description: 'Contactează echipa Analize.Online pentru întrebări, sugestii sau parteneriate. Email: contact@analize.online.' },
        en: { title: 'Contact — Analize.Online', description: 'Contact the Analize.Online team for questions, suggestions or partnerships. Email: contact@analize.online.' },
    },
    '/disclaimer-medical': {
        ro: { title: 'Disclaimer Medical — Analize.Online', description: 'Analize.Online oferă informații orientative bazate pe AI, nu diagnostic medical. Consultă întotdeauna un medic specialist.' },
        en: { title: 'Medical Disclaimer — Analize.Online', description: 'Analize.Online provides AI-based informational guidance, not medical diagnosis. Always consult a medical specialist.' },
    },
    '/analyzer': {
        ro: { title: 'Analizator Gratuit Analize Medicale | Analize.Online', description: 'Încarcă rezultatele analizelor tale medicale (text sau PDF) și primești interpretare AI gratuită. Fără cont necesar. Identifică valorile anormale instant.' },
        en: { title: 'Free Lab Results Analyzer | Analize.Online', description: 'Upload your lab results (text or PDF) and get free AI interpretation. No account needed. Identify abnormal values instantly.' },
    },
    '/demo': {
        ro: { title: 'Demo — Analize.Online | Vezi cum funcționează', description: 'Demo interactiv Analize.Online: dashboard cu date exemplu, biomarkeri extrasi, grafice evoluție, alerte. Vezi platforma în acțiune.' },
        en: { title: 'Demo — Analize.Online | See how it works', description: 'Interactive Analize.Online demo: dashboard with sample data, extracted biomarkers, evolution charts, alerts. See the platform in action.' },
    },
};

const setMetaTag = (property, content) => {
    let el = document.querySelector(`meta[property="${property}"]`);
    if (!el) {
        el = document.createElement('meta');
        el.setAttribute('property', property);
        document.head.appendChild(el);
    }
    el.setAttribute('content', content);
};

const setNameMetaTag = (name, content) => {
    let el = document.querySelector(`meta[name="${name}"]`);
    if (!el) {
        el = document.createElement('meta');
        el.setAttribute('name', name);
        document.head.appendChild(el);
    }
    el.setAttribute('content', content);
};

/**
 * SEO-optimized page title and meta tags hook.
 * Uses page-specific metadata when available, falls back to translation keys.
 */
/**
 * SEO-optimized page title and meta tags hook.
 * @param {string|null} titleKey - i18n key for page title
 * @param {string} fallback - Fallback title string
 * @param {object} override - Optional {title, description} to use directly (for dynamic pages like blog/biomarker)
 */
const usePageTitle = (titleKey, fallback = '', override = null) => {
    const { t, i18n } = useTranslation();
    const location = useLocation();

    useEffect(() => {
        const lang = i18n.language?.startsWith('ro') ? 'ro' : 'en';
        const path = location.pathname;
        const canonicalUrl = `${SITE_ORIGIN}${path === '/' ? '' : path}`;

        const defaults = DEFAULT_META[lang];
        let title, description;

        if (override?.title) {
            // Dynamic override (blog articles, biomarker pages)
            title = override.title;
            description = override.description || defaults.description;
        } else {
            // Use page-specific meta if available
            const pageMeta = PAGE_META[path]?.[lang];
            if (pageMeta) {
                title = pageMeta.title;
                description = pageMeta.description;
            } else {
                // Fallback to translation key
                const translated = titleKey ? t(titleKey) || fallback : fallback;
                title = translated ? `${translated} — ${SITE_NAME}` : defaults.title;
                description = defaults.description;
            }
        }

        // Set document title
        document.title = title;

        // Canonical URL
        let canonical = document.querySelector('link[rel="canonical"]');
        if (!canonical) {
            canonical = document.createElement('link');
            canonical.setAttribute('rel', 'canonical');
            document.head.appendChild(canonical);
        }
        canonical.setAttribute('href', canonicalUrl);

        // Open Graph
        setMetaTag('og:url', canonicalUrl);
        setMetaTag('og:title', title);
        setMetaTag('og:description', description);
        setMetaTag('og:image', OG_IMAGE);
        setMetaTag('og:type', 'website');
        setMetaTag('og:site_name', SITE_NAME);
        setMetaTag('og:locale', lang === 'ro' ? 'ro_RO' : 'en_US');

        // Standard meta
        setNameMetaTag('description', description);

        // Twitter
        setNameMetaTag('twitter:card', 'summary_large_image');
        setNameMetaTag('twitter:title', title);
        setNameMetaTag('twitter:description', description);
        setNameMetaTag('twitter:image', OG_IMAGE);

        // Dynamic hreflang — update per page so crawlers see correct URLs
        document.querySelectorAll('link[hreflang]').forEach(el => {
            el.setAttribute('href', canonicalUrl);
        });

        // Cleanup
        return () => {
            const d = DEFAULT_META.ro;
            document.title = d.title;
            setMetaTag('og:title', d.title);
            setMetaTag('og:description', d.description);
            setMetaTag('og:url', SITE_ORIGIN);
            setNameMetaTag('description', d.description);
        };
    }, [titleKey, fallback, i18n.language, location.pathname, override?.title, override?.description]);
};

export default usePageTitle;
