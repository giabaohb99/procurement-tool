import { useState } from 'react'
import { CircleAlert, Plus, Save, Trash2 } from 'lucide-react'

import { usePermission } from '@/core/authorization/use-permission'
import { useCrudTabDraft } from '@/shared/crud'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { useLeaveTypeQuotas, useReplaceLeaveTypeQuotas } from '../hooks/use-leave'
import { LEAVE_QUOTA_BASIS, type LeaveTypeQuotaRule } from '../types/leave'
import {
  QUOTA_BASIS_LABELS,
  describeQuotaRule,
  quotaValueOptions,
  upsertQuotaRule,
} from '../utils/leave-quota-rules'

interface LeaveTypeQuotaCardProps {
  leaveTypeId: number
}

/**
 * HẠN MỨC THEO NHÓM của một loại nghỉ (duoc-CR-715) — chép ý Leave Policy của ERPNext.
 *
 * Thứ tự áp lúc CẤP quỹ: hình thức nhân viên → cấp bậc → "Hạn mức mỗi năm" của loại nghỉ.
 * Danh sách sửa trên bản nháp rồi bấm Lưu một lần (backend thay cả danh sách). Quỹ đã cấp không đổi.
 * Bản nháp giữ bằng `useCrudTabDraft` để sống qua lượt đổi tab của trang chi tiết loại nghỉ (review M4
 * của duoc-CR-717 — Radix hủy mount tab ẩn).
 */
export function LeaveTypeQuotaCard({ leaveTypeId }: LeaveTypeQuotaCardProps) {
  const { can } = usePermission()
  const canWrite = can('leave_type', 'write')
  const { data, isLoading } = useLeaveTypeQuotas(leaveTypeId)
  const save = useReplaceLeaveTypeQuotas(leaveTypeId)

  //  `draft` = bản đang sửa dở; null = chưa đụng gì, hiện thẳng bản từ máy chủ.
  const [draft, setDraft] = useCrudTabDraft<LeaveTypeQuotaRule[]>(`leave-type-quotas:${leaveTypeId}`)
  const rules = draft ?? data?.items ?? []
  const dirty = draft !== null
  const [basis, setBasis] = useState<number>(LEAVE_QUOTA_BASIS.EMPLOYMENT_TYPE)
  const [basisValue, setBasisValue] = useState(0)
  const [quotaDays, setQuotaDays] = useState(12)
  const [error, setError] = useState<string | null>(null)

  const addRule = () => {
    const result = upsertQuotaRule(rules, {
      basis,
      basis_value: basisValue,
      quota_days: quotaDays,
    })
    setError(result.error)
    if (result.error) return
    setDraft(result.rules)
  }

  const removeRule = (rule: LeaveTypeQuotaRule) => {
    setDraft(rules.filter((r) => !(r.basis === rule.basis && r.basis_value === rule.basis_value)))
  }

  const saveAll = () => {
    save.mutate(rules, { onSuccess: () => setDraft(null) })
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Hạn mức theo nhóm</CardTitle>
        <p className="text-sm text-muted-foreground">
          Khi cấp quỹ năm, hệ thống tìm dòng khớp <strong>hình thức nhân viên</strong> trước, không có
          thì tìm theo <strong>cấp bậc</strong>, không có nữa thì dùng <strong>Hạn mức mỗi năm</strong> của loại nghỉ.
          Quỹ đã cấp cho người nào thì giữ nguyên, chỉ áp cho lần cấp sau.
        </p>
      </CardHeader>

      <CardContent className="space-y-4">
        {isLoading ? (
          <p className="text-sm text-muted-foreground">Đang tải…</p>
        ) : rules.length === 0 ? (
          <p className="rounded-md border border-dashed p-4 text-sm text-muted-foreground">
            Chưa khai nhóm nào — mọi người nhận đúng hạn mức mỗi năm của loại nghỉ.
          </p>
        ) : (
          <ul className="divide-y rounded-md border">
            {rules.map((rule) => (
              <li
                key={`${rule.basis}-${rule.basis_value}`}
                className="flex items-center gap-3 px-3 py-2 text-sm"
              >
                <span className="flex-1">{describeQuotaRule(rule)}</span>
                <span className="font-semibold text-primary">{rule.quota_days} ngày/năm</span>
                {canWrite && (
                  <Button
                    variant="ghost"
                    size="icon"
                    aria-label={`Xóa ${describeQuotaRule(rule)}`}
                    onClick={() => removeRule(rule)}
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
            <div className="grid grid-cols-1 items-end gap-3 sm:grid-cols-4">
              <div className="space-y-1">
                <Label>Theo</Label>
                <Select
                  value={String(basis)}
                  onValueChange={(v) => {
                    setBasis(Number(v))
                    setBasisValue(0)
                  }}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(QUOTA_BASIS_LABELS).map(([value, text]) => (
                      <SelectItem key={value} value={value}>
                        {text}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label>Nhóm</Label>
                <Select
                  value={basisValue ? String(basisValue) : undefined}
                  onValueChange={(v) => setBasisValue(Number(v))}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Chọn nhóm" />
                  </SelectTrigger>
                  <SelectContent>
                    {quotaValueOptions(basis).map((option) => (
                      <SelectItem key={option.value} value={String(option.value)}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1">
                <Label htmlFor="quota-days">Số ngày mỗi năm</Label>
                <Input
                  id="quota-days"
                  type="number"
                  min={0}
                  max={366}
                  step={0.5}
                  value={quotaDays}
                  onChange={(e) => setQuotaDays(Number(e.target.value))}
                />
              </div>
              <Button variant="outline" onClick={addRule}>
                <Plus className="mr-1 size-4" />
                Thêm dòng
              </Button>
            </div>
            {error && <p className="mt-2 text-xs text-destructive">{error}</p>}
            <div className="mt-3 flex items-center justify-between gap-3">
              <p className="text-xs text-muted-foreground">
                Thêm trùng nhóm thì ghi đè dòng cũ. Bấm <strong>Lưu hạn mức</strong> để áp dụng.
              </p>
              <div className="flex flex-wrap items-center gap-3">
                {dirty && (
                  <span role="status" className="flex items-center gap-1 text-xs font-medium text-warning">
                    <CircleAlert className="size-3.5" />
                    Có thay đổi chưa lưu
                  </span>
                )}
                <Button type="button" onClick={saveAll} disabled={!dirty || save.isPending}>
                  <Save className="mr-1 size-4" />
                  Lưu hạn mức
                </Button>
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
