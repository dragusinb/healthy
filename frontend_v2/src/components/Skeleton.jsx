import React from 'react';
import { cn } from '../lib/utils';

/**
 * Base skeleton shimmer element.
 * Use Tailwind classes via `className` to control width, height, and shape.
 */
const Skeleton = ({ className }) => (
    <div className={cn("animate-pulse bg-slate-200 rounded", className)} />
);

/**
 * Dashboard page skeleton.
 * Matches: Health Overview card, Health Score card, 3 stat cards, 3 quick-action cards, AI summary card, timeline card.
 */
const DashboardSkeleton = () => (
    <div>
        {/* Health Overview card */}
        <div className="card p-6 mb-8">
            <div className="flex items-center gap-2 mb-6">
                <Skeleton className="w-8 h-8 rounded-lg" />
                <Skeleton className="h-5 w-40" />
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Patient identity */}
                <div className="space-y-4">
                    <div className="flex items-center gap-3">
                        <Skeleton className="w-14 h-14 rounded-full" />
                        <div className="space-y-2">
                            <Skeleton className="h-5 w-36" />
                            <Skeleton className="h-3 w-24" />
                        </div>
                    </div>
                    <div className="p-3 bg-slate-50 rounded-xl space-y-3">
                        <Skeleton className="h-3 w-full" />
                        <Skeleton className="h-3 w-3/4" />
                        <Skeleton className="h-3 w-1/2" />
                    </div>
                </div>
                {/* Health status */}
                <div className="space-y-3">
                    <Skeleton className="h-3 w-28" />
                    <Skeleton className="h-16 w-full rounded-xl" />
                </div>
                {/* Reminders */}
                <div className="space-y-3">
                    <Skeleton className="h-3 w-24" />
                    <Skeleton className="h-16 w-full rounded-xl" />
                </div>
            </div>
        </div>

        {/* Health Score card */}
        <div className="card p-6 mb-8">
            <div className="flex items-center justify-between mb-4">
                <Skeleton className="h-5 w-32" />
                <Skeleton className="h-4 w-20" />
            </div>
            <div className="flex items-center justify-center py-6">
                <Skeleton className="w-32 h-32 rounded-full" />
            </div>
            <Skeleton className="h-3 w-3/4 mx-auto mt-4" />
        </div>

        {/* 3 Stat cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            {[0, 1, 2].map((i) => (
                <div key={i} className="card p-6">
                    <div className="flex justify-between items-start mb-4">
                        <Skeleton className="w-12 h-12 rounded-2xl" />
                        <Skeleton className="w-4 h-4" />
                    </div>
                    <Skeleton className="h-9 w-16 mb-2" />
                    <Skeleton className="h-3 w-28" />
                    <Skeleton className="h-2 w-20 mt-2" />
                </div>
            ))}
        </div>

        {/* 3 Quick action cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            {[0, 1, 2].map((i) => (
                <div key={i} className="card p-6 flex items-center gap-4">
                    <Skeleton className="w-12 h-12 rounded-xl flex-shrink-0" />
                    <div className="flex-1 space-y-2">
                        <Skeleton className="h-4 w-32" />
                        <Skeleton className="h-3 w-24" />
                    </div>
                    <Skeleton className="w-4 h-4 flex-shrink-0" />
                </div>
            ))}
        </div>

        {/* AI Doctor Summary card */}
        <div className="card p-6">
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-2">
                    <Skeleton className="w-8 h-8 rounded-lg" />
                    <Skeleton className="h-5 w-40" />
                </div>
                <Skeleton className="h-4 w-28" />
            </div>
            <div className="space-y-3">
                <Skeleton className="h-3 w-full" />
                <Skeleton className="h-3 w-full" />
                <Skeleton className="h-3 w-5/6" />
                <Skeleton className="h-3 w-4/6" />
            </div>
        </div>

        {/* Health Timeline card */}
        <div className="card p-6 mt-8">
            <div className="flex items-center gap-2 mb-4">
                <Skeleton className="w-8 h-8 rounded-lg" />
                <Skeleton className="h-5 w-36" />
            </div>
            <div className="space-y-4">
                {[0, 1, 2, 3].map((i) => (
                    <div key={i} className="flex items-start gap-4">
                        <Skeleton className="w-10 h-10 rounded-full flex-shrink-0" />
                        <div className="flex-1 space-y-2">
                            <Skeleton className="h-4 w-48" />
                            <Skeleton className="h-3 w-full" />
                            <Skeleton className="h-3 w-2/3" />
                        </div>
                        <Skeleton className="h-3 w-16 flex-shrink-0" />
                    </div>
                ))}
            </div>
        </div>
    </div>
);

/**
 * Biomarkers page skeleton.
 * Matches: search bar + filter controls, summary line, then category cards with biomarker rows.
 */
const BiomarkersSkeleton = () => (
    <div>
        {/* Controls row: search bar, filter toggle, sort dropdown */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
            <div className="flex gap-2 w-full md:w-auto">
                <Skeleton className="h-10 w-full md:w-80 rounded-xl" />
                <Skeleton className="h-10 w-36 rounded-xl" />
                <Skeleton className="h-10 w-32 rounded-xl" />
            </div>
            <Skeleton className="h-4 w-40" />
        </div>

        {/* Summary line */}
        <div className="mb-6 flex items-center gap-4">
            <Skeleton className="h-4 w-28" />
            <Skeleton className="h-4 w-24" />
        </div>

        {/* Category sections */}
        <div className="space-y-4">
            {[0, 1, 2, 3].map((catIdx) => (
                <div key={catIdx} className="card overflow-hidden">
                    {/* Category header */}
                    <div className="p-4 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <Skeleton className="w-10 h-10 rounded-lg" />
                            <div className="space-y-1.5">
                                <Skeleton className="h-4 w-28" />
                                <Skeleton className="h-3 w-16" />
                            </div>
                        </div>
                        <div className="flex items-center gap-3">
                            <Skeleton className="h-5 w-14 rounded-full" />
                            <Skeleton className="w-5 h-5" />
                        </div>
                    </div>

                    {/* Biomarker rows (expanded state) */}
                    <div className="border-t border-slate-100">
                        {/* Table header (desktop only) */}
                        <div className="hidden md:grid grid-cols-12 gap-4 p-3 bg-slate-50/50">
                            <Skeleton className="col-span-4 h-3 w-20" />
                            <Skeleton className="col-span-2 h-3 w-12" />
                            <Skeleton className="col-span-2 h-3 w-16" />
                            <Skeleton className="col-span-2 h-3 w-10" />
                            <Skeleton className="col-span-1 h-3 w-8 mx-auto" />
                            <Skeleton className="col-span-1 h-3 w-10 ml-auto" />
                        </div>
                        {/* Rows */}
                        {[0, 1, 2, 3, 4].map((rowIdx) => (
                            <div key={rowIdx} className="p-3">
                                {/* Desktop row */}
                                <div className="hidden md:grid grid-cols-12 gap-4 items-center">
                                    <Skeleton className="col-span-4 h-4 w-3/4" />
                                    <Skeleton className="col-span-2 h-4 w-16" />
                                    <Skeleton className="col-span-2 h-3 w-20" />
                                    <Skeleton className="col-span-2 h-3 w-16" />
                                    <Skeleton className="col-span-1 h-4 w-6 mx-auto" />
                                    <Skeleton className="col-span-1 h-3 w-3 ml-auto rounded-full" />
                                </div>
                                {/* Mobile row */}
                                <div className="md:hidden space-y-2">
                                    <Skeleton className="h-4 w-3/5" />
                                    <div className="flex items-center gap-2">
                                        <Skeleton className="h-4 w-16" />
                                        <Skeleton className="h-3 w-10" />
                                        <Skeleton className="h-3 w-20" />
                                    </div>
                                    <Skeleton className="h-3 w-20" />
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            ))}
        </div>
    </div>
);

/**
 * Health Reports page skeleton.
 * Matches: header with title + action button, latest report card with summary and findings, specialist cards grid.
 */
const HealthReportsSkeleton = () => (
    <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
                <div className="flex items-center gap-3">
                    <Skeleton className="w-10 h-10 rounded-xl" />
                    <Skeleton className="h-7 w-48" />
                </div>
                <Skeleton className="h-4 w-64 mt-2" />
            </div>
            <Skeleton className="h-12 w-44 rounded-xl" />
        </div>

        {/* Latest report card */}
        <div className="card overflow-hidden">
            {/* Card header */}
            <div className="p-6 border-b border-slate-100">
                <div className="flex items-center justify-between">
                    <Skeleton className="h-5 w-36" />
                    <Skeleton className="h-4 w-24" />
                </div>
            </div>

            <div className="p-6">
                {/* Risk badge + biomarker count */}
                <div className="flex items-center gap-4 mb-6">
                    <Skeleton className="h-8 w-28 rounded-full" />
                    <Skeleton className="h-4 w-36" />
                </div>

                {/* Summary text */}
                <div className="space-y-2 mb-6">
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-full" />
                    <Skeleton className="h-4 w-4/5" />
                </div>

                {/* Key findings section */}
                <Skeleton className="h-3 w-24 mb-3" />
                <div className="space-y-3">
                    {[0, 1, 2].map((i) => (
                        <div key={i} className="p-4 rounded-xl border border-slate-100">
                            <div className="flex items-center gap-2 mb-2">
                                <Skeleton className="h-4 w-24" />
                                <Skeleton className="h-5 w-16 rounded-full" />
                            </div>
                            <Skeleton className="h-3 w-full" />
                            <Skeleton className="h-3 w-3/4 mt-1" />
                            <div className="flex gap-2 mt-2">
                                <Skeleton className="h-6 w-20 rounded" />
                                <Skeleton className="h-6 w-24 rounded" />
                            </div>
                        </div>
                    ))}
                </div>

                {/* Recommendations section */}
                <Skeleton className="h-3 w-32 mt-6 mb-3" />
                <div className="space-y-2">
                    {[0, 1, 2].map((i) => (
                        <div key={i} className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
                            <Skeleton className="w-6 h-6 rounded-full flex-shrink-0" />
                            <div className="flex-1 space-y-1.5">
                                <Skeleton className="h-4 w-3/4" />
                                <Skeleton className="h-3 w-full" />
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>

        {/* Specialist reports grid */}
        <div className="card overflow-hidden">
            <div className="p-6 border-b border-slate-100">
                <Skeleton className="h-5 w-44" />
                <Skeleton className="h-3 w-40 mt-2" />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-6">
                {[0, 1, 2, 3].map((i) => (
                    <div key={i} className="p-4 rounded-xl border border-slate-100">
                        <div className="flex items-start gap-4">
                            <Skeleton className="w-12 h-12 rounded-xl flex-shrink-0" />
                            <div className="flex-1 space-y-2">
                                <Skeleton className="h-4 w-36" />
                                <Skeleton className="h-3 w-full" />
                                <Skeleton className="h-3 w-2/3" />
                                <Skeleton className="h-5 w-16 rounded-full" />
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    </div>
);

/**
 * Generic list skeleton with configurable row count.
 * Good for simple list/table pages (documents, linked accounts, etc.).
 */
const ListSkeleton = ({ rows = 5 }) => (
    <div className="space-y-3">
        {Array.from({ length: rows }).map((_, i) => (
            <div key={i} className="card p-4 flex items-center gap-4">
                <Skeleton className="w-10 h-10 rounded-lg flex-shrink-0" />
                <div className="flex-1 space-y-2">
                    <Skeleton className="h-4 w-2/5" />
                    <Skeleton className="h-3 w-3/5" />
                </div>
                <Skeleton className="h-3 w-16 flex-shrink-0" />
            </div>
        ))}
    </div>
);

export { Skeleton, DashboardSkeleton, BiomarkersSkeleton, HealthReportsSkeleton, ListSkeleton };
export default Skeleton;
