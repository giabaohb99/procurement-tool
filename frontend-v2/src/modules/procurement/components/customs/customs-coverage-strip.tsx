// bao-CR-470 — dải tháng đã phủ đầu màn Tra cứu giá hải quan. Chặn lỗi "quên nạp một
// tệp": mỗi lần kết xuất GTT02 bị cắt thành nhiều tệp hai tháng, sót một tệp là thấy ngay
// hai ô đỏ giữa dải. Ba trạng thái: có dữ liệu · trống · chưa tới.
import { Card } from '@/shared/ui/card'
import { Skeleton } from '@/shared/ui/skeleton'
import { formatDate } from '@/shared/utils/format-date'
import { formatQuantity } from '@/shared/utils/format-money'
import { cn } from '@/shared/utils/cn'

import type { CustomsCoverage, CustomsOptions } from '../../types/customs'
import { classifyCoverageMonth } from '../../utils/customs'

const MONTH_LABELS = ['T1', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'T8', 'T9', 'T10', 'T11', 'T12']

interface CustomsCoverageStripProps {
  coverage: CustomsCoverage | undefined
  ingredientCoverage: CustomsOptions['ingredient_coverage'] | undefined
  isLoading: boolean
}

export function CustomsCoverageStrip({
  coverage,
  ingredientCoverage,
  isLoading,
}: CustomsCoverageStripProps) {
  if (isLoading) {
    return (
      <Card className="gap-2 p-4">
        <Skeleton className="h-4 w-2/3" />
        <Skeleton className="h-5 w-full" />
      </Card>
    )
  }
  if (!coverage) return null
  if (!coverage.total) {
    return (
      <Card className="p-4 text-sm text-muted-foreground">Chưa có dữ liệu hải quan nào.</Card>
    )
  }

  const today = new Date()
  const ratio = ingredientCoverage?.ratio
  return (
    <Card className="gap-2 p-4 text-sm">
      <p>
        Dữ liệu:{' '}
        <b>
          {formatDate(coverage.date_from)} → {formatDate(coverage.date_to)}
        </b>{' '}
        · {formatQuantity(coverage.total)} dòng hàng
        {coverage.last_import_at && <> · lần nạp gần nhất {formatDate(coverage.last_import_at)}</>}
        {ratio !== null && ratio !== undefined && (
          <span className="text-muted-foreground">
            {' '}
            · nhận ra hoạt chất {Math.round(ratio * 100)}% (dòng không nhận ra vẫn tìm được bằng
            tên hàng)
          </span>
        )}
      </p>
      <div className="flex flex-col gap-1 overflow-x-auto">
        {coverage.years.map((year) => (
          <div key={year.year} className="flex items-center gap-1">
            <span className="w-10 shrink-0 text-xs text-muted-foreground">{year.year}</span>
            {year.months.map((count, index) => {
              const state = classifyCoverageMonth(year.year, index, count, today)
              const label = `${MONTH_LABELS[index]}/${year.year}: ${
                state === 'future' ? 'chưa tới' : `${count} dòng`
              }`
              return (
                <span
                  key={index}
                  title={label}
                  aria-label={label}
                  className={cn(
                    'w-11 shrink-0 rounded border py-0.5 text-center text-[11px]',
                    state === 'future' && 'border-dashed border-border text-muted-foreground/60',
                    state === 'filled' && 'border-transparent bg-info/10 text-info',
                    state === 'empty' && 'border-transparent bg-destructive/10 text-destructive',
                  )}
                >
                  {MONTH_LABELS[index]}
                </span>
              )
            })}
          </div>
        ))}
      </div>
    </Card>
  )
}
