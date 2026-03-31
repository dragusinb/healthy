import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { Mail, MessageSquare, Send, CheckCircle, HeartPulse, ArrowRight } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import usePageTitle from '../hooks/usePageTitle';
import useJsonLd from '../hooks/useJsonLd';
import PublicNav from '../components/PublicNav';
import api from '../api/client';

export default function Contact() {
  const { i18n } = useTranslation();
  const { user } = useAuth();
  const isRo = i18n.language === 'ro';
  const [form, setForm] = useState({ name: '', email: '', subject: '', message: '' });
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');

  usePageTitle(null, null, {
    title: isRo ? 'Contact — Analize.Online' : 'Contact — Analize.Online',
    description: isRo
      ? 'Contactează echipa Analize.Online pentru întrebări, sugestii sau parteneriate. Email: contact@analize.online.'
      : 'Contact the Analize.Online team for questions, suggestions, or partnerships. Email: contact@analize.online.',
  });

  useJsonLd({
    '@context': 'https://schema.org',
    '@type': 'ContactPage',
    name: isRo ? 'Contact Analize.Online' : 'Contact Analize.Online',
    url: 'https://analize.online/contact',
    mainEntity: {
      '@type': 'Organization',
      name: 'Analize.Online',
      email: 'contact@analize.online',
      url: 'https://analize.online',
    },
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name || !form.email || !form.message) return;
    setSending(true);
    setError('');
    try {
      await api.post('/support/contact', form);
      setSent(true);
    } catch (err) {
      setError(isRo ? 'A apărut o eroare. Trimite un email la contact@analize.online.' : 'An error occurred. Please email contact@analize.online.');
    } finally {
      setSending(false);
    }
  };

  const content = (
    <div className="max-w-3xl mx-auto">
      {/* Header */}
      <div className="mb-10">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 bg-blue-100 rounded-xl">
            <MessageSquare className="w-8 h-8 text-blue-600" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-slate-800">
              {isRo ? 'Contactează-ne' : 'Contact Us'}
            </h1>
            <p className="text-slate-500">
              {isRo ? 'Suntem aici să te ajutăm' : "We're here to help"}
            </p>
          </div>
        </div>
      </div>

      {/* Direct Email */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-6 mb-8">
        <div className="flex items-center gap-3">
          <Mail className="w-5 h-5 text-blue-600 flex-shrink-0" />
          <div>
            <p className="font-medium text-blue-800">
              {isRo ? 'Scrie-ne direct la:' : 'Email us directly at:'}
            </p>
            <a href="mailto:contact@analize.online" className="text-blue-600 font-semibold hover:underline text-lg">
              contact@analize.online
            </a>
          </div>
        </div>
      </div>

      {/* Contact Form */}
      {sent ? (
        <div className="bg-green-50 border border-green-200 rounded-2xl p-8 text-center">
          <CheckCircle className="w-12 h-12 text-green-500 mx-auto mb-4" />
          <h2 className="text-xl font-bold text-green-800 mb-2">
            {isRo ? 'Mesaj trimis!' : 'Message Sent!'}
          </h2>
          <p className="text-green-700">
            {isRo ? 'Mulțumim! Vom reveni cu un răspuns cât mai curând.' : 'Thank you! We will respond as soon as possible.'}
          </p>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="bg-white rounded-2xl border border-slate-200 p-6 space-y-5">
          <h2 className="text-lg font-bold text-slate-800">
            {isRo ? 'Trimite un mesaj' : 'Send a Message'}
          </h2>

          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                {isRo ? 'Nume' : 'Name'} *
              </label>
              <input
                type="text"
                value={form.name}
                onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:ring-2 focus:ring-teal-500 focus:border-transparent outline-none"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Email *</label>
              <input
                type="email"
                value={form.email}
                onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
                className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:ring-2 focus:ring-teal-500 focus:border-transparent outline-none"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              {isRo ? 'Subiect' : 'Subject'}
            </label>
            <input
              type="text"
              value={form.subject}
              onChange={e => setForm(f => ({ ...f, subject: e.target.value }))}
              className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:ring-2 focus:ring-teal-500 focus:border-transparent outline-none"
              placeholder={isRo ? 'Opțional' : 'Optional'}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">
              {isRo ? 'Mesaj' : 'Message'} *
            </label>
            <textarea
              value={form.message}
              onChange={e => setForm(f => ({ ...f, message: e.target.value }))}
              rows={5}
              className="w-full px-4 py-2.5 rounded-xl border border-slate-200 focus:ring-2 focus:ring-teal-500 focus:border-transparent outline-none resize-none"
              required
            />
          </div>

          {error && <p className="text-red-600 text-sm">{error}</p>}

          <button
            type="submit"
            disabled={sending}
            className="w-full flex items-center justify-center gap-2 px-6 py-3 bg-gradient-to-r from-cyan-500 to-teal-500 text-white font-semibold rounded-xl hover:shadow-lg transition-all disabled:opacity-50"
          >
            <Send size={18} />
            {sending
              ? (isRo ? 'Se trimite...' : 'Sending...')
              : (isRo ? 'Trimite mesajul' : 'Send Message')}
          </button>
        </form>
      )}

      {/* Info Section */}
      <div className="mt-8 bg-slate-50 rounded-2xl border border-slate-200 p-6">
        <h3 className="font-bold text-slate-800 mb-3">
          {isRo ? 'Alte modalități de contact' : 'Other Ways to Reach Us'}
        </h3>
        <div className="space-y-2 text-sm text-slate-600">
          <p>
            <strong>{isRo ? 'Parteneriate:' : 'Partnerships:'}</strong>{' '}
            <a href="mailto:contact@analize.online" className="text-teal-600 hover:underline">contact@analize.online</a>
          </p>
          <p>
            <strong>{isRo ? 'Suport tehnic:' : 'Technical Support:'}</strong>{' '}
            {isRo
              ? 'Dacă ai deja un cont, folosește secțiunea '
              : 'If you already have an account, use the '}
            <Link to="/support" className="text-teal-600 hover:underline">
              {isRo ? 'Suport' : 'Support'}
            </Link>
            {isRo ? ' din aplicație.' : ' section in the app.'}
          </p>
        </div>
      </div>

      {/* Footer links */}
      <div className="mt-8 pt-6 border-t border-slate-200 flex flex-wrap gap-4 text-sm text-slate-500">
        <Link to="/despre-noi" className="hover:text-teal-600">{isRo ? 'Despre noi' : 'About Us'}</Link>
        <Link to="/terms" className="hover:text-teal-600">{isRo ? 'Termeni' : 'Terms'}</Link>
        <Link to="/privacy" className="hover:text-teal-600">{isRo ? 'Confidențialitate' : 'Privacy'}</Link>
        <Link to="/disclaimer-medical" className="hover:text-teal-600">{isRo ? 'Disclaimer medical' : 'Medical Disclaimer'}</Link>
      </div>
    </div>
  );

  if (user) return content;

  return (
    <>
      <PublicNav />
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 py-12 px-4">
        {content}
      </div>
    </>
  );
}
