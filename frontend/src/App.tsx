import { Routes, Route } from 'react-router-dom';
import Navbar from './components/layout/Navbar';
import LandingPage from './pages/LandingPage';
import VoiceDemo from './pages/VoiceDemo';
import Dashboard from './pages/Dashboard';
import CallHistory from './pages/CallHistory';
import AlertsPage from './pages/AlertsPage';
import FeaturesPage from './pages/FeaturesPage';

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/demo" element={<VoiceDemo />} />
        <Route path="/features" element={<FeaturesPage />} />
        <Route path="/alerts" element={<AlertsPage />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/calls" element={<CallHistory />} />
      </Routes>
    </div>
  );
}
