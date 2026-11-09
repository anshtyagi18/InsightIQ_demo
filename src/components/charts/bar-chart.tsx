
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Tooltip } from 'recharts';

const data = [
  { name: 'Jan', revenue: 4000, profit: 2400 },
  { name: 'Feb', revenue: 3000, profit: 1398 },
  { name: 'Mar', revenue: 2000, profit: 9800 },
  { name: 'Apr', revenue: 2780, profit: 3908 },
  { name: 'May', revenue: 1890, profit: 4800 },
  { name: 'Jun', revenue: 2390, profit: 3800 },
];

export function AnalyticsBarChart() {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 10, right: 20, left: 20, bottom: 25 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
        <XAxis 
          dataKey="name" 
          stroke="rgba(255,255,255,0.6)" 
          label={{ value: 'Month', position: 'insideBottom', offset: -10, fill: '#94a3b8', fontSize: 12 }}
        />
        <YAxis 
          stroke="rgba(255,255,255,0.6)" 
          label={{ value: 'Amount ($)', angle: -90, position: 'insideLeft', offset: 0, fill: '#94a3b8', fontSize: 12, style: { textAnchor: 'middle' } }}
        />
        <Tooltip 
          contentStyle={{
            backgroundColor: 'rgba(255, 255, 255, 0.95)',
            border: '1px solid rgba(0, 0, 0, 0.1)',
            borderRadius: '8px',
            color: '#1f2937',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
            fontSize: '14px',
            fontWeight: '500',
            backdropFilter: 'blur(10px)'
          }}
        />
        <Bar dataKey="revenue" fill="#3B82F6" radius={[4, 4, 0, 0]} />
        <Bar dataKey="profit" fill="#8B5CF6" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
