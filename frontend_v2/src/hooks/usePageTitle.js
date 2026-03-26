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
const usePageTitle = (titleKey, fallback = '') => {
    const { t, i18n } = useTranslation();
    const location = useLocation();

    useEffect(() => {
        const lang = i18n.language?.startsWith('ro') ? 'ro' : 'en';
        const path = location.pathname;
        const canonicalUrl = `${SITE_ORIGIN}${path === '/' ? '' : path}`;

        // Use page-specific meta if available
        const pageMeta = PAGE_META[path]?.[lang];
        const defaults = DEFAULT_META[lang];

        let title, description;
        if (pageMeta) {
            title = pageMeta.title;
            description = pageMeta.description;
        } else {
            // Fallback to translation key
            const translated = titleKey ? t(titleKey) || fallback : fallback;
            title = translated ? `${translated} — ${SITE_NAME}` : defaults.title;
            description = defaults.description;
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

        // Cleanup
        return () => {
            const d = DEFAULT_META.ro;
            document.title = d.title;
            setMetaTag('og:title', d.title);
            setMetaTag('og:description', d.description);
            setMetaTag('og:url', SITE_ORIGIN);
            setNameMetaTag('description', d.description);
        };
    }, [titleKey, fallback, i18n.language, location.pathname]);
};

export default usePageTitle;
