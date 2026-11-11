 //import { useEffect, useState } from 'react'
 import { Layout } from './components/Layout'
  //import api from './api/api.js'
  import { HashRouter as Router, Routes, Route } from 'react-router-dom'
    import { AlertDet } from './pages/AlertDetails'
    import { AlertFeed } from './pages/AlertFeed'
        import { Config } from './pages/Config'
            import { Hist } from './pages/History'
                import { LiveMonit } from './pages/LiveMonitoring'
                    import { Stats } from './pages/Stats'

  function App() {
    return(
        <Router>
            <Routes>
                 <Route element={<Layout />}>
                    <Route path="/" element={<LiveMonit />} />
                    <Route path="/AlertFeed" element={<AlertFeed />} />
                    <Route path="/AlertDetails/:id" element={<AlertDet />} />
                    <Route path="/History" element={<Hist />} />
                    <Route path="/Stats" element={<Stats />} />
                    <Route path="/Config" element={<Config />} />
                </Route>
            </Routes>
        </Router>
        )
  }

  export default App