import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useLocation } from 'react-router-dom';

const SITE_ORIGIN = 'https://analize.online';
const DEFAULT_DESCRIPTION = 'Analize.Online - Toate analizele tale medicale, într-un singur loc';
const OG_IMAGE = 'https://analize.online/healthy.svg';

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

const usePageTitle = (titleKey, fallback = '') => {
    const { t, i18n } = useTranslation();
    const location = useLocation();

    useEffect(() => {
        const title = titleKey ? t(titleKey) || fallback : fallback;
        const suffix = 'Analize.Online';
        const fullTitle = title ? `${title} - ${suffix}` : suffix;
        const description = title ? `${title} - ${suffix}` : DEFAULT_DESCRIPTION;
        document.title = fullTitle;

        // Build canonical URL from current path
        const canonicalUrl = `${SITE_ORIGIN}${location.pathname}`;

        // Update <link rel="canonical">
        let canonical = document.querySelector('link[rel="canonical"]');
        if (!canonical) {
            canonical = document.createElement('link');
            canonical.setAttribute('rel', 'canonical');
            document.head.appendChild(canonical);
        }
        canonical.setAttribute('href', canonicalUrl);

        // Update OG meta tags
        setMetaTag('og:url', canonicalUrl);
        setMetaTag('og:title', fullTitle);
        setMetaTag('og:description', description);
        setMetaTag('og:image', OG_IMAGE);
        setMetaTag('og:type', 'website');

        // Update standard and Twitter meta tags
        setNameMetaTag('description', description);
        setNameMetaTag('twitter:card', 'summary');

        // Cleanup: restore defaults on unmount
        return () => {
            document.title = suffix;
            setMetaTag('og:title', suffix);
            setMetaTag('og:description', DEFAULT_DESCRIPTION);
            setMetaTag('og:image', OG_IMAGE);
            setMetaTag('og:type', 'website');
            setMetaTag('og:url', SITE_ORIGIN);
            setNameMetaTag('description', DEFAULT_DESCRIPTION);
            setNameMetaTag('twitter:card', 'summary');
        };
    }, [titleKey, fallback, i18n.language, location.pathname]);
};

export default usePageTitle;
