import { HeartPulse, Lock } from 'lucide-react'
import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'
import { SearchField } from '@/shared/ui/search-field'
import { Skeleton } from '@/shared/ui/skeleton'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import { matchesVietnamese } from '@/shared/utils/vn-text'

import { PROJECT_HEALTH, type WorkOverviewProject } from '../hooks/use-work-overview'
import { PROJECT_HEALTH_TONE } from '../utils/project-health-tone'

/** Số thẻ mỗi lượt hiện — đủ ba hàng ở khổ rộng; dự án đáng lo nhất đã được máy chủ xếp lên đầu. */
const PAGE_SIZE = 9
/** Dòng "dự án chưa có việc" chỉ nêu chừng này tên — 100 tên nối nhau là một bức tường chữ. */
const EMPTY_NAMES = 10

const HEALTH_FILTERS: { label: string; code: number | null }[] = [
  { label: 'Tất cả', code: null },
  { label: 'Trễ', code: PROJECT_HEALTH.LATE },
  { label: 'Có rủi ro', code: PROJECT_HEALTH.AT_RISK },
  { label: 'Đúng tiến độ', code: PROJECT_HEALTH.ON_TRACK },
]

interface WorkOverviewProjectHealthCardsProps {
  projects: WorkOverviewProject[] | undefined
  isLoading: boolean
  isError: boolean
}

/** Một thẻ dự án: tên + nhãn sức khỏe, thanh tiến độ, một dòng số. Bấm được khi mình là thành viên. */
function ProjectCard({ project, onOpen }: { project: WorkOverviewProject; onOpen: () => void }) {
  const body = (
    <>
      <div className="flex items-start justify-between gap-2">
        <span className="flex min-w-0 items-center gap-1.5">
          <span className="truncate text-sm font-semibold text-foreground" title={project.name}>
            {project.name}
          </span>
          {!project.can_open && (
            <span className="shrink-0" title="Bạn chưa là thành viên dự án này nên chưa mở được bảng việc">
              <Lock className="size-3.5 text-muted-foreground" aria-label="Chưa là thành viên" />
            </span>
          )}
        </span>
        <Badge variant="outline" className={cn('shrink-0 font-medium', PROJECT_HEALTH_TONE[project.health])}>
          {project.health_label}
        </Badge>
      </div>

      <div className="mt-3 flex items-center gap-2">
        <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-muted">
          <span className="block h-full rounded-full bg-primary" style={{ width: `${project.progress}%` }} />
        </span>
        <span className="shrink-0 text-xs font-medium tabular-nums">{project.progress}%</span>
      </div>
      <p className="mt-1 text-xs text-muted-foreground tabular-nums">
        {project.done.toLocaleString('vi-VN')}/{project.total.toLocaleString('vi-VN')} việc đã xong
      </p>

      <p className="mt-3 flex flex-wrap gap-x-3 gap-y-1 text-xs text-muted-foreground">
        <span>
          <b className="font-semibold text-foreground tabular-nums">{project.open.toLocaleString('vi-VN')}</b> đang mở
        </span>
        <span className={cn(project.overdue > 0 && 'text-destructive')}>
          <b className={cn('font-semibold tabular-nums', project.overdue > 0 ? 'text-destructive' : 'text-foreground')}>
            {project.overdue.toLocaleString('vi-VN')}
          </b>{' '}
          quá hạn
        </span>
        <span>{project.last_due ? `hạn chót ${formatDate(project.last_due)}` : 'chưa có hạn chót'}</span>
      </p>
    </>
  )

  //  Không là thành viên: mở bảng việc là 403 — thẻ đứng yên, không giả làm nút.
  return project.can_open ? (
    <button
      type="button"
      onClick={onOpen}
      className="rounded-xl border bg-card p-4 text-left transition-colors hover:border-primary/40 hover:bg-muted/30"
    >
      {body}
    </button>
  ) : (
    <div className="rounded-xl border bg-card p-4">{body}</div>
  )
}

/**
 * SỨC KHỎE TỪNG DỰ ÁN trên tab Dự án của màn Tổng quan (duoc-CR-782) — lưới thẻ, mỗi dự án một thẻ. Bản bảng cũ anh
 * Được chê "xấu": chín dòng dự án trống toàn số 0, chữ "chưa là thành viên" lặp mỗi dòng, cột số rộng mà toàn 0.
 *
 * Dự án CHƯA CÓ VIỆC không có thẻ — gom thành một dòng chữ cuối khối (không có gì để theo dõi thì không chiếm chỗ).
 * Nhiều dự án (anh hỏi "lỡ có 100 dự án"): ô tìm + lọc theo sức khỏe kèm số, chỉ hiện 9 thẻ đầu, "Xem thêm" mở dần.
 * Nhãn: Trễ = từ 25% việc mở đã quá hạn; Có rủi ro = có việc quá hạn; Đúng tiến độ = không việc nào quá hạn. Máy chủ đã xếp
 * dự án đáng lo lên đầu.
 */
export function WorkOverviewProjectHealthCards({ projects, isLoading, isError }: WorkOverviewProjectHealthCardsProps) {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [health, setHealth] = useState<number | null>(null)
  const [visible, setVisible] = useState(PAGE_SIZE)

  const all = projects ?? []
  const active = all.filter((p) => p.health !== PROJECT_HEALTH.NO_TASKS)
  const empty = all.filter((p) => p.health === PROJECT_HEALTH.NO_TASKS && matchesVietnamese(p.name, query))
  const filtered = active.filter(
    (p) => (health === null || p.health === health) && matchesVietnamese(p.name, query),
  )
  const shown = filtered.slice(0, visible)
  const countOf = (code: number) => active.filter((p) => p.health === code).length

  //  Đổi bộ lọc là bắt đầu lại từ 9 thẻ đầu — giữ số thẻ đã mở của lần lọc trước thì danh sách mới mở bung bất ngờ.
  const changeQuery = (value: string) => {
    setQuery(value)
    setVisible(PAGE_SIZE)
  }
  const changeHealth = (value: number | null) => {
    setHealth(value)
    setVisible(PAGE_SIZE)
  }

  return (
    <Card className="gap-3">
      <CardHeader className="max-md:px-4">
        <CardTitle className="flex items-center gap-2 text-base">
          <HeartPulse className="size-4 text-muted-foreground" />
          Sức khỏe từng dự án
        </CardTitle>
        <CardDescription>Trễ: từ 25% việc mở đã quá hạn · Có rủi ro: có việc quá hạn · Đúng tiến độ: không việc nào quá hạn.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3 max-md:px-4">
        {!isLoading && !isError && active.length > 0 && (
          <div className="flex flex-wrap items-center gap-2">
            {/*  Khung cố định bề rộng: `SearchField` tự giãn `flex-1`, để trần là nó ăn hết hàng, đẩy nút lọc xuống. */}
            <div className="w-full sm:w-72">
              <SearchField
                value={query}
                onChange={changeQuery}
                placeholder="Tìm dự án…"
                aria-label="Tìm dự án"
                className="w-full"
              />
            </div>
            <div role="group" aria-label="Lọc theo sức khỏe" className="flex flex-wrap gap-1.5">
              {HEALTH_FILTERS.map((f) => {
                const count = f.code === null ? active.length : countOf(f.code)
                const on = health === f.code
                return (
                  <button
                    key={f.label}
                    type="button"
                    aria-pressed={on}
                    onClick={() => changeHealth(f.code)}
                    className={cn(
                      'rounded-full border px-3 py-1 text-xs transition-colors',
                      on ? 'border-primary/40 bg-primary/10 font-medium text-primary' : 'text-muted-foreground hover:text-foreground',
                    )}
                  >
                    {f.label} <span className="tabular-nums">({count})</span>
                  </button>
                )
              })}
            </div>
          </div>
        )}

        {isLoading ? (
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            {[0, 1, 2].map((i) => (
              <Skeleton key={i} className="h-32 w-full rounded-xl" />
            ))}
          </div>
        ) : isError ? (
          <p className="py-6 text-center text-sm text-destructive">Không tải được số liệu dự án.</p>
        ) : active.length === 0 ? (
          <p className="py-6 text-center text-sm text-muted-foreground">
            Chưa có dự án nào có việc trong phạm vi đang xem.
          </p>
        ) : filtered.length === 0 ? (
          //  Rỗng vì LỌC khác rỗng vì chưa có gì — nói rõ đang lọc.
          <p className="py-6 text-center text-sm text-muted-foreground">Không có dự án nào khớp bộ lọc.</p>
        ) : (
          <>
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {shown.map((p) => (
                <ProjectCard key={p.list_id} project={p} onOpen={() => navigate(appRoutes.project.detail(p.list_id))} />
              ))}
            </div>
            {filtered.length > shown.length && (
              <div className="flex justify-center">
                <Button variant="outline" size="sm" onClick={() => setVisible((v) => v + PAGE_SIZE)}>
                  Xem thêm {Math.min(PAGE_SIZE, filtered.length - shown.length)} dự án (còn{' '}
                  {(filtered.length - shown.length).toLocaleString('vi-VN')})
                </Button>
              </div>
            )}
          </>
        )}
        {!isLoading && empty.length > 0 && (
          <p className="text-xs text-muted-foreground">
            <span className="font-medium text-foreground">{empty.length} dự án chưa có việc:</span>{' '}
            {empty.slice(0, EMPTY_NAMES).map((p) => p.name).join(', ')}
            {empty.length > EMPTY_NAMES ? ` và ${empty.length - EMPTY_NAMES} dự án khác.` : '.'}
          </p>
        )}
      </CardContent>
    </Card>
  )
}
