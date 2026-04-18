import React, { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowRight, Calendar, Loader2, BookOpen, Utensils, Dumbbell, ShoppingCart, Brain, Activity, Sun, HeartPulse } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import usePageTitle from '../hooks/usePageTitle';
import useJsonLd from '../hooks/useJsonLd';
import PublicNav from '../components/PublicNav';
import api from '../api/client';

const TOPIC_ICONS = {
  aggregation: Activity,
  ai_specialists: Brain,
  fitness_nutrition: Dumbbell,
  romanian_recipes: Utensils,
  grocery_lists: ShoppingCart,
  biomarker_deep_dive: HeartPulse,
  seasonal_health: Sun,
};

const TOPIC_COLORS = {
  aggregation: 'from-blue-500 to-cyan-500',
  ai_specialists: 'from-violet-500 to-purple-500',
  fitness_nutrition: 'from-orange-500 to-amber-500',
  romanian_recipes: 'from-rose-500 to-pink-500',
  grocery_lists: 'from-emerald-500 to-green-500',
  biomarker_deep_dive: 'from-red-500 to-rose-500',
  seasonal_health: 'from-yellow-500 to-amber-400',
};

const TOPIC_LABELS_RO = {
  aggregation: 'Agregare analize',
  ai_specialists: 'Specialiști AI',
  fitness_nutrition: 'Fitness & Nutriție',
  romanian_recipes: 'Rețete românești',
  grocery_lists: 'Cumpărături',
  biomarker_deep_dive: 'Biomarkeri',
  seasonal_health: 'Sănătate sezonieră',
};

const TOPIC_LABELS_EN = {
  aggregation: 'Lab aggregation',
  ai_specialists: 'AI specialists',
  fitness_nutrition: 'Fitness & Nutrition',
  romanian_recipes: 'Romanian recipes',
  grocery_lists: 'Grocery lists',
  biomarker_deep_dive: 'Biomarkers',
  seasonal_health: 'Seasonal health',
};

export default function BlogList() {
  const { i18n } = useTranslation();
  const { user } = useAuth();
  const isRo = i18n.language === 'ro';
  const [searchParams] = useSearchParams();
  const [articles, setArticles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(false);
  const [selectedTag, setSelectedTag] = useState(searchParams.get('tag') || null);
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
    url: 'https://analize.online/blog',
    publisher: { '@type': 'Organization', name: 'Analize.Online', url: 'https://analize.online' },
  });

  useEffect(() => { fetchArticles(); fetchTags(); }, [page, selectedTag]);

  const fetchArticles = async () => {
    setLoading(true);
    try {
      const params = { page, limit: 12 };
      if (selectedTag) params.tag = selectedTag;
      const res = await api.get('/blog/articles', { params });
      if (page === 1) setArticles(res.data.articles || []);
      else setArticles(prev => [...prev, ...(res.data.articles || [])]);
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
    return new Date(dateStr).toLocaleDateString(isRo ? 'ro-RO' : 'en-US', {
      year: 'numeric', month: 'long', day: 'numeric',
    });
  };

  const topicLabels = isRo ? TOPIC_LABELS_RO : TOPIC_LABELS_EN;

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Public nav for guests */}
      {!user && <PublicNav />}

      {/* Hero */}
      <section className={`${!user ? 'pt-28' : 'pt-8'} pb-12 px-6 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white`}>
        <div className="max-w-5xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 bg-white/10 px-4 py-2 rounded-full text-sm mb-6">
            <BookOpen size={16} />
            {isRo ? 'Articole noi în fiecare săptămână' : 'New articles every week'}
          </div>
          <h1 className="text-3xl md:text-5xl font-bold mb-4">
            {isRo ? 'Blog Sănătate' : 'Health Blog'}
          </h1>
          <p className="text-lg text-slate-300 max-w-2xl mx-auto">
            {isRo
              ? 'Nutriție cu rețete românești, interpretare analize de sânge, fitness personalizat și sfaturi de sănătate bazate pe știință.'
              : 'Nutrition with Romanian recipes, blood test interpretation, personalized fitness and science-based health tips.'}
          </p>
        </div>
      </section>

      <div className="max-w-6xl mx-auto px-6 py-8">
        {/* Tag filters */}
        {tags.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-8">
            <button
              onClick={() => { setSelectedTag(null); setPage(1); }}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                !selectedTag
                  ? 'bg-slate-800 text-white shadow-md'
                  : 'bg-white border border-slate-200 text-slate-600 hover:border-slate-400'
              }`}
            >
              {isRo ? 'Toate' : 'All'}
            </button>
            {tags.map(t => (
              <button
                key={t.tag}
                onClick={() => { setSelectedTag(t.tag); setPage(1); }}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                  selectedTag === t.tag
                    ? 'bg-slate-800 text-white shadow-md'
                    : 'bg-white border border-slate-200 text-slate-600 hover:border-slate-400'
                }`}
              >
                {t.tag} <span className="text-slate-400 ml-1">{t.count}</span>
              </button>
            ))}
          </div>
        )}

        {/* Articles */}
        {loading && articles.length === 0 ? (
          <div className="flex justify-center py-20">
            <Loader2 className="animate-spin text-teal-500" size={32} />
          </div>
        ) : articles.length === 0 ? (
          <div className="text-center py-20 text-slate-500">
            <BookOpen size={48} className="mx-auto mb-4 text-slate-300" />
            <p className="text-lg">{isRo ? 'Niciun articol încă.' : 'No articles yet.'}</p>
            <p className="mt-2">{isRo ? 'Revino în curând — publicăm săptămânal!' : 'Check back soon — we publish weekly!'}</p>
          </div>
        ) : (
          <>
            {/* Featured first article */}
            {page === 1 && articles.length > 0 && (
              <Link
                to={`/blog/${articles[0].slug}`}
                className="block mb-8 bg-white rounded-2xl border border-slate-200 overflow-hidden hover:shadow-xl transition-all group"
              >
                <div className="grid md:grid-cols-2">
                  <div className={`bg-gradient-to-br ${TOPIC_COLORS[articles[0].topic_category] || 'from-teal-500 to-cyan-500'} p-8 md:p-12 flex items-center justify-center min-h-[200px]`}>
                    {(() => {
                      const Icon = TOPIC_ICONS[articles[0].topic_category] || BookOpen;
                      return <Icon size={80} className="text-white/30" />;
                    })()}
                  </div>
                  <div className="p-8 md:p-12 flex flex-col justify-center">
                    <div className="flex items-center gap-3 mb-3">
                      <span className="text-xs font-semibold text-teal-600 bg-teal-50 px-3 py-1 rounded-full">
                        {topicLabels[articles[0].topic_category] || 'Articol'}
                      </span>
                      <span className="text-xs text-slate-400">{formatDate(articles[0].published_at)}</span>
                    </div>
                    <h2 className="text-2xl md:text-3xl font-bold text-slate-800 group-hover:text-teal-700 transition-colors mb-3">
                      {isRo ? articles[0].title : (articles[0].title_en || articles[0].title)}
                    </h2>
                    <p className="text-slate-500 mb-4 line-clamp-3">
                      {isRo ? articles[0].excerpt : (articles[0].excerpt_en || articles[0].excerpt)}
                    </p>
                    <span className="inline-flex items-center gap-2 text-teal-600 font-semibold group-hover:gap-3 transition-all">
                      {isRo ? 'Citește articolul' : 'Read article'} <ArrowRight size={16} />
                    </span>
                  </div>
                </div>
              </Link>
            )}

            {/* Rest of articles grid */}
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {articles.slice(page === 1 ? 1 : 0).map(a => {
                const Icon = TOPIC_ICONS[a.topic_category] || BookOpen;
                const color = TOPIC_COLORS[a.topic_category] || 'from-teal-500 to-cyan-500';
                return (
                  <Link
                    key={a.slug}
                    to={`/blog/${a.slug}`}
                    className="bg-white rounded-2xl border border-slate-200 overflow-hidden hover:shadow-lg hover:border-slate-300 transition-all group"
                  >
                    {/* Topic color banner with icon */}
                    <div className={`bg-gradient-to-br ${color} px-6 py-8 flex items-center justify-between`}>
                      <Icon size={32} className="text-white/40" />
                      <span className="text-xs font-semibold text-white/80 bg-white/20 px-3 py-1 rounded-full">
                        {topicLabels[a.topic_category] || 'Articol'}
                      </span>
                    </div>
                    <div className="p-6">
                      <div className="text-xs text-slate-400 mb-2 flex items-center gap-1.5">
                        <Calendar size={12} />
                        {formatDate(a.published_at)}
                      </div>
                      <h2 className="text-lg font-bold text-slate-800 group-hover:text-teal-700 transition-colors mb-2 line-clamp-2">
                        {isRo ? a.title : (a.title_en || a.title)}
                      </h2>
                      <p className="text-sm text-slate-500 line-clamp-3 mb-4">
                        {isRo ? a.excerpt : (a.excerpt_en || a.excerpt)}
                      </p>
                      <span className="text-sm text-teal-600 font-semibold flex items-center gap-1 group-hover:gap-2 transition-all">
                        {isRo ? 'Citește' : 'Read'} <ArrowRight size={14} />
                      </span>
                    </div>
                  </Link>
                );
              })}
            </div>

            {hasMore && (
              <div className="text-center mt-10">
                <button
                  onClick={() => setPage(p => p + 1)}
                  disabled={loading}
                  className="px-8 py-3 bg-white border border-slate-200 rounded-xl text-slate-700 font-medium hover:border-slate-400 hover:shadow-md transition-all"
                >
                  {loading ? <Loader2 className="animate-spin inline" size={16} /> : (isRo ? 'Mai multe articole' : 'Load more')}
                </button>
              </div>
            )}
          </>
        )}

        {/* Bottom CTA */}
        <section className="mt-16 mb-8 bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl p-8 md:p-12 text-white">
          <div className="grid md:grid-cols-2 gap-8 items-center">
            <div>
              <h2 className="text-2xl md:text-3xl font-bold mb-4">
                {isRo
                  ? 'Sfaturile generice nu funcționează. Cele personalizate, da.'
                  : "Generic advice doesn't work. Personalized advice does."}
              </h2>
              <p className="text-slate-300 mb-6">
                {isRo
                  ? 'Pe Analize.Online primești plan nutrițional cu rețete românești, program de exerciții și interpretare de la specialiști AI — totul bazat pe analizele tale reale, nu pe un articol de blog.'
                  : 'On Analize.Online you get a nutrition plan with Romanian recipes, exercise program and AI specialist interpretation — all based on your real lab results, not a blog article.'}
              </p>
              <Link
                to="/nutrition-preview"
                className="inline-flex items-center gap-2 px-8 py-3 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-xl font-semibold hover:from-amber-600 hover:to-orange-600 transition-all shadow-lg shadow-amber-500/20"
              >
                {isRo ? 'Încearcă planul alimentar gratuit' : 'Try the free meal plan'}
                <ArrowRight size={18} />
              </Link>
            </div>
            <div className="hidden md:flex justify-center">
              <div className="grid grid-cols-2 gap-3 text-sm">
                {[
                  { icon: Brain, text: isRo ? 'Specialiști AI' : 'AI Specialists' },
                  { icon: Utensils, text: isRo ? 'Rețete românești' : 'Romanian recipes' },
                  { icon: Dumbbell, text: isRo ? 'Plan exerciții' : 'Exercise plan' },
                  { icon: ShoppingCart, text: isRo ? 'Listă cumpărături' : 'Grocery list' },
                ].map((item, i) => (
                  <div key={i} className="flex items-center gap-2 bg-white/10 rounded-xl px-4 py-3">
                    <item.icon size={16} className="text-teal-400" />
                    <span className="text-white/90">{item.text}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
