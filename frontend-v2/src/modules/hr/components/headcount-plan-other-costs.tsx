import { AlertCircle, Lock, Plus } from 'lucide-react'

import { COST_CALC_METHOD_CODE } from '@/shared/constants/statuses'
import { Button } from '@/shared/ui/button'
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '@/shared/ui/dropdown-menu'
import type { HrCostGroup, HrCostItem } from '../types/hr-cost'
import { OTHER_COST_KINDS, buildOtherCostItem, type OtherCostKind } from '../utils/hr-cost-item-presets'
import { listOtherCostProblems } from '../utils/hr-cost-item-validation'
import { HeadcountPlanOtherCostRow } from './headcount-plan-other-cost-row'

interface HeadcountPlanOtherCostsProps {
  items: readonly HrCostItem[]
  onChange: (items: HrCostItem[]) => void
  groups: readonly HrCostGroup[]
  positions: readonly { id: number; name: string }[]
  periodMonths: readonly number[]
  periodLabel: string
  /** Chi phí của mẫu gợi ý không đưa vào vì tháng chi nằm ngoài kỳ. */
  skipped: readonly string[]
  showMoney: boolean
  readOnly: boolean
  /** Có câu này = trang sửa được nhưng người này KHÔNG được sửa chi phí (backend 403) — chỉ xem, kèm lý do. */
  lockedReason?: string
  /** Câu lỗi kiểm hợp lệ của máy chủ (422 từ `/compute`). */
  serverError?: string
}

/**
 * Khối ② CHI PHÍ KHÁC (duoc-CR-690) — mọi khoản không phải «tiền / người / tháng» (cách tính 2…5), mỗi
 * khoản MỘT câu sửa tại chỗ. Mã, nhóm, nguồn thực tế, áp cho, thứ tự: hệ thống tự đặt, không hiện.
 */
export function HeadcountPlanOtherCosts({
  items,
  onChange,
  groups,
  positions,
  periodMonths,
  periodLabel,
  skipped,
  showMoney,
  readOnly,
  lockedReason,
  serverError,
}: HeadcountPlanOtherCostsProps) {
  const editable = !readOnly && !lockedReason
  const rows = items.map((item, index) => ({ item, index })).filter((r) => r.item.calc_method !== COST_CALC_METHOD_CODE.PER_HEAD_MONTH)
  const patch = (index: number, p: Partial<HrCostItem>) => onChange(items.map((it, k) => (k === index ? { ...it, ...p } : it)))
  const add = (kind: OtherCostKind) => onChange([...items, buildOtherCostItem(kind, { items, groups, periodMonths })])

  return (
    <div className="space-y-2">
      {serverError && (
        <p className="flex items-start gap-2 rounded-md border border-destructive/40 bg-destructive/5 p-2 text-sm text-destructive">
          <AlertCircle className="mt-0.5 size-4 shrink-0" />
          <span>{serverError}</span>
        </p>
      )}
      {!readOnly && lockedReason && (
        <p className="flex items-start gap-2 rounded-md border border-dashed bg-muted/40 p-2 text-xs text-muted-foreground">
          <Lock className="mt-0.5 size-3.5 shrink-0" />
          <span>{lockedReason}</span>
        </p>
      )}
      {skipped.length > 0 && (
        <p className="rounded-md border border-amber-300 bg-amber-50 p-2 text-xs text-amber-800 dark:bg-amber-950/30 dark:text-amber-300">
          Không đưa vào vì tháng chi nằm ngoài kỳ {periodLabel}: {skipped.join(', ')}.
        </p>
      )}
      {rows.length === 0 ? (
        <p className="rounded-md border border-dashed p-4 text-center text-sm text-muted-foreground">
          {editable
            ? 'Chưa có chi phí nào ngoài lương. Bấm Thêm chi phí — ví dụ bảo hiểm, thưởng tháng 13, quà 8/3.'
            : 'Không có chi phí nào ngoài lương.'}
        </p>
      ) : (
        <ul className="divide-y rounded-md border">
          {rows.map(({ item, index }) => {
            const others = items.filter((_, k) => k !== index)
            return (
              <HeadcountPlanOtherCostRow
                key={`${index}-${item.code}`}
                item={item}
                others={others}
                positions={positions}
                periodMonths={periodMonths}
                problems={editable ? listOtherCostProblems(item, others, { periodMonths, showMoney }) : []}
                editable={editable}
                showMoney={showMoney}
                onChange={(p) => patch(index, p)}
              />
            )
          })}
        </ul>
      )}
      {editable && (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button type="button" size="sm" variant="outline">
              <Plus className="size-4" />
              Thêm chi phí
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="start" className="w-72">
            {OTHER_COST_KINDS.map((k) => (
              <DropdownMenuItem key={k.kind} className="flex-col items-start gap-0" onSelect={() => add(k.kind)}>
                <span className="font-medium">{k.label}</span>
                <span className="text-xs text-muted-foreground">{k.hint}</span>
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
      )}
    </div>
  )
}
