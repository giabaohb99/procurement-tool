import { X } from 'lucide-react'
import { useSearchParams } from 'react-router-dom'

import { useSetUrlParams } from '@/shared/hooks/use-url-param-state'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'

import { BENEFIT_PARAM, buildClearBenefitParams } from '../utils/benefit-occasion-presets'

/** Ba điều kiện chỉ đặt được qua nút dịp (không có ô nhập riêng) — hiện ra để người lập biết đang lọc gì. */
function describeConditions(params: URLSearchParams): { key: string; text: string }[] {
  const out: { key: string; text: string }[] = []
  const child = params.get(BENEFIT_PARAM.childMaxAge)
  if (child) out.push({ key: BENEFIT_PARAM.childMaxAge, text: `Tính theo con, con ≤ ${child} tuổi` })
  const month = params.get(BENEFIT_PARAM.birthMonth)
  if (month) out.push({ key: BENEFIT_PARAM.birthMonth, text: `Sinh tháng ${month}` })
  const years = params.get(BENEFIT_PARAM.seniorityYears)
  if (years) {
    const list = years.split(',').filter(Boolean).join(', ')
    out.push({ key: BENEFIT_PARAM.seniorityYears, text: `Tròn ${list} năm làm việc` })
  }
  return out
}

/**
 * Dải «Đang lọc» của H1: điều kiện dịp đặt sẵn (bấm ✕ bỏ từng cái) + nút «Bỏ hết điều kiện».
 * Nút này cũng là lối thoát khi báo cáo trả 403 vì lọc nhạy cảm (link được gửi từ người có
 * quyền): «Đặt lại bộ lọc» của thẻ lỗi chỉ đưa «Xem theo» về mặc định, không biết tới các
 * tham số riêng của trang. Mỗi nút = MỘT lượt ghi URL.
 */
export function BenefitActiveConditions() {
  const [searchParams] = useSearchParams()
  const setParams = useSetUrlParams()
  const conditions = describeConditions(searchParams)
  const hasAny = Object.values(BENEFIT_PARAM).some((k) => searchParams.has(k))
  if (!hasAny) return null

  return (
    <div className="flex flex-wrap items-center gap-2">
      {conditions.length > 0 && <span className="text-sm text-muted-foreground">Đang lọc:</span>}
      {conditions.map((c) => (
        <Badge key={c.key} variant="secondary" className="gap-1 pr-1">
          {c.text}
          <button
            type="button"
            aria-label={`Bỏ điều kiện ${c.text}`}
            className="rounded-sm opacity-60 hover:opacity-100"
            onClick={() => setParams({ [c.key]: null })}
          >
            <X className="size-3.5" aria-hidden />
          </button>
        </Badge>
      ))}
      <Button type="button" variant="ghost" size="sm" onClick={() => setParams(buildClearBenefitParams())}>
        Bỏ hết điều kiện
      </Button>
    </div>
  )
}
