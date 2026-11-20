import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

  const fmtTime = (ms) => new Date(ms).toLocaleTimeString()

  export function TrafficChart({ points }) {
    const data = points.map((p) => ({
      time: p.timestampUnixUs / 1000,           // µs -> ms for Date
      flows: p.flowCount,
      packets: Number(p.packetCount),
    }))

    return (
      <ResponsiveContainer width="100%" height={260}>
        <LineChart data={data} margin={{ right: 20 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" tickFormatter={fmtTime} minTickGap={40} />
          <YAxis allowDecimals={false} />
          <Tooltip labelFormatter={(ms) => new Date(ms).toLocaleString()} />
          <Legend />
          {/* animation off, otherwise the lines redraw on every poll */}
          <Line type="monotone" dataKey="flows" name="Flows" stroke="#2563eb" dot={false} isAnimationActive={false} />
          <Line type="monotone" dataKey="packets" name="Packets" stroke="#16a34a" dot={false} isAnimationActive={false} />
        </LineChart>
      </ResponsiveContainer>
    )
  }