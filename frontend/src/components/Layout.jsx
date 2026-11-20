 import { Link, Outlet } from 'react-router-dom'
  import { HealthIndicator } from './HealthIndicator.jsx'

  export function Layout() {
    return (
      <>
        <nav className="navbar">
          <Link to="/">Live Monitoring</Link>
          <Link to="/AlertFeed">Alert Feed</Link>
          <Link to="/History">History</Link>
          <Link to="/Stats">Statistics</Link>
          <Link to="/Config">Configuration</Link>
          <HealthIndicator />
        </nav>
        <Outlet />
      </>
    )
  }