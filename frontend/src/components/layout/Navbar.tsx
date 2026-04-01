import { Link, useLocation } from 'react-router-dom';
import { Mic, LayoutDashboard, History, Sprout, Bell, Wrench } from 'lucide-react';
import clsx from 'clsx';

const links = [
  { to: '/', label: 'Home', icon: Sprout },
  { to: '/demo', label: 'Voice Demo', icon: Mic },
  { to: '/features', label: 'Features', icon: Wrench },
  { to: '/alerts', label: 'Alerts', icon: Bell },
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/calls', label: 'History', icon: History },
];

export default function Navbar() {
  const location = useLocation();
  return (
    <nav className="bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-2">
            <Sprout className="h-8 w-8 text-primary-600" />
            <span className="text-xl font-bold text-gray-900">KisanVaani</span>
            <span className="hidden sm:inline text-xs bg-primary-100 text-primary-700 px-2 py-0.5 rounded-full font-medium">v2.0</span>
          </Link>
          <div className="flex items-center gap-1">
            {links.map(({ to, label, icon: Icon }) => (
              <Link
                key={to}
                to={to}
                className={clsx(
                  'flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
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
        </div>
      </div>
    </nav>
  );
}
