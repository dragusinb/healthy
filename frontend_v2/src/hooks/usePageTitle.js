import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useLocation } from 'react-router-dom';

const SITE_ORIGIN = 'https://analize.online';

const setMetaTag = (property, content) => {
    let el = document.querySelector(`meta[property="${property}"]`);
    if (!el) {
        el = document.createElement('meta');
        el.setAttribute('property', property);
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
    }, [titleKey, fallback, i18n.language, location.pathname]);
};

export default usePageTitle;
