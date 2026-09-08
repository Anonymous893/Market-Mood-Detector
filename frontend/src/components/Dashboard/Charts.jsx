import { memo, useMemo } from 'react';
import {
  ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip as RcTooltip,
  LineChart, Line, ReferenceLine,
} from 'recharts';
import { Clock } from 'lucide-react';
import { CARD, SEMANTIC } from '../../constants/ui';

const pct1 = (v) => `${v > 0 ? '+' : ''}${((v ?? 0) * 100).toFixed(1)}%`;
const PANEL = `${CARD} p-5`;
const TITLE = 'text-base font-semibold text-gray-800 dark:text-gray-200';
const SUBTITLE = 'text-xs text-gray-400 dark:text-gray-500 mt-0.5 mb-4';
const FOOTER = 'mt-3 pt-3 border-t border-gray-100 dark:border-gray-700 text-xs text-gray-500 dark:text-gray-400';

function ChartHeader({ title, subtitle }) {
  return (
    <div className="mb-1">
      <h3 className={TITLE}>{title}</h3>
      {subtitle && <p className={SUBTITLE}>{subtitle}</p>}
    </div>
  );
}

function RadarPanel({ advanced_stats, totalArticles }) {
  const a = advanced_stats ?? {};
  const data = useMemo(() => [
    { metric: 'Sentiment', value: +(((a.avg_sentiment ?? 0) + 1) / 2 * 100).toFixed(1) },
    { metric: 'Consensus', value: +((a.consensus_strength ?? 0) * 100).toFixed(1) },
    { metric: 'Recency', value: +Math.min(((a.articles_24h ?? 0) / Math.max(a.articles_7d ?? 1, 1)) * 100, 100).toFixed(1) },
    { metric: 'Volume', value: +Math.min((totalArticles / 30) * 100, 100).toFixed(1) },
    { metric: 'Stability', value: +Math.max(0, Math.min((1 - (a.volatility ?? 0) * 2) * 100, 100)).toFixed(1) },
  ], [a.avg_sentiment, a.consensus_strength, a.articles_24h, a.articles_7d, a.volatility, totalArticles]);

  const strongest = data.reduce((best, d) => (d.value > best.value ? d : best), data[0]);

  return (
    <div className={PANEL}>
      <ChartHeader title="Market Strength Radar" subtitle="Normalized view of the backend's core signal dimensions" />
      <div className="h-60">
        <ResponsiveContainer width="100%" height="100%">
          <RadarChart data={data}>
            <PolarGrid stroke="#e5e7eb" />
            <PolarAngleAxis dataKey="metric" tick={{ fontSize: 11, fill: '#6b7280' }} />
            <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 9, fill: '#9ca3af' }} />
            <Radar name="Score" dataKey="value" stroke="#111827" fill="#111827" fillOpacity={0.15} strokeWidth={2} />
            <RcTooltip formatter={(v) => [`${Number(v).toFixed(1)}`, 'Score']} />
          </RadarChart>
        </ResponsiveContainer>
      </div>
      <p className={FOOTER}>Strongest dimension: <span className="font-semibold text-gray-700 dark:text-gray-300">{strongest.metric}</span> ({strongest.value.toFixed(0)}/100)</p>
    </div>
  );
}

function TimePanel({ advanced_stats, trend }) {
  const a = advanced_stats ?? {};
  return (
    <div className={PANEL}>
      <ChartHeader title="Time-Based Sentiment" subtitle="Recent coverage versus the trailing week" />
      <div className="space-y-3">
        {[
          { label: 'Last 24 Hours', count: a.articles_24h ?? 0, value: a.sentiment_24h ?? 0 },
          { label: 'Last 7 Days', count: a.articles_7d ?? 0, value: a.sentiment_7d ?? 0 },
        ].map(({ label, count, value }) => (
          <div key={label} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-100 dark:border-gray-700">
            <div>
              <div className="text-sm font-medium text-gray-700 dark:text-gray-300">{label}</div>
              <div className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">{count} scored articles</div>
            </div>
            <div className={`text-xl font-bold tabular-nums ${value > 0 ? SEMANTIC.positive.text : value < 0 ? SEMANTIC.negative.text : SEMANTIC.neutral.text}`}>
              {pct1(value)}
            </div>
          </div>
        ))}

        <div className={`p-3 ${SEMANTIC.info.bg} rounded-lg border ${SEMANTIC.info.border}`}>
          <div className="flex items-center gap-2 mb-1">
            <Clock className="w-3.5 h-3.5 text-blue-500" />
            <span className="text-xs font-semibold text-blue-800 dark:text-blue-300">Coverage Freshness</span>
          </div>
          <p className="text-xs text-blue-600 dark:text-blue-400">
            {(a.articles_24h ?? 0) > 0 ? 'Active' : 'Limited'} recent coverage ·{' '}
            {Math.round(((a.articles_24h ?? 0) / Math.max(a.articles_7d ?? 1, 1)) * 100)}% from last 24 h
            {a.avg_article_age_hours != null && ` · avg age ${a.avg_article_age_hours.toFixed(1)} h`}
          </p>
          {trend && trend.direction !== 'new' && (
            <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
              Trend: {trend.direction} · confidence {trend.confidence_delta > 0 ? '+' : ''}{(trend.confidence_delta ?? 0).toFixed(1)} points
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

function PiePanel({ stats }) {
  const total = (stats?.bullish ?? 0) + (stats?.neutral ?? 0) + (stats?.bearish ?? 0);
  const pieData = [
    { name: 'Bullish', value: stats?.bullish ?? 0, color: SEMANTIC.positive.hex },
    { name: 'Neutral', value: stats?.neutral ?? 0, color: SEMANTIC.neutral.hex },
    { name: 'Bearish', value: stats?.bearish ?? 0, color: SEMANTIC.negative.hex },
  ].filter((d) => d.value > 0);
  const majority = pieData.length ? pieData.reduce((best, d) => (d.value > best.value ? d : best), pieData[0]) : null;

  return (
    <div className={PANEL}>
      <ChartHeader title="Sentiment Distribution" subtitle={`${total} scored articles by sentiment class`} />
      <div className="h-52">
        {pieData.length ? (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie data={pieData} cx="50%" cy="50%" innerRadius={52} outerRadius={80} paddingAngle={3} dataKey="value">
                {pieData.map((e) => <Cell key={e.name} fill={e.color} />)}
              </Pie>
              <RcTooltip formatter={(v, n) => [v, n]} />
            </PieChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-full flex items-center justify-center text-sm text-gray-400 dark:text-gray-500">No scored articles</div>
        )}
      </div>
      <div className="flex justify-center gap-5 mt-2">
        {pieData.map((e) => (
          <div key={e.name} className="flex items-center gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: e.color }} />
            <span className="text-xs text-gray-600 dark:text-gray-400">{e.name}</span>
          </div>
        ))}
      </div>
      {majority && <p className={FOOTER}><span className="font-semibold text-gray-700 dark:text-gray-300">{majority.name}</span> makes up {total > 0 ? Math.round((majority.value / total) * 100) : 0}% of coverage</p>}
    </div>
  );
}

function SourcePanel({ source_contributions, source_health }) {
  const contributions = Object.entries(source_contributions ?? {});
  const health = source_health ?? [];
  const mainSource = contributions[0]?.[1];
  const mainName = contributions[0]?.[0] ?? health[0]?.name ?? 'Yahoo Finance';
  const mainHealth = health.find((h) => h.name === mainName);

  return (
    <div className={PANEL}>
      <ChartHeader title="News Coverage" subtitle="The refactored backend intentionally uses one source" />
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-sm font-semibold text-gray-800 dark:text-gray-200">{mainName}</span>
          <span className={`text-xs font-semibold ${mainHealth?.status === 'ok' ? SEMANTIC.positive.text : SEMANTIC.warning.text}`}>{mainHealth?.status === 'ok' ? 'Healthy' : mainHealth?.status ?? 'Unknown'}</span>
        </div>
        <div>
          <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
            <span>Weighted contribution</span>
            <span>{mainSource?.contribution_pct ?? 0}%</span>
          </div>
          <div className="h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
            <div className="h-full rounded-full bg-gray-700 dark:bg-gray-300" style={{ width: `${Math.min(mainSource?.contribution_pct ?? 0, 100)}%` }} />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
            <div className="text-xs text-gray-400 dark:text-gray-500">Articles scored</div>
            <div className="text-xl font-bold text-gray-800 dark:text-gray-200 mt-1">{mainSource?.articles ?? 0}</div>
          </div>
          <div className="p-3 bg-gray-50 dark:bg-gray-900 rounded-lg">
            <div className="text-xs text-gray-400 dark:text-gray-500">Fetch latency</div>
            <div className="text-xl font-bold text-gray-800 dark:text-gray-200 mt-1">{mainHealth?.duration_ms != null ? `${mainHealth.duration_ms}ms` : '—'}</div>
          </div>
        </div>
      </div>
      <p className={FOOTER}>Source reliability is fixed at 1.0 in the backend; the useful variation comes from article sentiment, recency, and history.</p>
    </div>
  );
}

function TrendTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0];
  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg px-3 py-2 text-xs max-w-[200px]">
      <p className="font-medium text-gray-700 dark:text-gray-300 truncate mb-0.5">{d.payload.title}…</p>
      <p style={{ color: d.value >= 0 ? SEMANTIC.positive.hex : SEMANTIC.negative.hex }}>Score: {d.value > 0 ? '+' : ''}{d.value?.toFixed(1)}</p>
    </div>
  );
}

function TrendPanel({ top_comments }) {
  const articles = (top_comments ?? []).slice(0, 12);
  const data = articles.map((c, i) => ({ index: i + 1, sentiment: +(c.score * 100).toFixed(2), title: c.text?.slice(0, 40) ?? '' }));
  const avg = data.length ? data.reduce((sum, d) => sum + d.sentiment, 0) / data.length : 0;

  return (
    <div className={PANEL}>
      <ChartHeader title="Sentiment Across Top Articles" subtitle={`Score progression across the ${data.length} most informative headlines`} />
      <div className="h-52">
        {data.length ? (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
              <XAxis dataKey="index" tick={{ fontSize: 11, fill: '#9ca3af' }} label={{ value: 'Article #', position: 'insideBottom', offset: -2, fontSize: 11, fill: '#9ca3af' }} />
              <YAxis tick={{ fontSize: 11, fill: '#9ca3af' }} tickFormatter={(v) => `${v > 0 ? '+' : ''}${v}`} />
              <RcTooltip content={<TrendTooltip />} />
              <ReferenceLine y={0} stroke="#e5e7eb" strokeDasharray="4 3" />
              <Line type="monotone" dataKey="sentiment" stroke="#111827" strokeWidth={2} dot={{ fill: '#111827', r: 3, strokeWidth: 0 }} activeDot={{ r: 5 }} />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-full flex items-center justify-center text-sm text-gray-400 dark:text-gray-500">No scored headlines available</div>
        )}
      </div>
      {data.length > 0 && <p className={FOOTER}>Average score across shown articles: <span className={`font-semibold ${avg >= 0 ? SEMANTIC.positive.text : SEMANTIC.negative.text}`}>{avg > 0 ? '+' : ''}{avg.toFixed(1)}</span></p>}
    </div>
  );
}

const VERDICT_COLOR = {
  'STRONG BUY': '#16a34a',
  'BUY': '#4ade80',
  'HOLD': '#9ca3af',
  'SELL': '#f87171',
  'STRONG SELL': '#dc2626',
  'INSUFFICIENT DATA': '#d97706',
};

function HistoryDot(props) {
  const { cx, cy, payload } = props;
  const color = VERDICT_COLOR[payload.verdict] ?? '#9ca3af';
  return <circle cx={cx} cy={cy} r={5} fill={color} stroke="white" strokeWidth={1.5} />;
}

function HistoryPanel({ history }) {
  if (!history?.length) return null;

  const chartData = [...history].reverse().map((h) => ({
    ts: new Date(h.timestamp).toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
    confidence: h.confidence_score,
    sentiment: Math.round(h.avg_sentiment * 100),
    verdict: h.verdict,
  }));

  return (
    <div className={PANEL}>
      <ChartHeader title="Analysis History" subtitle={`Confidence and sentiment across the last ${history.length} stored runs`} />
      {chartData.length >= 2 && (
        <div className="h-36 mb-5">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 4, right: 8, bottom: 0, left: -20 }}>
              <XAxis dataKey="ts" tick={{ fontSize: 10, fill: '#9ca3af' }} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 10, fill: '#9ca3af' }} />
              <RcTooltip formatter={(v, n) => [n === 'confidence' ? `${v}%` : `${v > 0 ? '+' : ''}${v}%`, n === 'confidence' ? 'Confidence' : 'Sentiment']} />
              <Line type="monotone" dataKey="confidence" stroke="#111827" strokeWidth={2} dot={<HistoryDot />} activeDot={{ r: 6 }} />
              <Line type="monotone" dataKey="sentiment" stroke="#6b7280" strokeWidth={1.5} strokeDasharray="4 2" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
      <div className="space-y-2">
        {history.map((h, i) => {
          const date = new Date(h.timestamp);
          const label = date.toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
          return (
            <div key={`${h.timestamp}-${i}`} className="flex items-center gap-3 text-xs flex-wrap">
              <span className="text-gray-400 dark:text-gray-500 w-32 shrink-0">{label}</span>
              <span className="px-2 py-0.5 rounded font-semibold text-white text-xs shrink-0" style={{ backgroundColor: VERDICT_COLOR[h.verdict] ?? '#9ca3af' }}>{h.verdict}</span>
              <span className="text-gray-500 dark:text-gray-400">{h.confidence_score?.toFixed(1)}% conf</span>
              <span className={`${h.avg_sentiment > 0 ? SEMANTIC.positive.text : h.avg_sentiment < 0 ? SEMANTIC.negative.text : 'text-gray-400'}`}>{h.avg_sentiment > 0 ? '+' : ''}{(h.avg_sentiment * 100).toFixed(1)}%</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

const MemoRadarPanel = memo(RadarPanel);
const MemoTimePanel = memo(TimePanel);
const MemoPiePanel = memo(PiePanel);
const MemoSourcePanel = memo(SourcePanel);
const MemoTrendPanel = memo(TrendPanel);
const MemoHistoryPanel = memo(HistoryPanel);

export {
  MemoRadarPanel as RadarPanel,
  MemoTimePanel as TimePanel,
  MemoPiePanel as PiePanel,
  MemoSourcePanel as SourcePanel,
  MemoTrendPanel as TrendPanel,
  MemoHistoryPanel as HistoryPanel,
};
