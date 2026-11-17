import { Activity, BarChart3, Newspaper, TrendingUp, Heart, Github, Linkedin, Search, Moon, Sun, Sparkles, Gauge, Cpu } from 'lucide-react';
import { useAnalysis } from './hooks/useAnalysis';
import { useTheme } from './hooks/useTheme';
import SearchBar from './components/SearchBar';
import { Sidebar, MobileStockPicker } from './components/Sidebar';
import LoadingSkeleton from './components/LoadingSkeleton';
import Dashboard from './components/Dashboard';
import { FOCUS_RING } from './constants/ui';

const APP_VERSION = '2.0.0';

export default function App() {
  const { ticker, setTicker, loading, phase, data, error, analyse, recentSearches } = useAnalysis();
  const { isDark, toggle } = useTheme();

  const handleStockSelect = (symbol) => {
    setTicker(symbol);
    analyse(symbol);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-950 transition-colors">

      {/* Navbar */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-gray-900 dark:bg-gray-700 rounded-lg">
                <Activity className="w-4 h-4 text-white" />
              </div>
              <div>
                <h1 className="text-sm font-bold text-gray-900 dark:text-gray-100 leading-tight">Market Mood Detector</h1>
                <p className="text-xs text-gray-500 dark:text-gray-400">Yahoo Finance + FinBERT</p>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <div className="hidden sm:flex items-center gap-5">
                {[
                  [Newspaper, 'Yahoo Finance'],
                  [BarChart3, 'Live analysis'],
                  [TrendingUp, 'Historical mood'],
                ].map((entry) => {
                  const [Icon, label] = entry;
                  return (
                    <div key={label} className="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400 font-medium">
                      <Icon className="w-3.5 h-3.5" />
                      <span>{label}</span>
                    </div>
                  );
                })}
              </div>

              <button
                onClick={toggle}
                aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
                className={`p-2 rounded-lg border border-gray-200 dark:border-gray-700 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors ${FOCUS_RING}`}
              >
                {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Body */}
      <div className="pt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8">
          <div className="flex gap-8">
            <main className="flex-1 min-w-0">
              <header className="mb-8">
                <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-gray-100 mb-2 tracking-tight">
                  Market Mood Analysis
                </h2>
                <p className="text-gray-500 dark:text-gray-400 text-sm sm:text-base max-w-2xl">
                  Analyse ticker-specific Yahoo Finance news with FinBERT, deduplication, recency weighting,
                  confidence scoring, trend detection, and historical market-mood tracking.
                </p>
              </header>

              <SearchBar
                ticker={ticker}
                setTicker={setTicker}
                loading={loading}
                onSubmit={(t) => analyse(t)}
                recentSearches={recentSearches}
              />

              <MobileStockPicker activeTicker={ticker} loading={loading} onSelect={handleStockSelect} />

              {error && !loading && (
                <div className="mb-6 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg" role="alert">
                  <p className="text-sm text-red-700 dark:text-red-400 font-medium">{error}</p>
                </div>
              )}

              {loading && <LoadingSkeleton phase={phase} />}

              {data && !loading && <Dashboard data={data} />}

              {!data && !loading && !error && (
                <div className="text-center py-16 sm:py-20 animate-fadeIn">
                  <div className="inline-flex items-center justify-center w-16 h-16 bg-gray-100 dark:bg-gray-800 rounded-2xl mb-5">
                    <Search className="w-7 h-7 text-gray-400 dark:text-gray-500" />
                  </div>
                  <h3 className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-2">Ready to Analyse</h3>
                  <p className="text-gray-400 dark:text-gray-500 text-sm max-w-md mx-auto mb-8">
                    Enter a ticker above or pick a stock from the panel — we'll pull current Yahoo Finance news,
                    score it with FinBERT, and return a confidence-backed market-mood verdict.
                  </p>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 max-w-2xl mx-auto text-left">
                    {[
                      [Newspaper, 'Yahoo Finance News', 'Ticker-specific RSS coverage with duplicate removal and source-health reporting.'],
                      [Cpu, 'FinBERT Scoring', 'Financial-language sentiment scoring with recent articles weighted more heavily.'],
                      [Gauge, 'Confidence & Trend', 'A confidence score combines signal, consensus, volume, source quality, recency, and stability, while history tracks changes over time.'],
                    ].map((entry) => {
                      const [Icon, title, desc] = entry;
                      return (
                        <div key={title} className="p-4 bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm">
                          <Icon className="w-4 h-4 text-gray-500 dark:text-gray-400 mb-2" />
                          <div className="text-sm font-semibold text-gray-800 dark:text-gray-200 mb-1">{title}</div>
                          <div className="text-xs text-gray-400 dark:text-gray-500 leading-relaxed">{desc}</div>
                        </div>
                      );
                    })}
                  </div>

                  <div className="mt-8 flex items-center justify-center gap-2 flex-wrap">
                    <span className="text-xs text-gray-400 dark:text-gray-500 mr-1 flex items-center gap-1">
                      <Sparkles className="w-3.5 h-3.5" /> Try:
                    </span>
                    {['TSLA', 'AAPL', 'NVDA', 'RELIANCE.NS'].map((sym) => (
                      <button
                        key={sym}
                        onClick={() => handleStockSelect(sym)}
                        className={`px-3 py-1.5 text-xs font-semibold rounded-full border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:border-gray-900 dark:hover:border-gray-400 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors ${FOCUS_RING}`}
                      >
                        {sym}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </main>

            <Sidebar activeTicker={ticker} loading={loading} onSelect={handleStockSelect} />
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800 mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400 text-sm flex-wrap justify-center">
              <span className="font-semibold text-gray-900 dark:text-gray-100">Market Mood Detector</span>
              <span className="text-xs px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400 font-medium">v{APP_VERSION}</span>
              <span className="hidden sm:inline"></span>
            </div>
            <p className="text-xs text-gray-400 dark:text-gray-500">© 2026 Market Mood Detector</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
