import { useEffect } from 'react';

/**
 * Injects a JSON-LD script tag into <head> and removes it on unmount.
 * @param {object|null} schema - The JSON-LD schema object, or null to skip.
 * @param {string} id - Unique ID for the script tag (to avoid duplicates).
 */
const useJsonLd = (schema, id = 'page-jsonld') => {
    useEffect(() => {
        if (!schema) return;

        // Remove existing tag with same ID
        const existing = document.getElementById(id);
        if (existing) existing.remove();

        const script = document.createElement('script');
        script.id = id;
        script.type = 'application/ld+json';
        script.textContent = JSON.stringify(schema);
        document.head.appendChild(script);

        return () => {
            const el = document.getElementById(id);
            if (el) el.remove();
        };
    }, [schema, id]);
};

export default useJsonLd;
