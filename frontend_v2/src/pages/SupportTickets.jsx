import React, { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { MessageSquare, Clock, CheckCircle, AlertCircle, ChevronRight, ExternalLink, Image, Wrench, X, Loader2 } from 'lucide-react';
import api from '../api/client';
import { useAuth } from '../context/AuthContext';

const statusColors = {
    open: 'bg-blue-100 text-blue-700',
    in_progress: 'bg-yellow-100 text-yellow-700',
    resolved: 'bg-green-100 text-green-700',
    closed: 'bg-gray-100 text-gray-700'
};

const aiStatusColors = {
    pending: 'bg-slate-100 text-slate-600',
    processing: 'bg-blue-100 text-blue-700',
    fixed: 'bg-green-100 text-green-700',
    skipped: 'bg-orange-100 text-orange-700',
    escalated: 'bg-red-100 text-red-700'
};

const StatusBadge = ({ status, type = 'status' }) => {
    const colors = type === 'ai' ? aiStatusColors : statusColors;
    return (
        <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[status] || 'bg-gray-100 text-gray-600'}`}>
            {status}
        </span>
    );
};

export default function SupportTickets() {
    const { t } = useTranslation();
    const { user } = useAuth();
    const isAdmin = user?.is_admin;

    const [tickets, setTickets] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedTicket, setSelectedTicket] = useState(null);
    const [ticketDetail, setTicketDetail] = useState(null);
    const [loadingDetail, setLoadingDetail] = useState(false);
    const [updatingStatus, setUpdatingStatus] = useState(false);
    const [statusResponse, setStatusResponse] = useState('');
    const [viewMode, setViewMode] = useState('mine'); // 'mine' or 'all' (admin only)

    useEffect(() => {
        fetchTickets();
    }, [isAdmin, viewMode]);

    const fetchTickets = async () => {
        setLoading(true);
        try {
            // Admin can view 'mine' or 'all', regular users always see their own
            const endpoint = (isAdmin && viewMode === 'all') ? '/support/admin/tickets' : '/support/tickets';
            const response = await api.get(endpoint);
            setTickets(response.data);
            // Reset selection when switching views
            setSelectedTicket(null);
            setTicketDetail(null);
        } catch (err) {
            setError(t('common.error'));
        } finally {
            setLoading(false);
        }
    };

    const fetchTicketDetail = async (ticketId) => {
        setLoadingDetail(true);
        try {
            // Use admin endpoint when viewing all tickets
            const endpoint = (isAdmin && viewMode === 'all') ? `/support/admin/tickets/${ticketId}` : `/support/tickets/${ticketId}`;
            const response = await api.get(endpoint);
            setTicketDetail(response.data);
            setStatusResponse(response.data.ai_response || '');
        } catch (err) {
            console.error('Failed to fetch ticket detail:', err);
        } finally {
            setLoadingDetail(false);
        }
    };

    const handleTicketClick = (ticket) => {
        setSelectedTicket(ticket.id);
        fetchTicketDetail(ticket.id);
    };

    const updateTicketStatus = async (newStatus) => {
        if (!ticketDetail) return;

        setUpdatingStatus(true);
        try {
            await api.patch(`/support/admin/tickets/${ticketDetail.id}/status`, {
                ai_status: newStatus,
                ai_response: statusResponse || null
            });
            // Refresh data
            await fetchTickets();
            await fetchTicketDetail(ticketDetail.id);
        } catch (err) {
            console.error('Failed to update ticket status:', err);
        } finally {
            setUpdatingStatus(false);
        }
    };

    const formatDate = (dateStr) => {
        if (!dateStr) return '-';
        const date = new Date(dateStr);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-64">
                <div className="w-8 h-8 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin" />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center gap-3">
                <div className={`p-3 rounded-xl ${isAdmin && viewMode === 'all' ? 'bg-amber-100' : 'bg-primary-100'}`}>
                    <MessageSquare size={24} className={isAdmin && viewMode === 'all' ? 'text-amber-600' : 'text-primary-600'} />
                </div>
                <div>
                    <h1 className="text-2xl font-bold text-slate-800">
                        {t('tickets.title')}
                    </h1>
                    <p className="text-slate-500">{t('tickets.subtitle')}</p>
                </div>
            </div>

            {/* Admin Tabs */}
            {isAdmin && (
                <div className="flex gap-2">
                    <button
                        onClick={() => setViewMode('mine')}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                            viewMode === 'mine'
                                ? 'bg-primary-100 text-primary-700'
                                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                        }`}
                    >
                        {t('tickets.myTickets')}
                    </button>
                    <button
                        onClick={() => setViewMode('all')}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                            viewMode === 'all'
                                ? 'bg-amber-100 text-amber-700'
                                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                        }`}
                    >
                        {t('tickets.allTickets')}
                    </button>
                </div>
            )}

            {error && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-red-700">
                    {error}
                </div>
            )}

            {tickets.length === 0 ? (
                <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-12 text-center">
                    <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <MessageSquare size={32} className="text-slate-400" />
                    </div>
                    <h3 className="text-lg font-semibold text-slate-700 mb-2">{t('tickets.noTickets')}</h3>
                    <p className="text-slate-500">{t('tickets.noTicketsHint')}</p>
                </div>
            ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* Tickets List */}
                    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
                        <div className="p-4 border-b border-slate-100">
                            <h2 className="font-semibold text-slate-700">
                                {isAdmin && viewMode === 'all' ? t('tickets.allTickets') : t('tickets.yourTickets')} ({tickets.length})
                            </h2>
                        </div>
                        <div className="divide-y divide-slate-100 max-h-[600px] overflow-y-auto">
                            {tickets.map((ticket) => (
                                <div
                                    key={ticket.id}
                                    onClick={() => handleTicketClick(ticket)}
                                    className={`p-4 cursor-pointer hover:bg-slate-50 transition-colors ${selectedTicket === ticket.id ? 'bg-primary-50 border-l-4 border-l-primary-500' : ''}`}
                                >
                                    <div className="flex items-start justify-between gap-3">
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-2 mb-1">
                                                <span className="font-mono text-sm text-slate-500">{ticket.ticket_number}</span>
                                                <StatusBadge status={ticket.status} />
                                            </div>
                                            <p className="text-slate-700 truncate">{ticket.description.substring(0, 80)}...</p>
                                            <div className="flex items-center gap-3 mt-2 text-xs text-slate-400">
                                                <span className="flex items-center gap-1">
                                                    <Clock size={12} />
                                                    {formatDate(ticket.created_at)}
                                                </span>
                                                {ticket.attachments_count > 0 && (
                                                    <span className="flex items-center gap-1">
                                                        <Image size={12} />
                                                        {ticket.attachments_count}
                                                    </span>
                                                )}
                                                {isAdmin && viewMode === 'all' && ticket.reporter_email && (
                                                    <span className="text-slate-500">
                                                        {ticket.reporter_email}
                                                    </span>
                                                )}
                                            </div>
                                        </div>
                                        <ChevronRight size={20} className="text-slate-300 flex-shrink-0" />
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Ticket Detail */}
                    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
                        {!selectedTicket ? (
                            <div className="p-12 text-center text-slate-400">
                                <MessageSquare size={48} className="mx-auto mb-4 opacity-50" />
                                <p>{t('tickets.selectTicket')}</p>
                            </div>
                        ) : loadingDetail ? (
                            <div className="flex items-center justify-center h-64">
                                <div className="w-8 h-8 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin" />
                            </div>
                        ) : ticketDetail && (
                            <div className="p-6 space-y-6 max-h-[600px] overflow-y-auto">
                                {/* Header */}
                                <div>
                                    <div className="flex items-center gap-2 mb-2">
                                        <span className="font-mono text-lg font-semibold text-slate-700">{ticketDetail.ticket_number}</span>
                                        <StatusBadge status={ticketDetail.status} />
                                        <StatusBadge status={ticketDetail.ai_status} type="ai" />
                                    </div>
                                    <p className="text-sm text-slate-500">
                                        {t('tickets.submittedOn')} {formatDate(ticketDetail.created_at)}
                                    </p>
                                </div>

                                {/* Page URL */}
                                <div>
                                    <label className="block text-xs font-medium text-slate-400 uppercase mb-1">{t('tickets.pageUrl')}</label>
                                    <a
                                        href={ticketDetail.page_url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-primary-600 hover:text-primary-700 flex items-center gap-1 text-sm"
                                    >
                                        {ticketDetail.page_url}
                                        <ExternalLink size={14} />
                                    </a>
                                </div>

                                {/* Description */}
                                <div>
                                    <label className="block text-xs font-medium text-slate-400 uppercase mb-1">{t('tickets.description')}</label>
                                    <p className="text-slate-700 whitespace-pre-wrap bg-slate-50 rounded-lg p-3">
                                        {ticketDetail.description}
                                    </p>
                                </div>

                                {/* AI Response */}
                                {ticketDetail.ai_response && (
                                    <div>
                                        <label className="block text-xs font-medium text-slate-400 uppercase mb-1">{t('tickets.aiResponse')}</label>
                                        <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                                            <p className="text-green-800 whitespace-pre-wrap">{ticketDetail.ai_response}</p>
                                            {ticketDetail.ai_fixed_at && (
                                                <p className="text-xs text-green-600 mt-2">
                                                    {t('tickets.fixedOn')} {formatDate(ticketDetail.ai_fixed_at)}
                                                </p>
                                            )}
                                        </div>
                                    </div>
                                )}

                                {/* Attachments */}
                                {ticketDetail.attachments && ticketDetail.attachments.length > 0 && (
                                    <div>
                                        <label className="block text-xs font-medium text-slate-400 uppercase mb-2">{t('tickets.attachments')}</label>
                                        <div className="space-y-2">
                                            {ticketDetail.attachments.map((att) => (
                                                <div key={att.id} className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                                                    <Image size={20} className="text-slate-400" />
                                                    <div>
                                                        <p className="text-sm font-medium text-slate-700">{att.file_name}</p>
                                                        <p className="text-xs text-slate-400">{Math.round(att.file_size / 1024)} KB</p>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {/* Admin Controls - only show when viewing all tickets */}
                                {isAdmin && viewMode === 'all' && (
                                    <div className="border-t border-slate-200 pt-4 mt-4">
                                        <label className="block text-xs font-medium text-slate-400 uppercase mb-2">
                                            {t('tickets.updateStatus')}
                                        </label>

                                        {/* Response textarea */}
                                        <textarea
                                            value={statusResponse}
                                            onChange={(e) => setStatusResponse(e.target.value)}
                                            rows={3}
                                            className="w-full px-3 py-2 mb-3 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500"
                                            placeholder={t('tickets.responseNote')}
                                        />

                                        {/* Status buttons */}
                                        <div className="flex flex-wrap gap-2">
                                            <button
                                                onClick={() => updateTicketStatus('pending')}
                                                disabled={updatingStatus || ticketDetail.ai_status === 'pending'}
                                                className="px-3 py-2 bg-slate-100 text-slate-700 rounded-lg text-sm font-medium hover:bg-slate-200 disabled:opacity-50 flex items-center gap-1"
                                            >
                                                <Clock size={14} />
                                                Pending
                                            </button>
                                            <button
                                                onClick={() => updateTicketStatus('processing')}
                                                disabled={updatingStatus || ticketDetail.ai_status === 'processing'}
                                                className="px-3 py-2 bg-blue-100 text-blue-700 rounded-lg text-sm font-medium hover:bg-blue-200 disabled:opacity-50 flex items-center gap-1"
                                            >
                                                <Wrench size={14} />
                                                {t('tickets.markForFix')}
                                            </button>
                                            <button
                                                onClick={() => updateTicketStatus('fixed')}
                                                disabled={updatingStatus || ticketDetail.ai_status === 'fixed'}
                                                className="px-3 py-2 bg-green-100 text-green-700 rounded-lg text-sm font-medium hover:bg-green-200 disabled:opacity-50 flex items-center gap-1"
                                            >
                                                <CheckCircle size={14} />
                                                {t('tickets.markFixed')}
                                            </button>
                                            <button
                                                onClick={() => updateTicketStatus('skipped')}
                                                disabled={updatingStatus || ticketDetail.ai_status === 'skipped'}
                                                className="px-3 py-2 bg-orange-100 text-orange-700 rounded-lg text-sm font-medium hover:bg-orange-200 disabled:opacity-50 flex items-center gap-1"
                                            >
                                                <X size={14} />
                                                {t('tickets.markSkipped')}
                                            </button>
                                            {updatingStatus && (
                                                <Loader2 size={20} className="animate-spin text-slate-400" />
                                            )}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
