import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowRight, Calendar, Tag, Loader2 } from 'lucide-react';
import usePageTitle from '../hooks/usePageTitle';
import useJsonLd from '../hooks/useJsonLd';
import api from '../api/client';

export default function BlogList() {
  const { i18n } = useTranslation();
  const isRo = i18n.language === 'ro';
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [selectedTag, setSelectedTag] = useState(null);
  const [tags, setTags] = useState([]);

  usePageTitle(null, null, {
    title: isRo
      ? 'Blog Sănătate — Sfaturi, rețete și ghiduri medicale | Analize.Online'
      : 'Health Blog — Tips, recipes and medical guides | Analize.Online',
    description: isRo
      ? 'Articole despre sănătate, nutriție cu rețete românești, interpretare analize de sânge, fitness bazat pe profilul medical. Blog Analize.Online.'
      : 'Articles about health, nutrition with Romanian recipes, blood test interpretation, fitness based on medical profile. Analize.Online blog.',
  });

  useJsonLd({
    '@context': 'https://schema.org',
    '@type': 'Blog',
    name: isRo ? 'Blog Analize.Online' : 'Analize.Online Blog',
    description: isRo
      ? 'Articole despre sănătate, nutriție și interpretare analize medicale'
      : 'Articles about health, nutrition and medical test interpretation',
    url: 'https://analize.online/blog',
    publisher: { '@type': 'Organization', name: 'Analize.Online', url: 'https://analize.online' },
  });

  useEffect(() => {
    fetchArticles();
    fetchTags();
  }, [page, selectedTag]);

  const fetchArticles = async () => {
    setLoading(true);
    try {
      const params = { page, limit: 12 };
      if (selectedTag) params.tag = selectedTag;
      const res = await api.get('/blog/articles', { params });
      if (page === 1) {
        setArticles(res.data.articles || []);
      } else {
        setArticles(prev => [...prev, ...(res.data.articles || [])]);
      }
      setHasMore(res.data.has_more || false);
    } catch (e) {
      console.error('Failed to fetch blog articles', e);
    } finally {
      setLoading(false);
    }
  };

  const fetchTags = async () => {
    try {
      const res = await api.get('/blog/tags');
      setTags(res.data.tags || []);
    } catch (e) { /* ignore */ }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    return d.toLocaleDateString(isRo ? 'ro-RO' : 'en-US', {
      year: 'numeric', month: 'long', day: 'numeric',
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      {/* Hero */}
      <section className="bg-gradient-to-br from-emerald-600 to-teal-700 text-white py-16 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-3xl md:text-5xl font-bold mb-4">
            {isRo ? 'Blog Sănătate' : 'Health Blog'}
          </h1>
          <p className="text-lg text-emerald-100 max-w-2xl mx-auto">
            {isRo
              ? 'Sfaturi de nutriție cu rețete românești, interpretare analize de sânge, fitness bazat pe profilul tău medical și multe altele.'
              : 'Nutrition tips with Romanian recipes, blood test interpretation, fitness based on your medical profile and more.'}
          </p>
        </div>
      </section>

      <div className="max-w-6xl mx-auto px-6 py-12">
        {/* Tags filter */}
        {tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-8">
            <button
              onClick={() => { setSelectedTag(null); setPage(1); }}
              className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
                !selectedTag ? 'bg-teal-600 text-white' : 'bg-white border border-slate-200 text-slate-600 hover:border-teal-300'
              }`}
            >
              {isRo ? 'Toate' : 'All'}
            </button>
            {tags.map(t => (
              <button
                key={t.tag}
                onClick={() => { setSelectedTag(t.tag); setPage(1); }}
                className={`px-4 py-1.5 rounded-full text-sm font-medium transition-colors ${
                  selectedTag === t.tag ? 'bg-teal-600 text-white' : 'bg-white border border-slate-200 text-slate-600 hover:border-teal-300'
                }`}
              >
                {t.tag} ({t.count})
              </button>
            ))}
          </div>
        )}

        {/* Articles grid */}
        {loading && articles.length === 0 ? (
          <div className="flex justify-center py-20">
            <Loader2 className="animate-spin text-teal-500" size={32} />
          </div>
        ) : articles.length === 0 ? (
          <div className="text-center py-20 text-slate-500">
            <p className="text-lg">{isRo ? 'Niciun articol încă.' : 'No articles yet.'}</p>
            <p className="mt-2">{isRo ? 'Revino în curând!' : 'Check back soon!'}</p>
          </div>
        ) : (
          <>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {articles.map(a => (
                <Link
                  key={a.slug}
                  to={`/blog/${a.slug}`}
                  className="bg-white rounded-2xl border border-slate-200 overflow-hidden hover:shadow-lg hover:border-teal-200 transition-all group"
                >
                  <div className="p-6">
                    <div className="flex items-center gap-2 text-xs text-slate-400 mb-3">
                      <Calendar size={12} />
                      {formatDate(a.published_at)}
                    </div>
                    <h2 className="text-lg font-bold text-slate-800 group-hover:text-teal-700 transition-colors mb-2 line-clamp-2">
                      {isRo ? a.title : (a.title_en || a.title)}
                    </h2>
                    <p className="text-sm text-slate-500 line-clamp-3 mb-4">
                      {isRo ? a.excerpt : (a.excerpt_en || a.excerpt)}
                    </p>
                    {a.tags && (
                      <div className="flex flex-wrap gap-1">
                        {a.tags.split(',').slice(0, 3).map(tag => (
                          <span key={tag} className="text-xs bg-slate-100 text-slate-500 px-2 py-0.5 rounded">
                            {tag.trim()}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </Link>
              ))}
            </div>

            {hasMore && (
              <div className="text-center mt-8">
                <button
                  onClick={() => setPage(p => p + 1)}
                  disabled={loading}
                  className="px-6 py-3 bg-white border border-slate-200 rounded-xl text-slate-700 font-medium hover:border-teal-300 transition-colors"
                >
                  {loading ? <Loader2 className="animate-spin inline" size={16} /> : (isRo ? 'Mai multe articole' : 'Load more')}
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
