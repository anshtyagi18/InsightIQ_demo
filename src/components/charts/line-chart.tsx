
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Tooltip } from 'recharts';

const data = [
  { name: 'Mon', users: 2400, sessions: 1400 },
  { name: 'Tue', users: 1398, sessions: 2210 },
  { name: 'Wed', users: 9800, sessions: 2290 },
  { name: 'Thu', users: 3908, sessions: 2000 },
  { name: 'Fri', users: 4800, sessions: 2181 },
  { name: 'Sat', users: 3800, sessions: 2500 },
  { name: 'Sun', users: 4300, sessions: 2100 },
];

export function AnalyticsLineChart() {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data} margin={{ top: 10, right: 20, left: 20, bottom: 25 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" />
        <XAxis 
          dataKey="name" 
          stroke="rgba(255,255,255,0.6)" 
          label={{ value: 'Day', position: 'insideBottom', offset: -10, fill: '#94a3b8', fontSize: 12 }}
        />
        <YAxis 
          stroke="rgba(255,255,255,0.6)" 
          label={{ value: 'Metrics', angle: -90, position: 'insideLeft', offset: 0, fill: '#94a3b8', fontSize: 12, style: { textAnchor: 'middle' } }}
        />
        <Tooltip 
          contentStyle={{
            backgroundColor: 'rgba(0,0,0,0.8)',
            border: '1px solid rgba(255,255,255,0.2)',
            borderRadius: '8px',
            backdropFilter: 'blur(10px)'
          }}
        />
        <Line
          type="monotone"
          dataKey="users"
          stroke="#3B82F6"
          strokeWidth={3}
          dot={{ fill: '#3B82F6', strokeWidth: 2, r: 4 }}
          activeDot={{ r: 6, stroke: '#3B82F6', strokeWidth: 2 }}
        />
        <Line
          type="monotone"
          dataKey="sessions"
          stroke="#8B5CF6"
          strokeWidth={3}
          dot={{ fill: '#8B5CF6', strokeWidth: 2, r: 4 }}
          activeDot={{ r: 6, stroke: '#8B5CF6', strokeWidth: 2 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
