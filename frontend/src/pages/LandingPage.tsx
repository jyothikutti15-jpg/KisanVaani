import { Link } from 'react-router-dom';
import { Mic, Globe, Phone, Brain, Sprout, ArrowRight, Users, Wheat } from 'lucide-react';

const LANGUAGES = [
  { code: 'hi', name: 'Hindi', native: 'हिन्दी', flag: '🇮🇳' },
  { code: 'te', name: 'Telugu', native: 'తెలుగు', flag: '🇮🇳' },
  { code: 'ta', name: 'Tamil', native: 'தமிழ்', flag: '🇮🇳' },
  { code: 'sw', name: 'Swahili', native: 'Kiswahili', flag: '🇰🇪' },
  { code: 'en', name: 'English', native: 'English', flag: '🌍' },
];

export default function LandingPage() {
  return (
    <div>
      {/* Hero */}
      <section className="bg-gradient-to-br from-primary-700 via-primary-600 to-primary-800 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="max-w-3xl">
            <h1 className="text-5xl font-extrabold leading-tight">
              Every Farmer Deserves an AI Advisor
            </h1>
            <p className="mt-6 text-xl text-primary-100 leading-relaxed">
              KisanVaani is a voice-first AI that helps smallholder farmers get expert agricultural
              advice — in their own language, through a simple phone call. No app. No internet. No smartphone needed.
            </p>
            <div className="mt-8 flex items-center gap-4">
              <Link
                to="/demo"
                className="inline-flex items-center gap-2 px-8 py-3.5 bg-white text-primary-700 rounded-xl font-bold text-lg hover:bg-primary-50 transition-colors"
              >
                <Mic className="h-5 w-5" />
                Try the Demo
                <ArrowRight className="h-5 w-5" />
              </Link>
            </div>
            <div className="mt-12 grid grid-cols-3 gap-8">
              <div>
                <p className="text-3xl font-bold">1.3B+</p>
                <p className="text-primary-200 text-sm">Smallholder farmers worldwide</p>
              </div>
              <div>
                <p className="text-3xl font-bold">100+</p>
                <p className="text-primary-200 text-sm">Languages supported</p>
              </div>
              <div>
                <p className="text-3xl font-bold">$0</p>
                <p className="text-primary-200 text-sm">Cost to the farmer</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">How It Works</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary-100 mb-4">
              <Phone className="h-8 w-8 text-primary-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">1. Dial the Number</h3>
            <p className="text-gray-600">
              Farmer calls a toll-free number from any phone — even a basic feature phone with no internet.
            </p>
          </div>
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-earth-100 mb-4">
              <Mic className="h-8 w-8 text-earth-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">2. Ask in Your Language</h3>
            <p className="text-gray-600">
              Speak your farming question in Hindi, Telugu, Tamil, Swahili, or English. The AI understands.
            </p>
          </div>
          <div className="text-center">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-green-100 mb-4">
              <Brain className="h-8 w-8 text-green-600" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">3. Get Expert Advice</h3>
            <p className="text-gray-600">
              AI analyzes your question with farming knowledge and responds with specific, actionable advice — spoken back to you.
            </p>
          </div>
        </div>
      </section>

      {/* What it can help with */}
      <section className="bg-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">What Farmers Can Ask</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              { icon: '🐛', title: 'Pest & Disease ID', desc: '"My tomato leaves have yellow spots — what is it and how to treat it?"' },
              { icon: '🌾', title: 'Crop Calendar', desc: '"When should I plant wheat this season? Which variety is best for my region?"' },
              { icon: '🌦️', title: 'Weather Advice', desc: '"Rain is expected tomorrow — should I spray pesticide today?"' },
              { icon: '💰', title: 'Market Prices', desc: '"What is the current mandi price for cotton? Should I sell now or wait?"' },
              { icon: '🏛️', title: 'Government Schemes', desc: '"Am I eligible for PM-KISAN? How do I apply for crop insurance?"' },
              { icon: '🌱', title: 'Soil & Fertilizer', desc: '"My soil test shows low nitrogen — which fertilizer should I use and how much?"' },
            ].map((item, i) => (
              <div key={i} className="rounded-xl border border-gray-200 p-5">
                <span className="text-3xl">{item.icon}</span>
                <h3 className="font-semibold text-gray-900 mt-3 mb-1">{item.title}</h3>
                <p className="text-sm text-gray-500 italic">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Languages */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <h2 className="text-3xl font-bold text-center text-gray-900 mb-8">Speaks Their Language</h2>
        <div className="flex flex-wrap justify-center gap-4">
          {LANGUAGES.map((lang) => (
            <div key={lang.code} className="flex items-center gap-3 px-6 py-3 bg-white rounded-xl border border-gray-200 shadow-sm">
              <span className="text-2xl">{lang.flag}</span>
              <div>
                <p className="font-semibold text-gray-900">{lang.name}</p>
                <p className="text-sm text-gray-500">{lang.native}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Impact */}
      <section className="bg-primary-700 text-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold mb-6">The Problem We're Solving</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            <div>
              <Users className="h-10 w-10 mx-auto mb-3 text-primary-200" />
              <p className="text-4xl font-bold">1.3B</p>
              <p className="text-primary-200 mt-1">Farmers with no AI tools</p>
            </div>
            <div>
              <Wheat className="h-10 w-10 mx-auto mb-3 text-primary-200" />
              <p className="text-4xl font-bold">40%</p>
              <p className="text-primary-200 mt-1">Post-harvest loss in developing nations</p>
            </div>
            <div>
              <Globe className="h-10 w-10 mx-auto mb-3 text-primary-200" />
              <p className="text-4xl font-bold">0</p>
              <p className="text-primary-200 mt-1">Voice-AI farm advisors in local languages</p>
            </div>
          </div>
          <Link
            to="/demo"
            className="inline-flex items-center gap-2 mt-10 px-8 py-3 bg-white text-primary-700 rounded-xl font-bold text-lg hover:bg-primary-50 transition-colors"
          >
            <Mic className="h-5 w-5" />
            Try It Now
          </Link>
        </div>
      </section>
    </div>
  );
}
