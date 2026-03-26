import React, { useEffect, useState } from 'react';
import { Link, useParams, Navigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, ArrowRight, Calendar, Tag, Loader2 } from 'lucide-react';
import usePageTitle from '../hooks/usePageTitle';
import useJsonLd from '../hooks/useJsonLd';
import api from '../api/client';

export default function BlogArticle() {
  const { slug } = useParams();
  const { i18n } = useTranslation();
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
        console.error('Failed to fetch article', e);
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
    publisher: {
      '@type': 'Organization',
      name: 'Analize.Online',
      url: 'https://analize.online',
      logo: 'https://analize.online/healthy.svg',
    },
    author: {
      '@type': 'Organization',
      name: 'Analize.Online',
    },
    mainEntityOfPage: {
      '@type': 'WebPage',
      '@id': `https://analize.online/blog/${article.slug}`,
    },
  } : null);

  if (notFound) return <Navigate to="/blog" replace />;

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="animate-spin text-teal-500" size={32} />
      </div>
    );
  }

  if (!article) return null;

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const d = new Date(dateStr);
    return d.toLocaleDateString(isRo ? 'ro-RO' : 'en-US', {
      year: 'numeric', month: 'long', day: 'numeric',
    });
  };

  const articleTags = (article.tags || '').split(',').map(t => t.trim()).filter(Boolean);

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-white">
      {/* Breadcrumb */}
      <div className="bg-white border-b border-slate-100">
        <div className="max-w-3xl mx-auto px-6 py-3">
          <nav className="flex items-center gap-2 text-sm text-slate-500">
            <Link to="/" className="hover:text-teal-600">Analize.Online</Link>
            <span>/</span>
            <Link to="/blog" className="hover:text-teal-600">Blog</Link>
            <span>/</span>
            <span className="text-slate-800 font-medium truncate">{title}</span>
          </nav>
        </div>
      </div>

      <article className="max-w-3xl mx-auto px-6 py-8">
        {/* Back */}
        <Link to="/blog" className="inline-flex items-center gap-2 text-sm text-teal-600 hover:text-teal-800 mb-6">
          <ArrowLeft size={16} />
          {isRo ? 'Toate articolele' : 'All articles'}
        </Link>

        {/* Header */}
        <header className="mb-8">
          <div className="flex items-center gap-3 text-sm text-slate-400 mb-4">
            <Calendar size={14} />
            {formatDate(article.published_at)}
          </div>
          <h1 className="text-3xl md:text-4xl font-bold text-slate-800 mb-4 leading-tight">
            {title}
          </h1>
          {articleTags.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {articleTags.map(tag => (
                <Link
                  key={tag}
                  to={`/blog?tag=${encodeURIComponent(tag)}`}
                  className="inline-flex items-center gap-1 text-xs bg-teal-50 text-teal-700 px-3 py-1 rounded-full hover:bg-teal-100 transition-colors"
                >
                  <Tag size={10} />
                  {tag}
                </Link>
              ))}
            </div>
          )}
        </header>

        {/* Article content */}
        <div
          className="prose prose-slate prose-lg max-w-none
            prose-headings:text-slate-800 prose-headings:font-bold
            prose-h2:text-2xl prose-h2:mt-10 prose-h2:mb-4
            prose-h3:text-xl prose-h3:mt-8 prose-h3:mb-3
            prose-p:text-slate-600 prose-p:leading-relaxed
            prose-li:text-slate-600
            prose-strong:text-slate-800
            prose-a:text-teal-600 prose-a:no-underline hover:prose-a:underline"
          dangerouslySetInnerHTML={{ __html: content }}
        />

        {/* CTA */}
        <section className="mt-12 bg-gradient-to-r from-teal-500 to-cyan-600 rounded-2xl p-8 text-white text-center">
          <h2 className="text-2xl font-bold mb-3">
            {isRo
              ? 'Vrei sfaturi personalizate bazate pe analizele tale?'
              : 'Want personalized advice based on your lab results?'}
          </h2>
          <p className="text-teal-100 mb-6 max-w-lg mx-auto">
            {isRo
              ? 'Pe Analize.Online primești plan nutrițional cu rețete românești, program de exerciții și interpretare de la specialiști AI — totul bazat pe valorile tale reale din analize.'
              : 'On Analize.Online you get a nutrition plan with Romanian recipes, exercise program and AI specialist interpretation — all based on your real lab values.'}
          </p>
          <Link
            to="/login"
            className="inline-flex items-center gap-2 px-8 py-3 bg-white text-teal-700 rounded-xl font-semibold hover:bg-teal-50 transition-colors"
          >
            {isRo ? 'Creează Cont Gratuit' : 'Create Free Account'}
            <ArrowRight size={18} />
          </Link>
        </section>
      </article>
    </div>
  );
}
