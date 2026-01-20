import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useMemo, useState, useEffect } from 'react';

export default function Trends({ results }) {
    // Unique test names
    const testNames = useMemo(() => [...new Set(results.map(r => r.test_name))].sort(), [results]);

    // State for selection
    const [selectedTest, setSelectedTest] = useState('');

    // Default selection logic
    useEffect(() => {
        if (!selectedTest && testNames.length > 0) {
            // Prefer Hemoglobina (case insensitive)
            const hemo = testNames.find(n => n.toLowerCase().includes('hemoglobina'));
            setSelectedTest(hemo || testNames[0]);
        }
    }, [testNames, selectedTest]);

    const data = useMemo(() => {
        if (!selectedTest) return [];
        return results
            .filter(r => r.test_name === selectedTest)
            .map(r => {
                // Handle "< 20", "> 50", "Negativ"
                let valStr = r.value.toString().replace(',', '.'); // Handle European decimal
                let val = parseFloat(valStr);

                // Heuristic for inequalities
                if (isNaN(val)) {
                    if (valStr.includes('<')) val = parseFloat(valStr.replace('<', ''));
                    if (valStr.includes('>')) val = parseFloat(valStr.replace('>', ''));
                }

                return {
                    date: new Date(r.date).toLocaleDateString(),
                    value: isNaN(val) ? null : val, // Null breaks the line for non-numeric results
                    originalValue: r.value,
                    provider: r.provider
                };
            })
            .sort((a, b) => new Date(a.date) - new Date(b.date)); // Sort by date
    }, [results, selectedTest]);

    if (!testNames.length) return <div className="p-4 text-gray-500">No data for trends.</div>;

    return (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold">Evolution Trend</h3>
                <select
                    className="border border-gray-200 rounded-md px-3 py-1 text-sm bg-gray-50 max-w-xs"
                    value={selectedTest}
                    onChange={(e) => setSelectedTest(e.target.value)}
                >
                    {testNames.map(name => (
                        <option key={name} value={name}>{name}</option>
                    ))}
                </select>
            </div>

            <div className="h-64 w-full" style={{ minHeight: '16rem' }}>
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={data}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis />
                        <Tooltip
                            content={({ active, payload, label }) => {
                                if (active && payload && payload.length) {
                                    return (
                                        <div className="bg-white p-2 border shadow-sm text-sm rounded">
                                            <p className="font-bold">{label}</p>
                                            <p className="text-teal-600">
                                                {selectedTest}: {payload[0].payload.originalValue}
                                            </p>
                                            <p className="text-xs text-gray-500">{payload[0].payload.provider}</p>
                                        </div>
                                    );
                                }
                                return null;
                            }}
                        />
                        <Line type="monotone" dataKey="value" stroke="#0d9488" strokeWidth={2} activeDot={{ r: 8 }} connectNulls={true} />
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
