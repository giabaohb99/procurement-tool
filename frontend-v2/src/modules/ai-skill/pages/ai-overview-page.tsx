import { Activity, BookOpen, ShieldAlert, Sparkles, Users } from 'lucide-react'
import { Link } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { Card, CardContent, CardHeader } from '@/shared/ui/card'
import { ColumnChart } from '@/shared/ui/column-chart'
import { ErrorState } from '@/shared/ui/error-state'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { SectionHeading } from '@/shared/ui/section-heading'
import { Skeleton } from '@/shared/ui/skeleton'
import { StatCard } from '@/shared/ui/stat-card'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import { KeyStateBadge } from '../config/ai-skill-meta'
import { describeChange, shortDay } from '../utils/overview-format'
import { useAiOverview, useSkillTitles } from '../hooks/use-my-ai'
import type { AiOverview } from '../types/ai-skill'

/**
 * G1 — Tổng quan Kho skill AI (doc 21 §6.2, K6 bao-CR-624): năm thẻ số, cột lượt gọi 14 ngày, ba bảng nhỏ (skill được
 * đọc nhiều, người dùng nhiều, công cụ dùng nhiều) và khóa sắp hết hạn. Số liệu từ `GET /api/agent-hub/ai-overview`,
 * đường này đòi quyền quản lý bot AI (`agent_group.read`) — thiếu thì trang nói rõ thay vì gọi để ăn 403.
 */
export function AiOverviewPage() {
  const { can } = usePermission()
  const allowed = can('agent_group', 'read')
  const { data, isLoading, isError } = useAiOverview(allowed)

  if (!allowed) {
    return (
      <PageContainer>
        <PageHeader title="Tổng quan" />
        <ErrorState
          title="Tổng quan dành cho người quản lý trợ lý AI"
          description="Bạn vẫn dùng được Bộ skill và Nhật ký sử dụng của mình ở menu bên trái."
        />
      </PageContainer>
    )
  }

  return (
    <PageContainer>
      <PageHeader
        title="Tổng quan"
        description="AI riêng của nhân sự đang dùng cẩm nang và dữ liệu ERP thế nào trong 7 – 14 ngày gần đây."
      />
      {isError ? (
        <ErrorState title="Không tải được số liệu" description="Dịch vụ AI chưa trả lời. Thử lại sau ít phút." />
      ) : (
        <OverviewBody data={data} loading={isLoading} />
      )}
    </PageContainer>
  )
}

function OverviewBody({ data, loading }: { data?: AiOverview; loading: boolean }) {
  const titles = useSkillTitles((data?.top_skills ?? []).map((s) => s.skill_id))
  const problems = (data?.denied_7d ?? 0) + (data?.error_7d ?? 0)

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-5">
        <StatCard
          icon={BookOpen}
          label="Bộ skill"
          value={data?.skills ? data.skills.skill_sets : '—'}
          hint={data && !data.skills ? 'ERP chưa trả lời' : undefined}
          loading={loading}
          to={appRoutes.aiSkill.root}
        />
        <StatCard icon={Sparkles} label="Skill đang dùng" value={data?.skills ? data.skills.skills : '—'} loading={loading} />
        <StatCard
          icon={Users}
          label="Người đã nối AI"
          value={data?.connected_users ?? 0}
          hint={data ? `${data.connected_days} ngày gần nhất` : undefined}
          loading={loading}
        />
        <StatCard
          icon={Activity}
          label="Lượt gọi 7 ngày"
          value={data?.calls_7d ?? 0}
          hint={data ? describeChange(data.calls_change_pct, data.calls_prev_7d) : undefined}
          loading={loading}
          to={appRoutes.aiSkill.logs}
        />
        <StatCard
          icon={ShieldAlert}
          label="Từ chối và lỗi 7 ngày"
          value={problems}
          hint={data ? `${data.denied_7d} từ chối · ${data.error_7d} lỗi` : undefined}
          tone={problems > 0 ? 'warning' : undefined}
          loading={loading}
          to={appRoutes.aiSkill.logs}
          className="max-sm:col-span-2"
        />
      </div>

      <Card>
        <CardHeader>
          <SectionHeading>Lượt gọi 14 ngày</SectionHeading>
        </CardHeader>
        <CardContent>
          {loading || !data ? (
            <Skeleton className="h-64 w-full" />
          ) : (
            <ColumnChart data={data.daily.map((d) => ({ label: shortDay(d.day), value: d.total }))} unit="lượt" height={260} />
          )}
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-3">
        <RankCard
          title="Skill được đọc nhiều"
          loading={loading}
          rows={(data?.top_skills ?? []).map((s) => ({ key: String(s.skill_id), label: titles.get(s.skill_id) || `Skill #${s.skill_id}`, calls: s.calls }))}
        />
        <RankCard
          title="Người dùng nhiều"
          loading={loading}
          rows={(data?.top_users ?? []).map((u) => ({ key: String(u.key), label: u.label || `#${u.key}`, calls: u.calls }))}
        />
        <RankCard
          title="Công cụ dùng nhiều"
          loading={loading}
          rows={(data?.top_tools ?? []).map((t) => ({ key: t.key, label: t.key, calls: t.calls, mono: true }))}
        />
      </div>

      <Card>
        <CardHeader>
          <SectionHeading>Khóa kết nối</SectionHeading>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          {loading || !data ? (
            <Skeleton className="h-16 w-full" />
          ) : (
            <>
              <div className="flex flex-wrap gap-3">
                {data.keys_by_state.map((s) => (
                  <span key={s.state} className="flex items-center gap-1.5">
                    <KeyStateBadge state={s.state} label={s.label} />
                    <span className="tabular-nums">{s.count}</span>
                  </span>
                ))}
              </div>
              {data.expiring_keys.length === 0 ? (
                <p className="text-muted-foreground">Không có khóa nào hết hạn trong {data.expiring_days} ngày tới.</p>
              ) : (
                <div className="space-y-1">
                  <p className="font-medium text-warning">
                    {data.expiring_keys.length} khóa hết hạn trong {data.expiring_days} ngày tới
                  </p>
                  <ul className="divide-y rounded-md border">
                    {data.expiring_keys.map((k) => (
                      <li key={k.key_id} className="flex flex-wrap items-center gap-3 px-3 py-2">
                        <span className="min-w-0 flex-1 font-medium">{k.owner_label || `#${k.user_id}`}</span>
                        <span className="text-muted-foreground">{k.name || 'Khóa kết nối'}</span>
                        <span className="text-xs whitespace-nowrap text-muted-foreground">hết hạn {formatDate(k.expires_at)}</span>
                      </li>
                    ))}
                  </ul>
                  <Link to={appRoutes.aiSkill.keys} className="text-xs text-primary hover:underline">
                    Mở Khóa nhân sự để phát khóa mới
                  </Link>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function RankCard({
  title,
  rows,
  loading,
}: {
  title: string
  rows: { key: string; label: string; calls: number; mono?: boolean }[]
  loading: boolean
}) {
  return (
    <Card className="min-w-0">
      <CardHeader>
        <SectionHeading>{title}</SectionHeading>
      </CardHeader>
      <CardContent className="text-sm">
        {loading ? (
          <Skeleton className="h-24 w-full" />
        ) : rows.length === 0 ? (
          <p className="text-muted-foreground">Chưa có lượt nào trong 14 ngày.</p>
        ) : (
          <ol className="space-y-1.5">
            {rows.map((row, i) => (
              <li key={row.key} className="flex items-center gap-2">
                <span className="w-5 shrink-0 text-right text-xs text-muted-foreground tabular-nums">{i + 1}</span>
                <span className={cn('min-w-0 flex-1 truncate', row.mono && 'font-mono text-xs')} title={row.label}>
                  {row.label}
                </span>
                <span className="shrink-0 tabular-nums">{row.calls.toLocaleString('vi-VN')}</span>
              </li>
            ))}
          </ol>
        )}
      </CardContent>
    </Card>
  )
}
