  import { Link, Outlet } from 'react-router-dom'

  export function Layout() {
    return (
      <>
        <nav>
          <Link to="/">Live Monitoring</Link>
          <Link to="/AlertFeed">Alert Feed</Link>
          <Link to="/History">History</Link>
          <Link to="/Stats">Statistics</Link>
          <Link to="/Config">Configuration</Link>
        </nav>
        <Outlet />
      </>
    )
  }
