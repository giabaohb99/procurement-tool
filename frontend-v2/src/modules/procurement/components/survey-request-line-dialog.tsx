import { useState } from 'react'

import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { Button } from '@/shared/ui/button'
import { DatePicker } from '@/shared/ui/date-picker'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { RequiredMark } from '@/shared/ui/required-mark'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Textarea } from '@/shared/ui/textarea'
import { formatDate } from '@/shared/utils/format-date'
import { formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'
import {
  usePurchaseRequestItemGroups,
  usePurchaseRequestUnits,
} from '../hooks/use-purchase-request-support'
import type { SurveyRequestLine } from '../types/survey-request-detail'
import { SurveyLineStateBadge } from './document-status-badge'
import { LineAttachments } from './line-attachments'

/** Đính kèm của dòng khảo sát nằm dưới entity riêng, không chung với đầu phiếu. */
const LINE_ATTACHMENT_ENTITY = 'survey_request_line'

const UNASSIGNED = '__unassigned__'
const EMPTY_CATALOG_VALUE = '__empty__'

interface SurveyRequestLineDialogProps {
  line: SurveyRequestLine | null
  lineNumber: number
  open: boolean
  editing: boolean
  showNstmFields: boolean
  showStatus: boolean
  canAssignNstm: boolean
  purchasers: { code: string; name: string }[]
  /** Ảnh chọn trước khi dòng được lưu — trang giữ hộ, lưu xong mới tải lên. */
  pendingFiles: File[]
  onPendingFilesChange: (files: File[]) => void
  onOpenChange: (open: boolean) => void
  onChange: (line: SurveyRequestLine) => void
  onAssigneeChange: (line: SurveyRequestLine, assignee: string) => void
}

/**
 * Popup chi tiết một dòng cần khảo sát — chứa các trường không đặt vừa trên
 * bảng ngang: yêu cầu khác, đính kèm, và khối thông tin nội bộ của thu mua.
 */
export function SurveyRequestLineDialog({
  line,
  lineNumber,
  open,
  editing,
  showNstmFields,
  showStatus,
  canAssignNstm,
  purchasers,
  pendingFiles,
  onPendingFilesChange,
  onOpenChange,
  onChange,
  onAssigneeChange,
}: SurveyRequestLineDialogProps) {
  const [draft, setDraft] = useState<SurveyRequestLine | null>(line)
  const units = usePurchaseRequestUnits(editing)
  const itemGroups = usePurchaseRequestItemGroups(editing)

  // Mở dòng khác (hoặc dữ liệu dòng đổi) -> nạp lại bản nháp đang sửa.
  // Gọi hook ra biến riêng: `||` sẽ short-circuit, làm hook thứ hai không chạy.
  const lineChanged = useHasChanged(line)
  const openChanged = useHasChanged(open)
  if ((lineChanged || openChanged) && open) setDraft(line)

  if (!draft) return null

  function patch(changes: Partial<SurveyRequestLine>) {
    setDraft((current) => (current ? { ...current, ...changes } : current))
  }

  /** Mô tả thời gian chuẩn của phân loại — chỉ để người lập ước lượng ngày trả KQ. */
  function groupDescription(name: string) {
    const group = itemGroups.data?.items.find((item) => item.name === name)
    if (!group) return ''
    const parts: string[] = []
    if (group.std_days) parts.push(`Hàng NCC có sẵn: ${group.std_days} ngày`)
    if (group.std_days_unavail) parts.push(`không sẵn: ${group.std_days_unavail} ngày`)
    return parts.join(' · ')
  }

  const groupHint = groupDescription(draft.item_group)

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[92dvh] overflow-y-auto sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>Chi tiết dòng #{lineNumber}</DialogTitle>
          <DialogDescription>
            Mô tả càng rõ thì nhân sự thu mua càng khảo sát đúng thứ bạn cần.
          </DialogDescription>
        </DialogHeader>

        <div className="grid gap-4 sm:grid-cols-2">
          <LineField label="Phân loại" required>
            {editing ? (
              <CatalogSelect
                value={draft.item_group}
                placeholder="-- Phân loại --"
                options={(itemGroups.data?.items ?? []).map((group) => ({
                  value: group.name,
                  label: group.name,
                }))}
                onChange={(value) => patch({ item_group: value })}
              />
            ) : (
              <ReadOnlyValue>{draft.item_group}</ReadOnlyValue>
            )}
            {!!groupHint && <p className="text-xs text-muted-foreground">{groupHint}</p>}
          </LineField>

          <LineField label="Ngày yêu cầu trả kết quả">
            {editing ? (
              <DatePicker
                value={draft.result_due_date || ''}
                onChange={(value) => patch({ result_due_date: value })}
              />
            ) : (
              <ReadOnlyValue className="tabular-nums">
                {formatDate(draft.result_due_date)}
              </ReadOnlyValue>
            )}
          </LineField>

          <div className="sm:col-span-2">
            <LineField label="Chi tiết thông số kỹ thuật & chất lượng">
              {editing ? (
                <Textarea
                  rows={3}
                  value={draft.requirement_detail}
                  placeholder="Kích thước, chất liệu, tiêu chuẩn, mẫu tham khảo..."
                  onChange={(event) => patch({ requirement_detail: event.target.value })}
                />
              ) : (
                <ReadOnlyValue multiline>{draft.requirement_detail}</ReadOnlyValue>
              )}
            </LineField>
          </div>

          <div className="sm:col-span-2">
            <LineField label="Yêu cầu khác">
              {editing ? (
                <Textarea
                  rows={3}
                  value={draft.other_requirement}
                  placeholder="Thời gian giao, đóng gói, chứng từ kèm theo..."
                  onChange={(event) => patch({ other_requirement: event.target.value })}
                />
              ) : (
                <ReadOnlyValue multiline>{draft.other_requirement}</ReadOnlyValue>
              )}
            </LineField>
          </div>

          <LineField label="Số lượng dự kiến mua">
            {editing ? (
              <Input
                type="number"
                min={0}
                step="0.001"
                value={draft.request_qty || ''}
                onChange={(event) => patch({ request_qty: Number(event.target.value) })}
              />
            ) : (
              <ReadOnlyValue className="tabular-nums">
                {formatQuantity(draft.request_qty)}
              </ReadOnlyValue>
            )}
          </LineField>

          <LineField label="ĐVT">
            {editing ? (
              <CatalogSelect
                value={draft.uom}
                placeholder="-- ĐVT --"
                options={(units.data?.items ?? []).map((unit) => ({
                  value: unit.name,
                  label: unit.name,
                }))}
                onChange={(value) => patch({ uom: value })}
              />
            ) : (
              <ReadOnlyValue>{draft.uom}</ReadOnlyValue>
            )}
          </LineField>

          <LineField label="Giá đề xuất (VNĐ)">
            {editing ? (
              <Input
                type="number"
                min={0}
                step="0.0001"
                value={draft.proposed_price || ''}
                onChange={(event) => patch({ proposed_price: Number(event.target.value) })}
              />
            ) : (
              <ReadOnlyValue className="tabular-nums">
                {formatUnitPrice(draft.proposed_price)}
              </ReadOnlyValue>
            )}
          </LineField>

          {showStatus && (
            <LineField label="Trạng thái">
              <div className="flex min-h-9 flex-wrap items-center gap-2">
                <SurveyLineStateBadge state={draft.progress_state} tone={draft.progress_tone} />
                <span className="text-xs text-muted-foreground">
                  {draft.option_count} phương án{draft.has_chosen ? ', đã chọn' : ''}
                </span>
              </div>
            </LineField>
          )}

          {!!draft.pr_code && (
            <LineField label="Mã YCMH liên kết">
              <ReadOnlyValue>{draft.pr_code}</ReadOnlyValue>
            </LineField>
          )}

          <div className="sm:col-span-2">
            <LineAttachments
              entity={LINE_ATTACHMENT_ENTITY}
              lineId={draft.id ?? 0}
              canManage={editing}
              pendingFiles={pendingFiles}
              onPendingFilesChange={onPendingFilesChange}
            />
          </div>

          {showNstmFields && !!draft.id && (
            <>
              <LineField label="Nhân sự phụ trách">
                {canAssignNstm ? (
                  <Select
                    value={draft.assignee || undefined}
                    onValueChange={(value) => {
                      const assignee = value === UNASSIGNED ? '' : value
                      patch({ assignee })
                      onAssigneeChange(draft, assignee)
                    }}
                  >
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Chọn NSTM" />
                    </SelectTrigger>
                    <SelectContent>
                      {draft.assignee && (
                        <SelectItem value={UNASSIGNED} className="text-muted-foreground">
                          — Bỏ chọn —
                        </SelectItem>
                      )}
                      {purchasers.map((purchaser) => (
                        <SelectItem key={purchaser.code} value={purchaser.code}>
                          {purchaser.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                ) : (
                  <ReadOnlyValue>{draft.assignee_name || draft.assignee}</ReadOnlyValue>
                )}
              </LineField>

              <LineField label="Ngày tiếp nhận">
                <ReadOnlyValue className="tabular-nums">
                  {formatDate(draft.received_date) || (
                    <span className="font-normal text-muted-foreground">
                      Tự tính khi gán NSTM
                    </span>
                  )}
                </ReadOnlyValue>
              </LineField>
            </>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Đóng
          </Button>
          {editing && (
            <Button
              onClick={() => {
                onChange(draft)
                onOpenChange(false)
              }}
            >
              Xong
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function LineField({
  label,
  required,
  children,
}: {
  label: string
  /** Ô bắt buộc — vẽ dấu sao đỏ. Bộ trường lấy từ `utils/required-fields.ts`. */
  required?: boolean
  children: React.ReactNode
}) {
  return (
    <div className="space-y-1.5">
      <Label>
        {label}
        {required && <RequiredMark />}
      </Label>
      {children}
    </div>
  )
}

function CatalogSelect({
  value,
  placeholder,
  options,
  onChange,
}: {
  value: string
  placeholder: string
  options: { value: string; label: string }[]
  onChange: (value: string) => void
}) {
  return (
    <Select
      value={value || EMPTY_CATALOG_VALUE}
      onValueChange={(next) => onChange(next === EMPTY_CATALOG_VALUE ? '' : next)}
    >
      <SelectTrigger className="w-full">
        <SelectValue />
      </SelectTrigger>
      <SelectContent position="popper" align="start">
        <SelectItem value={EMPTY_CATALOG_VALUE}>{placeholder}</SelectItem>
        {options.map((option) => (
          <SelectItem key={option.value} value={option.value}>
            {option.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
