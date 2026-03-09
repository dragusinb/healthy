import { useEffect } from 'react';
import { useTranslation } from 'react-i18next';

const usePageTitle = (titleKey, fallback = '') => {
    const { t, i18n } = useTranslation();

    useEffect(() => {
        const title = titleKey ? t(titleKey) || fallback : fallback;
        const suffix = 'Analize.Online';
        document.title = title ? `${title} - ${suffix}` : suffix;
    }, [titleKey, fallback, i18n.language]);
};

export default usePageTitle;
