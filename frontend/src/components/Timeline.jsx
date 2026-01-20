export default function Timeline({ results }) {
    // Group by Date
    const grouped = results.reduce((acc, curr) => {
        const d = new Date(curr.date).toLocaleDateString();
        if (!acc[d]) acc[d] = [];
        acc[d].push(curr);
        return acc;
    }, {});

    const sortedDates = Object.keys(grouped).sort((a, b) => new Date(b) - new Date(a));

    return (
        <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <h3 className="text-lg font-semibold mb-4">Timeline History</h3>
            <div className="space-y-6">
                {sortedDates.map(date => (
                    <div key={date} className="relative pl-4 border-l-2 border-gray-200">
                        <div className="absolute -left-1.5 top-0 w-3 h-3 bg-teal-500 rounded-full"></div>
                        <div className="mb-2 text-sm text-gray-500 font-medium">{date}</div>
                        <div className="space-y-2">
                            {grouped[date].map(r => (
                                <div key={r.id} className="flex justify-between items-center text-sm">
                                    <span className="font-medium text-gray-700">{r.test_name}</span>
                                    <span className={`px-2 py-0.5 rounded ${r.flags === 'HIGH' ? 'bg-red-100 text-red-700' :
                                            r.flags === 'LOW' ? 'bg-yellow-100 text-yellow-700' : 'text-gray-600'
                                        }`}>
                                        {r.value} {r.unit}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
