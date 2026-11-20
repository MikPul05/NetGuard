  import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

  // data: [{ key, name, count }]; colors: optional { key: '#hex' }
  export function CountBarChart({ data, colors, height = 250 }) {
    return (
      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={data} layout="vertical" margin={{ left: 10, right: 20 }}>
          <CartesianGrid strokeDasharray="3 3" horizontal={false} />
          <XAxis type="number" allowDecimals={false} />
          <YAxis type="category" dataKey="name" width={190} />
          <Tooltip />
          <Bar dataKey="count" name="Count" fill="#2563eb">
            {colors && data.map((d) => <Cell key={d.key} fill={colors[d.key] ?? '#2563eb'} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    )
  }