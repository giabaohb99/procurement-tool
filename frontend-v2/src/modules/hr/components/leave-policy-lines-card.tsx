import { useMemo, useState } from 'react'
import { CircleAlert, Plus, Save, Trash2 } from 'lucide-react'

import { usePermission } from '@/core/authorization/use-permission'
import { useCrudTabDraft } from '@/shared/crud'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { useLeaveTypes } from '../hooks/use-leave'
import { useLeavePolicyLines, useReplaceLeavePolicyLines } from '../hooks/use-leave-policy'
import { useSingleFlight } from '../hooks/use-single-flight'
import type { LeavePolicyLine } from '../types/leave-policy'
import { formatCompDays } from '../utils/format-comp-days'
import {
  POLICY_DAYS_MAX,
  buildLeaveTypeNameLookup,
  parsePolicyDays,
  upsertPolicyLine,
} from '../utils/leave-policy-display'

interface LeavePolicyLinesCardProps {
  policyId: number
}

/**
 * Thẻ "Loại nghỉ & số ngày" của một chính sách (duoc-CR-717). Sửa trên bản nháp rồi bấm Lưu một lần —
 * backend THAY cả danh sách. Chỉ liệt kê loại nghỉ CÓ trừ quỹ và KHÔNG phải loại nhận nghỉ bù: loại
 * không trừ quỹ không có dòng quỹ để cấp, còn quỹ nghỉ bù cộng từ phiếu nghỉ bù (backend 422 cả hai).
 *
 * ⚠️ Bản nháp giữ bằng `useCrudTabDraft` (không phải `useState`): thẻ nằm trong một TAB của trang chi
 * tiết, Radix hủy mount tab ẩn — sang "Thông tin" xem lại rồi quay về là mất sạch dòng vừa thêm (review M4).
 * Có nháp thì hiện "Có thay đổi chưa lưu" cạnh nút Lưu của thẻ.
 */
export function LeavePolicyLinesCard({ policyId }: LeavePolicyLinesCardProps) {
  const { can } = usePermission()
  const canWrite = can('leave_type', 'write')
  const { data, isLoading } = useLeavePolicyLines(policyId)
  const save = useReplaceLeavePolicyLines(policyId)
  const runOnce = useSingleFlight()
  //  Mọi loại (kể cả đã ngừng) để dòng cũ vẫn ra tên; ô chọn chỉ lấy loại đang dùng.
  const { data: typeData } = useLeaveTypes(false)
  const typeName = useMemo(() => buildLeaveTypeNameLookup(typeData?.items), [typeData])
  const typeOptions = useMemo(
    () =>
      (typeData?.items ?? []).filter((t) => t.is_active && t.counts_balance && !t.is_compensatory),
    [typeData],
  )

  //  `draft` = bản đang sửa dở; null = chưa đụng gì, hiện thẳng bản từ máy chủ.
  const [draft, setDraft] = useCrudTabDraft<LeavePolicyLine[]>(`leave-policy-lines:${policyId}`)
  const lines = draft ?? data?.items ?? []
  const [leaveTypeId, setLeaveTypeId] = useState(0)
  const [days, setDays] = useState('12')
  const [error, setError] = useState<string | null>(null)

  const addLine = () => {
    const annualDays = parsePolicyDays(days)
    if (annualDays === null) {
      setError('Nhập số ngày (VD 12 hoặc 12,5).')
      return
    }
    const result = upsertPolicyLine(lines, { leave_type_id: leaveTypeId, annual_days: annualDays })
    setError(result.error)
    if (!result.error) setDraft(result.lines)
  }

  const saveAll = () =>
    runOnce((release) =>
      save.mutate(lines, { onSuccess: () => setDraft(null), onSettled: release }),
    )

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Loại nghỉ & số ngày mỗi năm</CardTitle>
        <p className="text-sm text-muted-foreground">
          Sửa số ngày chỉ áp cho lần cấp quỹ sau hoặc khi phân bổ có tick Tính lại; quỹ đã cấp giữ
          nguyên. Loại nghỉ không có ở đây vẫn cấp theo hạn mức của loại nghỉ.
        </p>
      </CardHeader>

      <CardContent className="space-y-4">
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Đang tải…</p>
        ) : lines.length === 0 ? (
          <p className="rounded-md border border-dashed p-4 text-sm text-muted-foreground">
            Chưa khai loại nghỉ nào — người được phân bổ chính sách này vẫn nhận hạn mức của từng loại nghỉ.
          </p>
        ) : (
          <ul className="divide-y rounded-md border">
            {lines.map((line) => (
              <li key={line.leave_type_id} className="flex items-center gap-3 px-3 py-2 text-sm">
                <span className="flex-1">{typeName(line.leave_type_id)}</span>
                <span className="font-semibold text-primary">
                  {formatCompDays(line.annual_days)} ngày/năm
                </span>
                {canWrite && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    aria-label={`Bỏ ${typeName(line.leave_type_id)}`}
                    onClick={() => setDraft(lines.filter((l) => l.leave_type_id !== line.leave_type_id))}
                  >
                    <Trash2 className="size-4 text-destructive" />
                  </Button>
                )}
              </li>
            ))}
          </ul>
        )}

        {canWrite && (
          <div className="rounded-md border bg-muted/30 p-3">
            <div className="grid grid-cols-1 items-end gap-3 sm:grid-cols-[2fr_1fr_auto]">
              <div className="space-y-1">
                <Label htmlFor="policy-line-type">Loại nghỉ</Label>
                <Select
                  value={leaveTypeId ? String(leaveTypeId) : ''}
                  onValueChange={(v) => setLeaveTypeId(Number(v))}
                >
                  <SelectTrigger id="policy-line-type" className="w-full">
                    <SelectValue placeholder="Chọn loại nghỉ có trừ quỹ" />
                  </SelectTrigger>
                  <SelectContent>
                    {typeOptions.map((t) => (
                      <SelectItem key={t.id} value={String(t.id)}>
                        {t.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label htmlFor="policy-line-days">Số ngày mỗi năm</Label>
                {/*  Ô CHỮ + bàn phím số: `type=number` đọc "12,5" thành rỗng ở trình duyệt không theo
                     locale dấu phẩy, và ô rỗng thành 0 ngày — tự đọc bằng `parsePolicyDays`. */}
                <Input
                  id="policy-line-days"
                  type="text"
                  inputMode="decimal"
                  autoComplete="off"
                  placeholder={`0 – ${POLICY_DAYS_MAX}`}
                  value={days}
                  onChange={(e) => {
                    setDays(e.target.value)
                    setError(null)
                  }}
                  //  Enter = Thêm dòng; chặn mặc định để không bao giờ nổi lên một form cha nào đó.
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault()
                      addLine()
                    }
                  }}
                />
              </div>
              <Button type="button" variant="outline" onClick={addLine}>
                <Plus className="mr-1 size-4" />
                Thêm dòng
              </Button>
            </div>
            {error && <p className="mt-2 text-xs text-destructive">{error}</p>}
            <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
              <p className="text-xs text-muted-foreground">
                Thêm trùng loại nghỉ thì ghi đè dòng cũ. Bấm <strong>Lưu số ngày</strong> để áp dụng.
              </p>
              <div className="flex flex-wrap items-center gap-3">
                {draft !== null && (
                  <span role="status" className="flex items-center gap-1 text-xs font-medium text-warning">
                    <CircleAlert className="size-3.5" />
                    Có thay đổi chưa lưu
                  </span>
                )}
                <Button type="button" onClick={saveAll} disabled={draft === null || save.isPending}>
                  <Save className="mr-1 size-4" />
                  {/*  Không gọi là "Lưu" trần: tab "Thông tin" có nút "Lưu" của biểu mẫu. */}
                  Lưu số ngày
                </Button>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
