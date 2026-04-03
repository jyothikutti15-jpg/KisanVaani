import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Mic, LayoutDashboard, History, Sprout, Bell, Wrench,
  TrendingUp, Satellite, ShoppingCart, HeadphonesIcon, Users, Menu, X, Globe
} from 'lucide-react';
import clsx from 'clsx';
import { useLanguage, LANGUAGE_OPTIONS } from '../../i18n/LanguageContext';

const allLinks = [
  { to: '/', key: 'nav.home', icon: Sprout },
  { to: '/demo', key: 'nav.voice_demo', icon: Mic },
  { to: '/features', key: 'nav.features', icon: Wrench },
  { to: '/prices', key: 'nav.prices', icon: TrendingUp },
  { to: '/satellite', key: 'nav.satellite', icon: Satellite },
  { to: '/marketplace', key: 'nav.marketplace', icon: ShoppingCart },
  { to: '/expert', key: 'nav.expert', icon: HeadphonesIcon },
  { to: '/network', key: 'nav.network', icon: Users },
  { to: '/alerts', key: 'nav.alerts', icon: Bell },
  { to: '/dashboard', key: 'nav.dashboard', icon: LayoutDashboard },
  { to: '/calls', key: 'nav.history', icon: History },
];

export default function Navbar() {
  const location = useLocation();
  const { lang, setLang, t } = useLanguage();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [langOpen, setLangOpen] = useState(false);

  const currentLang = LANGUAGE_OPTIONS.find(l => l.code === lang);

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
            {allLinks.map(({ to, key, icon: Icon }) => (
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
                {t(key)}
              </Link>
            ))}
          </div>

          {/* Language switcher + mobile toggle */}
          <div className="flex items-center gap-2">
            {/* Language dropdown */}
            <div className="relative">
              <button
                onClick={() => setLangOpen(!langOpen)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium bg-green-50 text-green-700 hover:bg-green-100 transition-colors"
              >
                <Globe className="h-4 w-4" />
                <span className="hidden sm:inline">{currentLang?.native}</span>
                <span className="sm:hidden">{lang.toUpperCase()}</span>
              </button>
              {langOpen && (
                <div className="absolute right-0 top-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-50 min-w-[160px]">
                  {LANGUAGE_OPTIONS.map((l) => (
                    <button
                      key={l.code}
                      onClick={() => { setLang(l.code); setLangOpen(false); }}
                      className={clsx(
                        'w-full text-left px-4 py-2.5 text-sm hover:bg-gray-50 flex items-center justify-between',
                        lang === l.code ? 'bg-green-50 text-green-700 font-medium' : 'text-gray-700'
                      )}
                    >
                      <span>{l.native}</span>
                      <span className="text-xs text-gray-400">{l.name}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Mobile toggle */}
            <button onClick={() => setMobileOpen(!mobileOpen)} className="lg:hidden p-2 rounded-lg hover:bg-gray-100">
              {mobileOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile nav */}
      {mobileOpen && (
        <div className="lg:hidden border-t border-gray-200 bg-white px-4 py-3 space-y-1">
          {allLinks.map(({ to, key, icon: Icon }) => (
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
              {t(key)}
            </Link>
          ))}
        </div>
      )}
    </nav>
  );
}
