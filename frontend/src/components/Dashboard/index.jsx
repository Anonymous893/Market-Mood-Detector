import { Signal, Newspaper, Target, Calendar, AlertTriangle, Zap } from 'lucide-react';
import VerdictCard from './VerdictCard';
import MetricCards from './MetricCards';
import Headlines from './Headlines';
import AnalyticsCards, { ExportToolbar } from './AnalyticsCards';
import SourceContribution from './SourceContribution';
import { RadarPanel, TimePanel, PiePanel, SourcePanel, TrendPanel, HistoryPanel } from './Charts';

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

const SECTION_TITLE = 'text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3';

export default function Dashboard({ data }) {
  const {
    stats,
    top_comments,
    advanced_stats,
    history,
    meta,
    timing,
    cached,
    cache_meta,
    source_contributions,
    source_health,
    confidence_score,
    trend,
    model_used,
  } = data;

  const totalArticles = (stats?.bullish ?? 0) + (stats?.bearish ?? 0) + (stats?.neutral ?? 0);
  const dateStr = new Date().toISOString().split('T')[0];
  const hasAnalytics = Boolean(advanced_stats);

  const handleExport = (format) => {
    if (format === 'json') {
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      downloadBlob(blob, `${data.ticker}_market_mood_${dateStr}.json`);
    } else if (format === 'csv') {
      const rows = [
        ['Text', 'Score', 'Sentiment', 'Source', 'SourceWeight', 'TimeAgo', 'HoursOld'],
        ...(top_comments ?? []).map((c) => [
          `"${(c.text ?? '').replace(/"/g, '""')}"`,
          Number(c.score ?? 0).toFixed(4),
          c.sentiment ?? '',
          c.source ?? '',
          c.source_weight ?? '',
          c.time_ago ?? '',
          c.hours_old ?? '',
        ]),
      ];
      const csv = rows.map((r) => r.join(',')).join('\n');
      const blob = new Blob([csv], { type: 'text/csv' });
      downloadBlob(blob, `${data.ticker}_headlines_${dateStr}.csv`);
    } else if (format === 'pdf') {
      window.print();
    }
  };

  return (
    <div className="space-y-8 animate-fadeIn" id="dashboard-print-area">
      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className={`${SECTION_TITLE} mb-0`}>Analysis Summary</h2>
          <div className="no-print">
            <ExportToolbar onExport={handleExport} />
          </div>
        </div>
        <AnalyticsCards
          confidence_score={confidence_score}
          meta={meta}
          timing={timing}
          cached={cached}
          cache_meta={cache_meta}
          model_used={model_used}
        />
      </section>

      <VerdictCard data={data} />

      {hasAnalytics ? (
        <section className="space-y-4">
          <h2 className={SECTION_TITLE}>Sentiment Analytics</h2>
          <MetricCards advanced_stats={advanced_stats} stats={stats} />

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <RadarPanel advanced_stats={advanced_stats} totalArticles={totalArticles} />
            <TimePanel advanced_stats={advanced_stats} trend={trend} />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <PiePanel stats={stats} />
            <SourcePanel source_contributions={source_contributions} source_health={source_health} />
          </div>

          <TrendPanel top_comments={top_comments} />
        </section>
      ) : (
        <section className="p-5 bg-gray-50 dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2 mb-2">
            <Target className="w-4 h-4 text-gray-500 dark:text-gray-400" />
            <h2 className="text-sm font-semibold text-gray-800 dark:text-gray-200">Limited Sentiment Data</h2>
          </div>
          <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
            The backend could not find enough Yahoo Finance articles with meaningful FinBERT sentiment to compute the full analytics panel.
            The verdict, source health, and available metadata are still shown below.
          </p>
        </section>
      )}

      <SourceContribution
        source_contributions={source_contributions}
        source_health={source_health}
      />

      <Headlines top_comments={top_comments} />

      <HistoryPanel history={history} />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-5 bg-gray-50 dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2 mb-3">
            <Calendar className="w-4 h-4 text-gray-500 dark:text-gray-400" />
            <h3 className="text-sm font-semibold text-gray-800 dark:text-gray-200">Analysis Methodology</h3>
          </div>
          <ul className="space-y-2 text-xs text-gray-600 dark:text-gray-400">
            {[
              [Signal,    'FinBERT analyses Yahoo Finance article headlines and produces a sentiment score for each article.'],
              [Newspaper, "Yahoo Finance is the project's only news source, using its ticker-specific RSS feed."],
              [Target,    'Near-neutral FinBERT scores are filtered, while stronger signals receive recency weighting before aggregation.'],
              [Zap,       'Confidence combines signal magnitude, consensus, article volume, source quality, recency, and signal stability. Historical runs are stored in SQLite for trend comparison.'],
            ].map((entry, i) => {
              const [Icon, text] = entry;
              return (
                <li key={i} className="flex items-start gap-2">
                  <Icon className="w-3.5 h-3.5 mt-0.5 text-gray-400 dark:text-gray-500 shrink-0" />
                  <span>{text}</span>
                </li>
              );
            })}
          </ul>
        </div>

        <div className="p-5 bg-amber-50 dark:bg-amber-900/20 rounded-xl border border-amber-200 dark:border-amber-800">
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="w-4 h-4 text-amber-600 dark:text-amber-400" />
            <h3 className="text-sm font-semibold text-amber-900 dark:text-amber-300">Disclaimer</h3>
          </div>
          <p className="text-xs text-amber-800 dark:text-amber-400 leading-relaxed">
            This analysis is for <strong>informational purposes only</strong> and does not constitute
            financial or investment advice. Automated sentiment can be incomplete or wrong, and a
            market-mood verdict does not predict price movement. Always conduct your own research
            and consult a licensed financial professional before investing.
          </p>
        </div>
      </div>
    </div>
  );
}
