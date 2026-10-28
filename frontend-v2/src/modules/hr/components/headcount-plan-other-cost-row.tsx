import { Badge } from '@/shared/ui/badge'
import { Checkbox } from '@/shared/ui/checkbox'
import { Input } from '@/shared/ui/input'
import { cn } from '@/shared/utils/cn'
import type { HrCostItem } from '../types/hr-cost'
import { describeCostItem } from '../utils/hr-cost-item-describe'
import { HeadcountPlanOtherCostSentence } from './headcount-plan-other-cost-sentence'

interface HeadcountPlanOtherCostRowProps {
  item: HrCostItem
  /** Mọi khoản KHÁC của kế hoạch (đọc «trên lương + phụ cấp», tên khoản gốc của dòng cũ). */
  others: readonly HrCostItem[]
  positions: readonly { id: number; name: string }[]
  periodMonths: readonly number[]
  problems: readonly string[]
  editable: boolean
  showMoney: boolean
  onChange: (patch: Partial<HrCostItem>) => void
}

/**
 * MỘT dòng của khối «Chi phí khác»: ô bật/tắt (tắt = bỏ khỏi kế hoạch khi lưu) · tên sửa được · câu có ô
 * số. Khoản cũ có cấu hình câu không biểu diễn được (chỉ áp vài vị trí, chi nhiều tháng…) thì đọc ra câu
 * mô tả CHỈ ĐỌC kèm nhãn «giữ nguyên» — lưu không đổi phần đó.
 */
export function HeadcountPlanOtherCostRow({
  item,
  others,
  positions,
  periodMonths,
  problems,
  editable,
  showMoney,
  onChange,
}: HeadcountPlanOtherCostRowProps) {
  const off = Boolean(item.excluded)
  const kept = Boolean(item.custom_parts?.length)
  const name = item.name.trim() || 'Chi phí chưa đặt tên'

  return (
    <li className="flex items-start gap-3 px-3 py-2">
      <Checkbox
        className="mt-2"
        checked={!off}
        disabled={!editable}
        aria-label={`Dùng ${name}`}
        title={off ? 'Đang tắt — bấm Lưu thì bỏ khỏi kế hoạch' : 'Bỏ chọn để bỏ khỏi kế hoạch'}
        onCheckedChange={(v) => onChange({ excluded: v !== true })}
      />
      <div className={cn('min-w-0 flex-1 space-y-1', off && 'opacity-50')}>
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
          {editable ? (
            <Input
              value={item.name}
              maxLength={150}
              aria-label="Tên chi phí"
              placeholder="Tên, ví dụ Quà 8/3"
              className="h-8 w-full sm:w-64"
              onChange={(e) => onChange({ name: e.target.value })}
              onKeyDown={(e) => e.key === 'Enter' && e.preventDefault()}
            />
          ) : (
            <span className="font-medium sm:w-64">{name}</span>
          )}
          {kept ? (
            <span className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
              {describeCostItem(item, [item, ...others], { showMoney, positions })}
              <Badge variant="outline" title="Cách tính riêng của kế hoạch này — lưu không đổi">
                giữ nguyên
              </Badge>
            </span>
          ) : (
            <HeadcountPlanOtherCostSentence
              item={item}
              others={others}
              periodMonths={periodMonths}
              editable={editable}
              showMoney={showMoney}
              onChange={onChange}
            />
          )}
        </div>
        {off && <p className="text-xs text-muted-foreground">Đang tắt — bấm Lưu thì bỏ khỏi kế hoạch.</p>}
        {problems.map((p) => (
          <p key={p} className="text-xs text-destructive">
            {p}
          </p>
        ))}
      </div>
    </li>
  )
}
