  export function SeverityBadge({ severity }) {
    return <span className={`badge badge-${severity?.toLowerCase()}`}>{severity}</span>
  }