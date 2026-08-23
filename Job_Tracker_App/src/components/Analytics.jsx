import { useMemo } from 'react'
import {
  Briefcase, TrendingUp, Award, Clock,
  FileText, Calendar, Target,
} from 'lucide-react'
import { STATUS_CONFIG, COLUMN_ORDER } from '../utils/statusConfig'
import { calculateStats, formatPercentage, formatDays } from '../utils/analyticsHelpers'

// ─── Primitive building blocks ────────────────────────────────────────────────

function MetricCard({ icon: Icon, iconColor, title, value, sub, children }) {
  return (
    <div className="bg-gray-800/60 border border-gray-700/60 rounded-xl p-5 flex flex-col gap-3">
      <div className="flex items-center gap-2 text-gray-500">
        <Icon size={14} className={iconColor} />
        <span className="text-xs font-medium uppercase tracking-wide">{title}</span>
      </div>
      {value !== undefined && (
        <div>
          <p className="text-3xl font-bold text-white tabular-nums leading-none">{value}</p>
          {sub && <p className="text-xs text-gray-500 mt-1.5 leading-relaxed">{sub}</p>}
        </div>
      )}
      {children}
    </div>
  )
}

function HBar({ pct, colorClass, label, count, total }) {
  return (
    <div className="flex items-center gap-2.5">
      <span className="w-24 shrink-0 text-xs text-gray-400 truncate text-right">{label}</span>
      <div className="flex-1 bg-gray-700/40 rounded-full h-2 overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${colorClass}`}
          style={{ width: `${Math.max(pct, pct > 0 ? 2 : 0)}%` }}
        />
      </div>
      <span className="w-14 shrink-0 text-right tabular-nums text-xs text-gray-400">
        {count}{total > 0 ? ` · ${Math.round(pct)}%` : ''}
      </span>
    </div>
  )
}

// ─── Section: Status Breakdown ────────────────────────────────────────────────

function StatusBreakdown({ byStatus, total }) {
  return (
    <MetricCard icon={Target} iconColor="text-indigo-400" title="By Status">
      <div className="space-y-2.5">
        {COLUMN_ORDER.map((status) => {
          const cfg   = STATUS_CONFIG[status]
          const count = byStatus[status] ?? 0
          const pct   = total > 0 ? (count / total) * 100 : 0
          return (
            <HBar
              key={status}
              label={cfg.label}
              count={count}
              pct={pct}
              total={total}
              colorClass={cfg.dot.replace('bg-', 'bg-')}
            />
          )
        })}
      </div>
    </MetricCard>
  )
}

// ─── Section: Resume Performance ─────────────────────────────────────────────

function ResumePerformance({ resumePerformance }) {
  if (resumePerformance.length === 0) {
    return (
      <MetricCard icon={FileText} iconColor="text-indigo-400" title="Resume Performance">
        <p className="text-xs text-gray-600">No resume tags found. Tag your jobs with a resume version to track performance.</p>
      </MetricCard>
    )
  }

  const best = resumePerformance[0]

  return (
    <MetricCard icon={FileText} iconColor="text-indigo-400" title="Resume Performance"
      sub={resumePerformance.length > 1 ? `Best: ${best.resume} (${formatPercentage(best.rate, 0)} interview rate)` : undefined}
    >
      <div className="space-y-2">
        {resumePerformance.map((r, i) => (
          <div key={r.resume} className="flex items-center gap-2 text-xs">
            <span className={`shrink-0 font-medium ${i === 0 ? 'text-emerald-400' : 'text-gray-400'}`}>
              {r.resume}
            </span>
            <div className="flex-1 bg-gray-700/40 rounded-full h-1.5 overflow-hidden">
              <div
                className={`h-full rounded-full ${i === 0 ? 'bg-emerald-500' : 'bg-gray-500'}`}
                style={{ width: `${Math.max(r.rate, r.rate > 0 ? 2 : 0)}%` }}
              />
            </div>
            <span className="shrink-0 tabular-nums text-gray-500">
              {r.apps} apps · {r.interviews} interviews · {formatPercentage(r.rate, 0)}
            </span>
          </div>
        ))}
      </div>
    </MetricCard>
  )
}

// ─── Section: Funnel Chart ────────────────────────────────────────────────────

const FUNNEL_LABELS = {
  applied:      'Applied',
  phone_screen: 'Phone Screen',
  interview:    'Interview',
  offer:        'Offer',
}
const FUNNEL_COLORS = {
  applied:      'bg-amber-500',
  phone_screen: 'bg-violet-500',
  interview:    'bg-orange-500',
  offer:        'bg-emerald-500',
}

function FunnelChart({ funnel }) {
  const base = funnel[0]?.count ?? 0

  return (
    <div className="bg-gray-800/60 border border-gray-700/60 rounded-xl p-5">
      <div className="flex items-center gap-2 text-gray-500 mb-4">
        <TrendingUp size={14} className="text-indigo-400" />
        <span className="text-xs font-medium uppercase tracking-wide">Application Funnel</span>
      </div>
      <div className="space-y-3">
        {funnel.map(({ stage, count }, i) => {
          const pct    = base > 0 ? (count / base) * 100 : 0
          const prev   = i > 0 ? funnel[i - 1].count : count
          const dropPct = prev > 0 ? Math.round(((prev - count) / prev) * 100) : 0
          return (
            <div key={stage}>
              <div className="flex items-center justify-between text-xs mb-1.5">
                <span className="text-gray-300">{FUNNEL_LABELS[stage]}</span>
                <div className="flex items-center gap-3 tabular-nums">
                  {i > 0 && dropPct > 0 && (
                    <span className="text-red-400">−{dropPct}%</span>
                  )}
                  <span className="text-white font-medium">{count}</span>
                  <span className="text-gray-500">({formatPercentage(pct, 0)})</span>
                </div>
              </div>
              <div className="bg-gray-700/40 rounded-full h-3 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-700 ${FUNNEL_COLORS[stage]}`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          )
        })}
      </div>
      {base === 0 && (
        <p className="text-xs text-gray-600 text-center mt-4">No active applications yet</p>
      )}
    </div>
  )
}

// ─── Section: Timeline Chart ──────────────────────────────────────────────────

function TimelineChart({ timeline }) {
  const maxCount = Math.max(...timeline.map((d) => d.count), 1)
  // Show every 5th label to avoid crowding
  const labelEvery = 5

  return (
    <div className="bg-gray-800/60 border border-gray-700/60 rounded-xl p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2 text-gray-500">
          <Calendar size={14} className="text-indigo-400" />
          <span className="text-xs font-medium uppercase tracking-wide">Application Timeline (30 days)</span>
        </div>
        <span className="text-xs text-gray-500 tabular-nums">
          Total: {timeline[timeline.length - 1]?.cumulative ?? 0}
        </span>
      </div>

      {/* Bars */}
      <div className="flex items-end gap-0.5 h-20 overflow-x-auto pb-1">
        {timeline.map(({ date, count, label }, i) => {
          const heightPct = count > 0 ? Math.max((count / maxCount) * 100, 8) : 0
          return (
            <div
              key={date}
              className="relative flex flex-col items-center group shrink-0"
              style={{ width: '3%', minWidth: 8 }}
              title={`${label}: ${count} new`}
            >
              <div className="flex-1 w-full flex items-end">
                <div
                  className="w-full rounded-t-sm bg-indigo-500/60 group-hover:bg-indigo-400 transition-colors"
                  style={{ height: count > 0 ? `${heightPct}%` : '2px', opacity: count > 0 ? 1 : 0.2 }}
                />
              </div>
              {/* Label every N days */}
              {i % labelEvery === 0 && (
                <span className="absolute -bottom-5 text-[9px] text-gray-600 whitespace-nowrap rotate-0 leading-none">
                  {label}
                </span>
              )}
            </div>
          )
        })}
      </div>
      <div className="h-5" /> {/* space for rotated labels */}
    </div>
  )
}

// ─── Main Analytics Component ─────────────────────────────────────────────────

export default function Analytics({ jobs }) {
  const stats = useMemo(() => calculateStats(jobs), [jobs])

  const interviewRateLabel = stats.activeCount > 0
    ? `${stats.interviewRate >= 1 ? Math.round(stats.interviewRate) : '<1'}% of active applications reached interview stage`
    : 'No active applications yet'

  const offerRateLabel = stats.activeCount > 0
    ? `1 offer per ${stats.offerRate > 0 ? Math.round(100 / stats.offerRate) : '∞'} applications`
    : 'No offers yet'

  return (
    <div className="space-y-6">
      {/* ── Row 1: 4 key metrics ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          icon={Briefcase}
          iconColor="text-indigo-400"
          title="Total Applications"
          value={stats.total}
          sub={`${stats.activeCount} active · ${stats.appsThisMonth} this month`}
        />
        <MetricCard
          icon={TrendingUp}
          iconColor="text-emerald-400"
          title="Interview Rate"
          value={formatPercentage(stats.interviewRate, 1)}
          sub={interviewRateLabel}
        />
        <MetricCard
          icon={Award}
          iconColor="text-amber-400"
          title="Offer Rate"
          value={formatPercentage(stats.offerRate, 1)}
          sub={offerRateLabel}
        />
        <MetricCard
          icon={Clock}
          iconColor="text-violet-400"
          title="Days to Interview"
          value={formatDays(stats.avgDaysToInterview)}
          sub={`Median: ${formatDays(stats.medianDaysToInterview)}`}
        />
      </div>

      {/* ── Row 2: Status breakdown + Resume performance ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <StatusBreakdown byStatus={stats.byStatus} total={stats.total} />
        <ResumePerformance resumePerformance={stats.resumePerformance} />
      </div>

      {/* ── Row 3: Charts ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <FunnelChart funnel={stats.funnel} />
        <TimelineChart timeline={stats.timeline} />
      </div>
    </div>
  )
}
