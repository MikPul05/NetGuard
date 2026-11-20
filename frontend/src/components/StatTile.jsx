  export function StatTile({ label, value, color }) {
    return (
      <div className="tile" style={color ? { borderTopColor: color } : undefined}>
        <div className="tile-value">{value}</div>
        <div className="tile-label">{label}</div>
      </div>
    )
  }