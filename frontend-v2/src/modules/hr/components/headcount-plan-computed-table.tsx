import { ChevronDown, ChevronRight, Loader2 } from 'lucide-react'
import { Fragment, useState } from 'react'

import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/shared/ui/table'
import { cn } from '@/shared/utils/cn'
import { formatMoney } from '@/shared/utils/format-money'
import type { HeadcountPlanActual, HeadcountPlanComputed, HeadcountPlanPeriod } from '../types/headcount-plan'
import { HeadcountPlanActualRows } from './headcount-plan-actual-rows'

interface HeadcountPlanComputedTableProps {
  computed: HeadcountPlanComputed | null | undefined
  /** Kỳ con dựng ở giao diện — dùng làm tiêu đề cột khi bộ tính chưa trả lời. */
  periods: readonly HeadcountPlanPeriod[]
  showMoney: boolean
  isFetching: boolean
  /** Thực tế so với kế hoạch — chỉ kế hoạch ĐÃ LƯU có (không có ở bản xem trước). */
  actual?: HeadcountPlanActual | null
  /** Ghi chú dưới bảng («Thực tế chưa gồm…», «Q3 đang chạy…»). */
  notes?: readonly string[]
}

/** Ô tiền: `null` (bị che / chưa tính) hiện gạch mờ thật, không để trống. */
function Money({ value, strong }: { value: number | null | undefined; strong?: boolean }) {
  if (value == null) return <span className="text-muted-foreground/50">—</span>
  return <span className={cn('tabular-nums', strong && 'font-semibold')}>{formatMoney(value)}</span>
}

/**
 * Khối 4 — HỆ THỐNG TỰ TÍNH (chỉ đọc, tài liệu 06 §2.4). Mỗi NHÓM một dòng, bấm mở ra từng khoản;
 * dưới cùng là Tổng chi phí, Định biên cuối kỳ con, Bình quân / người. Không được xem lương thì chỉ
 * còn dòng định biên — mọi dòng tiền bị gỡ, không phải dựng toàn gạch.
 *
 * Con số là của BỘ TÍNH ở backend (`POST /compute`), giao diện không tự cộng nhân — tự cộng là sớm
 * muộn lệch với báo cáo A4 / A5 đọc cùng bộ tính đó.
 */
export function HeadcountPlanComputedTable({
  computed,
  periods,
  showMoney,
  isFetching,
  actual,
  notes = [],
}: HeadcountPlanComputedTableProps) {
  const [open, setOpen] = useState<Set<number>>(() => new Set())
  const heads = computed?.periods?.length ? computed.periods : periods
  const toggle = (groupId: number) =>
    setOpen((prev) => {
      const next = new Set(prev)
      if (next.has(groupId)) next.delete(groupId)
      else next.add(groupId)
      return next
    })

  return (
    <div className="relative overflow-x-auto rounded-md border">
      {isFetching && (
        <span className="absolute top-2 right-2 flex items-center gap-1 text-xs text-muted-foreground">
          <Loader2 className="size-3 animate-spin" />
          Đang tính…
        </span>
      )}
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="min-w-56">Khoản mục</TableHead>
            {heads.map((p) => (
              <TableHead key={p.key} className="min-w-32 text-right">
                {p.label}
              </TableHead>
            ))}
            <TableHead className="min-w-36 text-right">Tổng kỳ</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {showMoney &&
            (computed?.groups ?? []).map((g) => {
              const gid = g.group_id ?? 0
              const expanded = open.has(gid)
              const children = (computed?.items ?? []).filter((i) => (i.group_id ?? 0) === gid)
              return (
                <Fragment key={`g${gid}`}>
                  <TableRow>
                    <TableCell>
                      <button
                        type="button"
                        className="flex items-center gap-1 font-medium"
                        aria-expanded={expanded}
                        onClick={() => toggle(gid)}
                      >
                        {expanded ? <ChevronDown className="size-4" /> : <ChevronRight className="size-4" />}
                        {g.name || 'Chưa xếp nhóm'}
                      </button>
                    </TableCell>
                    {heads.map((p, i) => (
                      <TableCell key={p.key} className="text-right">
                        <Money value={g.values[i]} />
                      </TableCell>
                    ))}
                    <TableCell className="text-right">
                      <Money value={g.total} strong />
                    </TableCell>
                  </TableRow>
                  {expanded &&
                    children.map((it) => (
                      <TableRow key={`i${it.code}`} className="text-muted-foreground">
                        <TableCell className="pl-9">{it.name}</TableCell>
                        {heads.map((p, i) => (
                          <TableCell key={p.key} className="text-right">
                            <Money value={it.values[i]} />
                          </TableCell>
                        ))}
                        <TableCell className="text-right">
                          <Money value={it.total} />
                        </TableCell>
                      </TableRow>
                    ))}
                </Fragment>
              )
            })}
          {showMoney && (
            <TableRow className="bg-muted/40">
              <TableCell className="font-semibold">Tổng chi phí nhân sự</TableCell>
              {heads.map((p, i) => (
                <TableCell key={p.key} className="text-right">
                  <Money value={computed?.total?.values[i]} strong />
                </TableCell>
              ))}
              <TableCell className="text-right">
                <Money value={computed?.total?.total} strong />
              </TableCell>
            </TableRow>
          )}
          <TableRow>
            <TableCell>Định biên cuối kỳ con</TableCell>
            {heads.map((p, i) => (
              <TableCell key={p.key} className="text-right tabular-nums">
                {computed?.headcount[i] ?? ''}
              </TableCell>
            ))}
            <TableCell className="text-right tabular-nums">
              {computed?.headcount.length ? computed.headcount[computed.headcount.length - 1] : ''}
            </TableCell>
          </TableRow>
          {showMoney && (
            <TableRow>
              <TableCell>Bình quân / người</TableCell>
              {heads.map((p) => (
                <TableCell key={p.key} />
              ))}
              <TableCell className="text-right">
                <Money value={computed?.avg_per_head} />
              </TableCell>
            </TableRow>
          )}
          {actual && <HeadcountPlanActualRows actual={actual} periods={heads} showMoney={showMoney} />}
        </TableBody>
      </Table>
      {notes.length > 0 && (
        <ul className="space-y-0.5 border-t px-3 py-2 text-xs text-muted-foreground">
          {notes.map((n) => (
            <li key={n}>{n}</li>
          ))}
        </ul>
      )}
    </div>
  )
}
