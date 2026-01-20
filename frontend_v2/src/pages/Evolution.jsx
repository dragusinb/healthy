import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import api from '../api/client';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceArea } from 'recharts';
import { ArrowLeft, Activity, Calendar } from 'lucide-react';
import { cn } from '../lib/utils';

const Evolution = () => {
    const { name } = useParams(); // Biomarker name from URL
    const navigate = useNavigate();
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (name) {
            fetchEvolution();
        }
    }, [name]);

    const fetchEvolution = async () => {
        setLoading(true);
        try {
            // Decode name if needed, though react router handles it
            const res = await api.get(`/dashboard/evolution/${encodeURIComponent(name)}`);
            setData(res.data);
        } catch (e) {
            console.error("Failed to fetch evolution data", e);
        } finally {
            setLoading(false);
        }
    };

    if (loading) return <div className="p-8 text-center text-gray-500">Loading evolution data...</div>;

    if (data.length === 0) {
        return (
            <div className="max-w-4xl mx-auto p-6 text-center">
                <button onClick={() => navigate(-1)} className="mb-4 text-blue-600 hover:underline flex items-center justify-center gap-2">
                    <ArrowLeft size={16} /> Back
                </button>
                <h2 className="text-2xl font-bold text-gray-800 mb-2">{name}</h2>
                <p className="text-gray-500">No history found for this biomarker.</p>
            </div>
        );
    }

    // Calculate min/max for domain or references if available
    // Assuming first point has ref range for visualization or we parse it.
    // const refRange = data[0]?.ref_range; 

    return (
        <div className="max-w-6xl mx-auto p-6">
            <button
                onClick={() => navigate(-1)}
                className="mb-6 flex items-center gap-2 text-gray-500 hover:text-gray-800 transition-colors bg-white px-3 py-1.5 rounded-lg border border-gray-200 shadow-sm"
            >
                <ArrowLeft size={16} /> Back
            </button>

            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
                <div>
                    <h2 className="text-3xl font-bold text-gray-900 tracking-tight flex items-center gap-3">
                        <div className="p-2 bg-blue-100 text-blue-600 rounded-xl">
                            <Activity size={24} />
                        </div>
                        {name}
                    </h2>
                    <p className="text-gray-500 mt-2 ml-1">Evolution history of your results over time.</p>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                    <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Latest Value</p>
                    <p className={cn("text-4xl font-bold mt-2", data[data.length - 1]?.flags !== 'NORMAL' ? "text-rose-600" : "text-gray-900")}>
                        {data[data.length - 1]?.value} <span className="text-lg font-normal text-gray-400">{data[data.length - 1]?.unit}</span>
                    </p>
                    <p className="text-sm text-gray-400 mt-1">
                        {new Date(data[data.length - 1]?.date).toLocaleDateString()}
                    </p>
                </div>

                <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                    <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Reference Range</p>
                    <p className="text-2xl font-semibold text-gray-800 mt-2">
                        {data[data.length - 1]?.ref_range || 'N/A'}
                    </p>
                    <p className="text-sm text-gray-400 mt-2">Standard medical range</p>
                </div>

                <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                    <p className="text-sm font-medium text-gray-500 uppercase tracking-wide">Total Tests</p>
                    <p className="text-4xl font-bold text-blue-600 mt-2">
                        {data.length}
                    </p>
                    <p className="text-sm text-gray-400 mt-1">Recorded measurements</p>
                </div>
            </div>

            <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-200">
                <h3 className="text-lg font-semibold text-gray-800 mb-6 flex items-center gap-2">
                    <Activity className="text-blue-500" size={20} />
                    Evolution Graph
                </h3>
                <div className="h-80 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f0f0f0" />
                            <XAxis
                                dataKey="date"
                                tickMargin={10}
                                axisLine={false}
                                tickLine={false}
                                stroke="#9ca3af"
                                fontSize={12}
                            />
                            <YAxis
                                axisLine={false}
                                tickLine={false}
                                stroke="#9ca3af"
                                fontSize={12}
                            />
                            <Tooltip
                                contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                            />
                            <Line
                                type="monotone"
                                dataKey="value"
                                stroke="#2563eb"
                                strokeWidth={3}
                                dot={{ r: 4, fill: "#2563eb", strokeWidth: 2, stroke: "#fff" }}
                                activeDot={{ r: 6, fill: "#2563eb" }}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    );
};

export default Evolution;
