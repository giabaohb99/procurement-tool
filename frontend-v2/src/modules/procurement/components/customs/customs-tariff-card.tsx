import { cn } from '@/shared/utils/cn'

import type { CustomsTariffRow } from '../../types/customs'

type TariffRate = string | number | null | undefined

/** Thuế suất để nguyên chữ của biểu thuế (có dòng ghi "*", "5 (a)"…) — trống là gạch ngang. */
function formatRate(value: TariffRate): string {
  return value === null || value === undefined || value === '' ? '—' : String(value)
}

function hasRate(value: TariffRate): boolean {
  return value !== null && value !== undefined && value !== ''
}

interface CustomsTariffCardProps {
  row: CustomsTariffRow
  /**
   * Bộ hiệp định cần bày (thẻ của bảng "Thuế suất theo FTA"). Không truyền = thẻ của bảng biểu
   * thuế chính: mô tả · ĐVT · thông thường / MFN / VAT · chính sách.
   */
  ftaKeys?: string[]
}

/**
 * Một MÃ HS của biểu thuế ở khổ điện thoại — dùng cho cả hai bảng của mục Thuế: biểu thuế chính
 * (7 cột, ~1.100px) và bảng thuế suất theo hiệp định (1 + N cột, mỗi cột 90px — 15 hiệp định là
 * ~1.500px).
 *
 * ⚠️ **Mô tả lên đầu, mã HS xuống dòng phụ** — cả ở thẻ FTA (bảng FTA chỉ có cột mã, nhưng ở
 * khổ hẹp không còn bảng biểu thuế nằm cạnh để dò mã ra mô tả); mã cha (4 · 6 số) chữ mờ,
 * mã lá (8 số) đậm — y như bảng: mã cha chỉ để đọc mô tả nhóm, không có thuế suất.
 *
 * ⚠️ **Thuế suất xếp lưới NHÃN – SỐ, giữ nguyên chữ của biểu thuế** ("5 (a)", "*"…): đổi sang
 * số là mất phần ghi chú. Mã cha không có thuế suất nào thì bỏ hẳn lưới, không in ba gạch ngang.
 */
export function CustomsTariffCard({ row, ftaKeys }: CustomsTariffCardProps) {
  const isLeaf = row.hs_code.length >= 8
  const rates = ftaKeys
    ? ftaKeys.map((key) => ({ label: key, value: row.fta?.[key] }))
    : [
        { label: 'Thông thường', value: row.rate_normal },
        { label: 'Ưu đãi (MFN)', value: row.rate_mfn },
        { label: 'VAT', value: row.rate_vat },
      ]
  const showRates = rates.some((rate) => hasRate(rate.value))

  return (
    <div className="space-y-1.5">
      {row.name_vn && (
        <p className={cn('break-words', isLeaf ? 'font-medium text-foreground' : 'text-muted-foreground')}>
          {row.name_vn}
        </p>
      )}
      <p className="text-xs text-muted-foreground">
        <span className={cn('tabular-nums', isLeaf && 'font-semibold text-foreground')}>
          HS {row.hs_code}
        </span>
        {!ftaKeys && row.unit && <span> · ĐVT {row.unit}</span>}
      </p>

      {showRates && (
        <dl className="grid grid-cols-2 gap-x-4 gap-y-0.5 text-xs">
          {rates.map((rate) => (
            <div key={rate.label} className="flex justify-between gap-2">
              <dt className="text-muted-foreground">{rate.label}</dt>
              <dd className="text-right tabular-nums">{formatRate(rate.value)}</dd>
            </div>
          ))}
        </dl>
      )}

      {!ftaKeys && row.policy && <p className="text-xs break-words">{row.policy}</p>}
    </div>
  )
}
