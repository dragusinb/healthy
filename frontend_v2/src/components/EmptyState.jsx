import React from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { FileText, Activity, Brain, Pill, Plus, ArrowRight, Upload, Stethoscope } from 'lucide-react';
import { cn } from '../lib/utils';

const EmptyState = ({ icon: Icon, title, description, actionLabel, actionTo, actionOnClick, className }) => (
    <div className={cn("flex flex-col items-center justify-center py-16 px-6 text-center", className)}>
        <div className="w-24 h-24 bg-gradient-to-br from-primary-50 to-primary-100 rounded-3xl flex items-center justify-center mb-6 shadow-sm">
            <Icon size={40} className="text-primary-500" />
        </div>
        <h3 className="text-xl font-bold text-slate-800 dark:text-slate-200 mb-2">{title}</h3>
        <p className="text-slate-600 dark:text-slate-400 max-w-sm mb-8 leading-relaxed">{description}</p>
        {actionLabel && actionTo && (
            <Link
                to={actionTo}
                className="inline-flex items-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-xl font-semibold hover:bg-primary-700 transition-colors shadow-md shadow-primary-500/20"
            >
                {actionLabel}
                <ArrowRight size={18} />
            </Link>
        )}
        {actionLabel && actionOnClick && (
            <button
                onClick={actionOnClick}
                className="inline-flex items-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-xl font-semibold hover:bg-primary-700 transition-colors shadow-md shadow-primary-500/20"
            >
                {actionLabel}
                <ArrowRight size={18} />
            </button>
        )}
    </div>
);

export const DocumentsEmpty = () => {
    const { t } = useTranslation();
    return (
        <EmptyState
            icon={FileText}
            title={t('emptyStates.documents.title')}
            description={t('emptyStates.documents.description')}
            actionLabel={t('emptyStates.documents.action')}
            actionTo="/linked-accounts"
        />
    );
};

export const BiomarkersEmpty = () => {
    const { t } = useTranslation();
    return (
        <EmptyState
            icon={Activity}
            title={t('emptyStates.biomarkers.title')}
            description={t('emptyStates.biomarkers.description')}
            actionLabel={t('emptyStates.biomarkers.action')}
            actionTo="/documents"
        />
    );
};

export const HealthReportsEmpty = ({ onRunAnalysis }) => {
    const { t } = useTranslation();
    return (
        <EmptyState
            icon={Brain}
            title={t('emptyStates.healthReports.title')}
            description={t('emptyStates.healthReports.description')}
            actionLabel={t('emptyStates.healthReports.action')}
            actionOnClick={onRunAnalysis}
        />
    );
};

export const MedicationsEmpty = () => {
    const { t } = useTranslation();
    return (
        <EmptyState
            icon={Pill}
            title={t('emptyStates.medications.title')}
            description={t('emptyStates.medications.description')}
        />
    );
};

export const ScreeningsEmpty = () => {
    const { t } = useTranslation();
    return (
        <EmptyState
            icon={Stethoscope}
            title={t('emptyStates.screenings.title')}
            description={t('emptyStates.screenings.description')}
            actionLabel={t('emptyStates.screenings.action')}
            actionTo="/health"
        />
    );
};

export default EmptyState;
