
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, ResponsiveContainer } from 'recharts';

const data = [
  { name: 'Jan', value: 4000, value2: 2400 },
  { name: 'Feb', value: 3000, value2: 1398 },
  { name: 'Mar', value: 2000, value2: 9800 },
  { name: 'Apr', value: 2780, value2: 3908 },
  { name: 'May', value: 1890, value2: 4800 },
  { name: 'Jun', value: 2390, value2: 3800 },
];

export function AnalyticsAreaChart() {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <AreaChart data={data} margin={{ top: 10, right: 20, left: 20, bottom: 25 }}>
        <defs>
          <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.8}/>
            <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.1}/>
          </linearGradient>
          <linearGradient id="colorValue2" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.8}/>
            <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0.1}/>
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
        <XAxis 
          dataKey="name" 
          stroke="rgba(255,255,255,0.6)" 
          label={{ value: 'Month', position: 'insideBottom', offset: -10, fill: '#94a3b8', fontSize: 12 }}
        />
        <YAxis 
          stroke="rgba(255,255,255,0.6)" 
          label={{ value: 'Revenue ($)', angle: -90, position: 'insideLeft', offset: 0, fill: '#94a3b8', fontSize: 12, style: { textAnchor: 'middle' } }}
        />
        <Area
          type="monotone"
          dataKey="value2"
          stackId="1"
          stroke="#8B5CF6"
          fill="url(#colorValue2)"
          strokeWidth={2}
        />
        <Area
          type="monotone"
          dataKey="value"
          stackId="1"
          stroke="#3B82F6"
          fill="url(#colorValue)"
          strokeWidth={2}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
