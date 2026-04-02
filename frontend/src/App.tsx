import { Routes, Route } from 'react-router-dom';
import Navbar from './components/layout/Navbar';
import ErrorBoundary from './components/ErrorBoundary';
import LandingPage from './pages/LandingPage';
import VoiceDemo from './pages/VoiceDemo';
import Dashboard from './pages/Dashboard';
import CallHistory from './pages/CallHistory';
import AlertsPage from './pages/AlertsPage';
import FeaturesPage from './pages/FeaturesPage';
import PricePredictionPage from './pages/PricePredictionPage';
import SatellitePage from './pages/SatellitePage';
import MarketplacePage from './pages/MarketplacePage';
import ExpertCallbackPage from './pages/ExpertCallbackPage';
import FarmerNetworkPage from './pages/FarmerNetworkPage';

export default function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <ErrorBoundary>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/demo" element={<VoiceDemo />} />
          <Route path="/features" element={<FeaturesPage />} />
          <Route path="/prices" element={<PricePredictionPage />} />
          <Route path="/satellite" element={<SatellitePage />} />
          <Route path="/marketplace" element={<MarketplacePage />} />
          <Route path="/expert" element={<ExpertCallbackPage />} />
          <Route path="/network" element={<FarmerNetworkPage />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/calls" element={<CallHistory />} />
        </Routes>
      </ErrorBoundary>
    </div>
  );
}
