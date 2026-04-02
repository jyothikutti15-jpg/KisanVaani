import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Mic, LayoutDashboard, History, Sprout, Bell, Wrench,
  TrendingUp, Satellite, ShoppingCart, HeadphonesIcon, Users, Menu, X
} from 'lucide-react';
import clsx from 'clsx';

const mainLinks = [
  { to: '/', label: 'Home', icon: Sprout },
  { to: '/demo', label: 'Voice Demo', icon: Mic },
  { to: '/features', label: 'Features', icon: Wrench },
];

const advancedLinks = [
  { to: '/prices', label: 'Prices', icon: TrendingUp },
  { to: '/satellite', label: 'Satellite', icon: Satellite },
  { to: '/marketplace', label: 'Market', icon: ShoppingCart },
  { to: '/expert', label: 'Expert', icon: HeadphonesIcon },
  { to: '/network', label: 'Network', icon: Users },
];

const systemLinks = [
  { to: '/alerts', label: 'Alerts', icon: Bell },
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/calls', label: 'History', icon: History },
];

const allLinks = [...mainLinks, ...advancedLinks, ...systemLinks];

export default function Navbar() {
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <nav className="bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-2 shrink-0">
            <Sprout className="h-8 w-8 text-primary-600" />
            <span className="text-xl font-bold text-gray-900">KisanVaani</span>
            <span className="hidden sm:inline text-xs bg-primary-100 text-primary-700 px-2 py-0.5 rounded-full font-medium">v2.1</span>
          </Link>

          {/* Desktop nav */}
          <div className="hidden lg:flex items-center gap-0.5">
            {allLinks.map(({ to, label, icon: Icon }) => (
              <Link
                key={to}
                to={to}
                className={clsx(
                  'flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-medium transition-colors',
                  location.pathname === to
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-gray-600 hover:bg-gray-100'
                )}
              >
                <Icon className="h-3.5 w-3.5" />
                {label}
              </Link>
            ))}
          </div>

          {/* Mobile toggle */}
          <button onClick={() => setMobileOpen(!mobileOpen)} className="lg:hidden p-2 rounded-lg hover:bg-gray-100">
            {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </div>

      {/* Mobile nav */}
      {mobileOpen && (
        <div className="lg:hidden border-t border-gray-200 bg-white px-4 py-3 space-y-1">
          {allLinks.map(({ to, label, icon: Icon }) => (
            <Link
              key={to}
              to={to}
              onClick={() => setMobileOpen(false)}
              className={clsx(
                'flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                location.pathname === to
                  ? 'bg-primary-50 text-primary-700'
                  : 'text-gray-600 hover:bg-gray-100'
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          ))}
        </div>
      )}
    </nav>
  );
}
