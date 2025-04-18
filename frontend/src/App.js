import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import AnalysisPage from './pages/AnalysisPage';
import HistoricalPage from './pages/HistoricalPage';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/analyse" element={<AnalysisPage />} />
        <Route path="/historical/:stock" element={<HistoricalPage />} />
      </Routes>
    </Router>
  );
}
export default App;