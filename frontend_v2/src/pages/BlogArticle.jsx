import React, { useEffect, useState } from 'react';
import { Link, useParams, Navigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, ArrowRight, Calendar, Tag, Loader2, BookOpen, Brain, Utensils, Dumbbell, ShoppingCart, HeartPulse, Activity, Sun, Clock, Share2 } from 'lucide-react';
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

export default function BlogArticle() {
  const { slug } = useParams();
  const { i18n } = useTranslation();
  const { user } = useAuth();
  const isRo = i18n.language === 'ro';
  const [article, setArticle] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    setLoading(true);
    setNotFound(false);
    api.get(`/blog/articles/${slug}`)
      .then(res => setArticle(res.data))
      .catch(e => {
        if (e.response?.status === 404) setNotFound(true);
      })
      .finally(() => setLoading(false));
  }, [slug]);

  const title = article ? (isRo ? article.title : (article.title_en || article.title)) : '';
  const content = article ? (isRo ? article.content_html : (article.content_html_en || article.content_html)) : '';
  const excerpt = article ? (isRo ? article.excerpt : (article.excerpt_en || article.excerpt)) : '';
  const meta = article ? (isRo ? article.meta_description : (article.meta_description_en || article.meta_description)) : '';

  usePageTitle(null, null, article ? {
    title: `${title} | Analize.Online`,
    description: meta || excerpt || '',
  } : {});

  useJsonLd(article ? {
    '@context': 'https://schema.org',
    '@type': 'Article',
    headline: title,
    description: meta || excerpt,
    datePublished: article.published_at,
    dateModified: article.updated_at || article.published_at,
    url: `https://analize.online/blog/${article.slug}`,
    inLanguage: isRo ? 'ro' : 'en',
    publisher: { '@type': 'Organization', name: 'Analize.Online', url: 'https://analize.online', logo: 'https://analize.online/healthy.svg' },
    author: { '@type': 'Organization', name: 'Analize.Online' },
    mainEntityOfPage: { '@type': 'WebPage', '@id': `https://analize.online/blog/${article.slug}` },
  } : null);

  if (notFound) return <Navigate to="/blog" replace />;

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <Loader2 className="animate-spin text-teal-500" size={32} />
      </div>
    );
  }

  if (!article) return null;

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    return new Date(dateStr).toLocaleDateString(isRo ? 'ro-RO' : 'en-US', {
      year: 'numeric', month: 'long', day: 'numeric',
    });
  };

  const readingTime = Math.max(3, Math.ceil((content?.length || 0) / 1200));
  const articleTags = (article.tags || '').split(',').map(t => t.trim()).filter(Boolean);
  const Icon = TOPIC_ICONS[article.topic_category] || BookOpen;
  const gradient = TOPIC_COLORS[article.topic_category] || 'from-teal-500 to-cyan-500';

  const shareUrl = `https://analize.online/blog/${article.slug}`;

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Public nav for guests */}
      {!user && <PublicNav />}

      {/* Article header with gradient */}
      <header className={`${!user ? 'pt-28' : 'pt-8'} pb-12 px-6 bg-gradient-to-br ${gradient} text-white relative overflow-hidden`}>
        <div className="absolute inset-0 opacity-10">
          <Icon size={300} className="absolute -right-10 -bottom-10 text-white" />
        </div>
        <div className="max-w-3xl mx-auto relative">
          {/* Breadcrumb */}
          <nav className="flex items-center gap-2 text-sm text-white/60 mb-6">
            <Link to="/" className="hover:text-white/90">Analize.Online</Link>
            <span>/</span>
            <Link to="/blog" className="hover:text-white/90">Blog</Link>
          </nav>

          <div className="flex items-center gap-3 mb-4">
            <span className="text-xs font-semibold bg-white/20 px-3 py-1 rounded-full">
              {article.topic_category?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) || 'Article'}
            </span>
            <span className="flex items-center gap-1 text-xs text-white/70">
              <Calendar size={12} /> {formatDate(article.published_at)}
            </span>
            <span className="flex items-center gap-1 text-xs text-white/70">
              <Clock size={12} /> {readingTime} min {isRo ? 'de citit' : 'read'}
            </span>
          </div>

          <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold leading-tight mb-4">
            {title}
          </h1>

          {excerpt && (
            <p className="text-lg text-white/80 max-w-2xl">
              {excerpt}
            </p>
          )}
        </div>
      </header>

      {/* Article body */}
      <div className="max-w-3xl mx-auto px-6 -mt-6">
        <article className="bg-white rounded-2xl shadow-sm border border-slate-200 p-8 md:p-12 mb-8">
          {/* Article content */}
          <div
            className="prose prose-slate prose-lg max-w-none
              prose-headings:text-slate-800 prose-headings:font-bold
              prose-h2:text-2xl prose-h2:mt-10 prose-h2:mb-4 prose-h2:pb-2 prose-h2:border-b prose-h2:border-slate-100
              prose-h3:text-xl prose-h3:mt-8 prose-h3:mb-3
              prose-p:text-slate-600 prose-p:leading-relaxed prose-p:text-[17px]
              prose-li:text-slate-600 prose-li:text-[17px]
              prose-strong:text-slate-800
              prose-a:text-teal-600 prose-a:no-underline hover:prose-a:underline
              prose-ul:my-4 prose-ol:my-4
              prose-blockquote:border-teal-500 prose-blockquote:bg-teal-50 prose-blockquote:rounded-r-xl prose-blockquote:py-1"
            dangerouslySetInnerHTML={{ __html: content }}
          />

          {/* Tags */}
          {articleTags.length > 0 && (
            <div className="flex flex-wrap gap-2 mt-10 pt-6 border-t border-slate-100">
              {articleTags.map(tag => (
                <Link
                  key={tag}
                  to={`/blog?tag=${encodeURIComponent(tag)}`}
                  className="inline-flex items-center gap-1.5 text-sm bg-slate-100 text-slate-600 px-4 py-1.5 rounded-full hover:bg-slate-200 transition-colors"
                >
                  <Tag size={12} />
                  {tag}
                </Link>
              ))}
            </div>
          )}

          {/* Share */}
          <div className="flex items-center gap-3 mt-6 pt-6 border-t border-slate-100">
            <span className="text-sm text-slate-400">{isRo ? 'Distribuie:' : 'Share:'}</span>
            <a
              href={`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}`}
              target="_blank"
              rel="noopener noreferrer"
              className="px-3 py-1.5 rounded-lg text-sm bg-blue-50 text-blue-600 hover:bg-blue-100 transition-colors"
            >
              Facebook
            </a>
            <a
              href={`https://wa.me/?text=${encodeURIComponent(title + ' ' + shareUrl)}`}
              target="_blank"
              rel="noopener noreferrer"
              className="px-3 py-1.5 rounded-lg text-sm bg-green-50 text-green-600 hover:bg-green-100 transition-colors"
            >
              WhatsApp
            </a>
            <button
              onClick={() => navigator.clipboard?.writeText(shareUrl)}
              className="px-3 py-1.5 rounded-lg text-sm bg-slate-100 text-slate-600 hover:bg-slate-200 transition-colors flex items-center gap-1"
            >
              <Share2 size={12} /> {isRo ? 'Copiază link' : 'Copy link'}
            </button>
          </div>
        </article>

        {/* Inline CTA — mid page */}
        <div className="bg-gradient-to-r from-teal-500 to-cyan-600 rounded-2xl p-8 md:p-10 text-white mb-8">
          <div className="flex flex-col md:flex-row items-center gap-6">
            <div className="flex-1">
              <h3 className="text-xl md:text-2xl font-bold mb-2">
                {isRo
                  ? 'Vrei sfaturi personalizate, nu generice?'
                  : 'Want personalized advice, not generic?'}
              </h3>
              <p className="text-teal-100">
                {isRo
                  ? 'Încarcă analizele tale pe Analize.Online și primești plan nutrițional cu rețete românești, program de exerciții și listă de cumpărături — toate bazate pe valorile tale reale.'
                  : 'Upload your lab results on Analize.Online and get a nutrition plan with Romanian recipes, exercise program and grocery list — all based on your real values.'}
              </p>
            </div>
            <Link
              to="/login"
              className="shrink-0 inline-flex items-center gap-2 px-8 py-3 bg-white text-teal-700 rounded-xl font-bold hover:bg-teal-50 transition-colors shadow-lg"
            >
              {isRo ? 'Începe Gratuit' : 'Start Free'}
              <ArrowRight size={18} />
            </Link>
          </div>
        </div>

        {/* Feature grid CTA */}
        <div className="bg-white rounded-2xl border border-slate-200 p-8 md:p-10 mb-8">
          <h3 className="text-xl font-bold text-slate-800 mb-6 text-center">
            {isRo ? 'Ce primești pe Analize.Online' : 'What you get on Analize.Online'}
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { icon: Brain, title: isRo ? 'Specialiști AI' : 'AI Specialists', desc: isRo ? 'Cardiolog, Endocrinolog, Hematolog...' : 'Cardiologist, Endocrinologist...' },
              { icon: Utensils, title: isRo ? 'Rețete românești' : 'Romanian recipes', desc: isRo ? 'Plan de 7 zile cu porții exacte' : '7-day plan with exact portions' },
              { icon: Dumbbell, title: isRo ? 'Plan exerciții' : 'Exercise plan', desc: isRo ? 'Adaptat profilului tău medical' : 'Adapted to your medical profile' },
              { icon: ShoppingCart, title: isRo ? 'Listă cumpărături' : 'Grocery list', desc: isRo ? 'Organizată pe categorii' : 'Organized by category' },
            ].map((f, i) => (
              <div key={i} className="text-center p-4">
                <div className="w-12 h-12 bg-teal-50 rounded-xl flex items-center justify-center mx-auto mb-3">
                  <f.icon size={22} className="text-teal-600" />
                </div>
                <h4 className="font-semibold text-slate-800 text-sm mb-1">{f.title}</h4>
                <p className="text-xs text-slate-500">{f.desc}</p>
              </div>
            ))}
          </div>
          <div className="text-center mt-6">
            <Link
              to="/login"
              className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-cyan-500 to-teal-500 text-white rounded-xl font-semibold hover:from-cyan-600 hover:to-teal-600 transition-all shadow-md"
            >
              {isRo ? 'Creează Cont Gratuit' : 'Create Free Account'}
              <ArrowRight size={16} />
            </Link>
          </div>
        </div>

        {/* Back to blog */}
        <div className="text-center pb-12">
          <Link to="/blog" className="inline-flex items-center gap-2 text-slate-500 hover:text-teal-600 font-medium transition-colors">
            <ArrowLeft size={16} />
            {isRo ? 'Toate articolele' : 'All articles'}
          </Link>
        </div>
      </div>
    </div>
  );
}
