import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceArea } from 'recharts';
import { useMemo, useState, useEffect } from 'react';
import axios from 'axios';
import { Info } from 'lucide-react';

export default function Trends({ results, selectedTest, setSelectedTest, selectedCategory, setSelectedCategory }) {
    const [biomarkerInfo, setBiomarkerInfo] = useState(null);

    // 1. Group Test Names by Category
    const { categories, testsByCategory, testToCategory } = useMemo(() => {
        if (!results) return { categories: [], testsByCategory: {}, testToCategory: {} };
        const cats = new Set();
        const mapping = {};
        const revMapping = {};

        results.forEach(r => {
            const cat = r.category || 'General';
            cats.add(cat);
            if (!mapping[cat]) mapping[cat] = new Set();
            mapping[cat].add(r.test_name);
            revMapping[r.test_name] = cat;
        });

        return {
            categories: [...cats].sort(),
            testsByCategory: mapping,
            testToCategory: revMapping
        };
    }, [results]);

    // 2. Fetch Biomarker Info
    useEffect(() => {
        if (!selectedTest) return;

        async function fetchInfo() {
            try {
                const res = await axios.get(`http://localhost:8000/biomarker-info?name=${encodeURIComponent(selectedTest)}`);
                setBiomarkerInfo(res.data);
            } catch (err) {
                console.error("Failed to fetch biomarker info", err);
                setBiomarkerInfo(null);
            }
        }
        fetchInfo();
    }, [selectedTest]);

    // 3. Effect: Auto-select category/test if empty
    useEffect(() => {
        if (categories.length > 0 && !selectedCategory) {
            setSelectedCategory(categories[0]);
        }
    }, [categories]);

    // 4. Effect: Reverse Sync (Test -> Category)
    useEffect(() => {
        if (selectedTest && testToCategory[selectedTest]) {
            const neededCat = testToCategory[selectedTest];
            if (selectedCategory !== neededCat) {
                setSelectedCategory(neededCat);
            }
        }
    }, [selectedTest, testToCategory]);

    // 5. Effect: Forward Sync (Category -> Test)
    useEffect(() => {
        if (selectedCategory && testsByCategory[selectedCategory]) {
            const tests = [...testsByCategory[selectedCategory]].sort();
            if (!tests.includes(selectedTest)) {
                setSelectedTest(tests[0]);
            }
        }
    }, [selectedCategory, testsByCategory]);

    // 6. Data for Chart
    const data = useMemo(() => {
        if (!selectedTest || !results) return [];
        return results
            .filter(r => r.test_name === selectedTest)
            .map(r => {
                let valStr = String(r.value).replace(',', '.');
                valStr = valStr.replace('=', '').trim();
                let val = parseFloat(valStr);
                if (isNaN(val)) {
                    if (valStr.includes('<')) val = parseFloat(valStr.replace('<', '').trim());
                    else if (valStr.includes('>')) val = parseFloat(valStr.replace('>', '').trim());
                }

                return {
                    date: r.date,
                    labelDate: new Date(r.date).toLocaleDateString(),
                    value: isNaN(val) ? null : val,
                    originalValue: r.value,
                    unit: r.unit,
                    provider: r.provider,
                    flags: r.flags,
                    reference_range: r.reference_range
                };
            })
            .sort((a, b) => new Date(a.date) - new Date(b.date));
    }, [results, selectedTest]);

    const availableTests = useMemo(() => {
        if (!selectedCategory || !testsByCategory[selectedCategory]) return [];
        return [...testsByCategory[selectedCategory]].sort();
    }, [selectedCategory, testsByCategory]);

    // Helper for Custom Dot
    const CustomDot = (props) => {
        const { cx, cy, payload } = props;
        if (!cx || !cy) return null;

        // Use the flag from the specific test result (AI Parsed)
        const isAbnormal = payload.flags === 'HIGH' || payload.flags === 'LOW' || payload.flags === 'POS';

        return (
            <circle
                cx={cx}
                cy={cy}
                r={isAbnormal ? 6 : 4}
                stroke={isAbnormal ? "#ef4444" : "#0d9488"}
                strokeWidth={2}
                fill={isAbnormal ? "#fee2e2" : "white"}
            />
        );
    };

    if (!results || results.length === 0) {
        return (
            <div className="bg-white p-8 rounded-xl border border-gray-100 text-center text-gray-500">
                No trend data available yet.
            </div>
        );
    }

    // Determine Y-Axis Domain
    let yDomain = ['auto', 'auto'];
    if (biomarkerInfo && biomarkerInfo.has_info && data.length > 0) {
        const values = data.map(d => d.value).filter(v => v !== null);
        const minVal = Math.min(...values, biomarkerInfo.min_safe);
        const maxVal = Math.max(...values, biomarkerInfo.max_safe);
        // Add some padding
        yDomain = [Math.floor(minVal * 0.9), Math.ceil(maxVal * 1.1)];
    }

    return (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100 h-full flex flex-col">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
                <div>
                    <h3 className="text-lg font-bold text-slate-900">Health Evolution</h3>
                    <p className="text-sm text-gray-500">Track your biomarkers over time</p>
                </div>
                <div className="flex gap-2">
                    <select
                        className="border border-gray-200 rounded-lg px-4 py-2 text-sm bg-gray-50 focus:ring-2 focus:ring-teal-500 outline-none w-40"
                        value={selectedCategory}
                        onChange={(e) => setSelectedCategory(e.target.value)}
                    >
                        {categories.map(cat => (
                            <option key={cat} value={cat}>{cat}</option>
                        ))}
                    </select>
                    <select
                        className="border border-gray-200 rounded-lg px-4 py-2 text-sm bg-gray-50 focus:ring-2 focus:ring-teal-500 outline-none w-48"
                        value={selectedTest}
                        onChange={(e) => setSelectedTest(e.target.value)}
                    >
                        {availableTests.map(name => (
                            <option key={name} value={name}>{name}</option>
                        ))}
                    </select>
                </div>
            </div>

            <div className="flex-1 w-full relative" style={{ minHeight: '300px' }}>
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                        <XAxis
                            dataKey="labelDate"
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: '#64748B', fontSize: 12 }}
                            dy={10}
                        />
                        <YAxis
                            axisLine={false}
                            tickLine={false}
                            tick={{ fill: '#64748B', fontSize: 12 }}
                            width={30}
                            domain={yDomain}
                        />
                        <Tooltip
                            content={({ active, payload, label }) => {
                                if (active && payload && payload.length) {
                                    const data = payload[0].payload;
                                    const isAbnormal = ['HIGH', 'LOW', 'POS'].includes(data.flags);
                                    return (
                                        <div className="bg-white p-3 border border-gray-100 shadow-lg rounded-xl text-sm">
                                            <div className="font-bold text-slate-700 mb-1">{data.labelDate}</div>
                                            <div className="flex items-baseline gap-2">
                                                <span className={`font-mono font-bold ${isAbnormal ? "text-red-500" : "text-slate-700"}`}>
                                                    {data.value} {data.unit}
                                                </span>
                                                <span className="text-slate-400 text-xs">Result</span>
                                            </div>
                                            {data.reference_range && (
                                                <div className="text-xs text-slate-400 mt-1">
                                                    Ref: {data.reference_range}
                                                </div>
                                            )}
                                        </div>
                                    );
                                }
                                return null;
                            }}
                            cursor={{ stroke: '#0d9488', strokeWidth: 1, strokeDasharray: '4 4' }}
                        />

                        {/* Reference Areas for Normal Ranges */}
                        {biomarkerInfo && biomarkerInfo.has_info && (
                            <>
                                <ReferenceArea
                                    y1={biomarkerInfo.min_safe}
                                    y2={biomarkerInfo.max_safe}
                                    fill="#22c55e"
                                    fillOpacity={0.1}
                                    label={{ value: 'Normal Range', position: 'insideTopRight', fill: '#16a34a', fontSize: 10 }}
                                />
                                <ReferenceArea
                                    y1={yDomain[0]}
                                    y2={biomarkerInfo.min_safe}
                                    fill="#ef4444"
                                    fillOpacity={0.05}
                                />
                                <ReferenceArea
                                    y1={biomarkerInfo.max_safe}
                                    y2={yDomain[1]}
                                    fill="#ef4444"
                                    fillOpacity={0.05}
                                />
                            </>
                        )}

                        <Line
                            type="monotone"
                            dataKey="value"
                            stroke="#0d9488"
                            strokeWidth={3}
                            dot={<CustomDot />}
                            activeDot={{ r: 7, strokeWidth: 0, fill: '#0d9488' }}
                            connectNulls={true}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>

            {/* Description Box */}
            {biomarkerInfo && biomarkerInfo.has_info && (
                <div className="mt-6 bg-slate-50 p-4 rounded-lg border border-slate-100 animate-in fade-in slide-in-from-top-4">
                    <div className="flex items-start gap-3">
                        <div className="p-2 bg-white rounded-lg shadow-sm text-teal-600">
                            <Info size={20} />
                        </div>
                        <div>
                            <h4 className="font-semibold text-slate-900">{biomarkerInfo.display_name}</h4>
                            <p className="text-sm text-slate-600 mt-1 leading-relaxed">
                                {biomarkerInfo.description}
                            </p>
                            <div className="mt-2 flex items-center gap-4 text-xs font-mono text-slate-500">
                                <span className="px-2 py-1 bg-green-100 text-green-700 rounded">
                                    Normal: {biomarkerInfo.min_safe} - {biomarkerInfo.max_safe} {biomarkerInfo.unit}
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
