import { FileText, Paperclip, Trash2, Upload, X } from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'

import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { Button } from '@/shared/ui/button'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Skeleton } from '@/shared/ui/skeleton'
import { Textarea } from '@/shared/ui/textarea'
import { formatDate } from '@/shared/utils/format-date'
import {
  useDeletePurchaseRequestAttachment,
  usePurchaseRequestAttachments,
  usePurchaseRequestItemGroups,
  usePurchaseRequestUnits,
  useUploadPurchaseRequestAttachments,
} from '../hooks/use-purchase-request-support'
import type { SurveyRequestLine } from '../types/survey-request-detail'
import { SurveyLineStateBadge } from './document-status-badge'

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
          <LineField label="Phân loại *">
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
              <Input value={draft.item_group} disabled />
            )}
            {!!groupHint && <p className="text-xs text-muted-foreground">{groupHint}</p>}
          </LineField>

          <LineField label="Ngày yêu cầu trả kết quả">
            <DatePicker
              value={draft.result_due_date || ''}
              disabled={!editing}
              onChange={(value) => patch({ result_due_date: value })}
            />
          </LineField>

          <div className="sm:col-span-2">
            <LineField label="Chi tiết thông số kỹ thuật & chất lượng">
              <Textarea
                rows={3}
                value={draft.requirement_detail}
                disabled={!editing}
                placeholder="Kích thước, chất liệu, tiêu chuẩn, mẫu tham khảo..."
                onChange={(event) => patch({ requirement_detail: event.target.value })}
              />
            </LineField>
          </div>

          <div className="sm:col-span-2">
            <LineField label="Yêu cầu khác">
              <Textarea
                rows={3}
                value={draft.other_requirement}
                disabled={!editing}
                placeholder="Thời gian giao, đóng gói, chứng từ kèm theo..."
                onChange={(event) => patch({ other_requirement: event.target.value })}
              />
            </LineField>
          </div>

          <LineField label="Số lượng dự kiến mua">
            <Input
              type="number"
              min={0}
              step="0.001"
              value={draft.request_qty || ''}
              disabled={!editing}
              onChange={(event) => patch({ request_qty: Number(event.target.value) })}
            />
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
              <Input value={draft.uom} disabled />
            )}
          </LineField>

          <LineField label="Giá đề xuất (VNĐ)">
            <Input
              type="number"
              min={0}
              step="0.0001"
              value={draft.proposed_price || ''}
              disabled={!editing}
              onChange={(event) => patch({ proposed_price: Number(event.target.value) })}
            />
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
              <Input value={draft.pr_code} disabled />
            </LineField>
          )}

          <div className="sm:col-span-2">
            <LineAttachments
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
                  <Input value={draft.assignee_name || draft.assignee} disabled />
                )}
              </LineField>

              <LineField label="Ngày tiếp nhận">
                <Input
                  value={formatDate(draft.received_date)}
                  placeholder="Tự tính khi gán NSTM"
                  disabled
                />
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

function LineField({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <Label>{label}</Label>
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

const IMAGE_PATTERN = /\.(jpe?g|png|webp|gif)$/i

/**
 * Đính kèm của một dòng.
 *
 * Dòng CHƯA lưu thì chưa có id để gắn tệp vào, nên ảnh được giữ tạm trong bộ nhớ
 * và chỉ tải lên sau khi bấm Lưu phiếu (trang lo việc đó). Không làm vậy thì
 * người lập phải lưu phiếu trước rồi mới quay lại đính ảnh từng dòng.
 */
function LineAttachments({
  lineId,
  canManage,
  pendingFiles,
  onPendingFilesChange,
}: {
  lineId: number
  canManage: boolean
  pendingFiles: File[]
  onPendingFilesChange: (files: File[]) => void
}) {
  const inputRef = useRef<HTMLInputElement>(null)
  const { data, isLoading } = usePurchaseRequestAttachments(LINE_ATTACHMENT_ENTITY, lineId)
  const upload = useUploadPurchaseRequestAttachments(LINE_ATTACHMENT_ENTITY, lineId)
  const remove = useDeletePurchaseRequestAttachment(LINE_ATTACHMENT_ENTITY, lineId)

  // Ảnh tạm phải có URL để xem trước; tạo xong nhớ thu hồi, không thì mỗi lần
  // mở popup lại giữ thêm một bản blob trong bộ nhớ trình duyệt.
  const previews = useMemo(
    () => pendingFiles.map((file) => ({ file, url: URL.createObjectURL(file) })),
    [pendingFiles],
  )
  useEffect(
    () => () => previews.forEach((preview) => URL.revokeObjectURL(preview.url)),
    [previews],
  )

  const files = data ?? []

  return (
    <section className="rounded-lg border p-3">
      <div className="mb-3 flex items-center justify-between gap-2">
        <h4 className="flex items-center gap-2 text-sm font-semibold text-navy dark:text-foreground">
          <Paperclip className="size-4 text-primary" />
          Hình ảnh / tài liệu đính kèm
        </h4>
        {canManage && (
          <>
            <input
              ref={inputRef}
              className="hidden"
              type="file"
              multiple
              onChange={(event) => {
                const picked = Array.from(event.target.files ?? [])
                if (picked.length) {
                  if (lineId > 0) void upload.mutateAsync({ files: picked })
                  else onPendingFilesChange([...pendingFiles, ...picked])
                }
                event.target.value = ''
              }}
            />
            <Button
              variant="ghost"
              size="sm"
              disabled={upload.isPending}
              onClick={() => inputRef.current?.click()}
            >
              <Upload />
              Thêm tệp
            </Button>
          </>
        )}
      </div>

      {lineId > 0 && isLoading && <Skeleton className="h-20 w-full" />}

      {lineId <= 0 && (
        <p className="mb-2 text-xs text-muted-foreground">
          Chọn hình bây giờ — sẽ được lưu cùng khi bạn bấm Lưu.
        </p>
      )}

      {lineId > 0 && !isLoading && !files.length && (
        <p className="text-xs text-muted-foreground">Chưa có tệp nào.</p>
      )}

      <div className="flex flex-wrap gap-2">
        {files.map((file) =>
          file.content_type.startsWith('image/') || IMAGE_PATTERN.test(file.filename) ? (
            <div key={file.id} className="group relative">
              <a href={file.url} target="_blank" rel="noreferrer">
                <img
                  className="size-20 rounded-md border object-cover"
                  src={file.url}
                  alt={file.filename}
                />
              </a>
              {canManage && (
                <div className="absolute right-1 top-1 rounded-md bg-background/90 opacity-0 shadow-sm transition-opacity focus-within:opacity-100 group-hover:opacity-100">
                  <ConfirmIconButton
                    icon={Trash2}
                    title="Xóa tệp"
                    confirmTitle={`Xóa tệp ${file.filename}?`}
                    confirmDescription="Tệp sẽ bị gỡ khỏi dòng khảo sát này."
                    confirmLabel="Xóa"
                    destructive
                    disabled={remove.isPending}
                    onConfirm={() => void remove.mutateAsync(file.id)}
                  />
                </div>
              )}
            </div>
          ) : (
            <div key={file.id} className="flex items-center gap-1 rounded-md border px-2 py-1">
              <a
                className="flex items-center gap-1.5 text-sm hover:underline"
                href={file.url}
                target="_blank"
                rel="noreferrer"
              >
                <FileText className="size-4 text-muted-foreground" />
                {file.filename}
              </a>
              {canManage && (
                <ConfirmIconButton
                  icon={Trash2}
                  title="Xóa tệp"
                  confirmTitle={`Xóa tệp ${file.filename}?`}
                  confirmDescription="Tệp sẽ bị gỡ khỏi dòng khảo sát này."
                  confirmLabel="Xóa"
                  destructive
                  disabled={remove.isPending}
                  onConfirm={() => void remove.mutateAsync(file.id)}
                />
              )}
            </div>
          ),
        )}

        {previews.map((preview, index) => (
          <div key={`${preview.file.name}-${index}`} className="group relative">
            {preview.file.type.startsWith('image/') ? (
              <img
                className="size-20 rounded-md border object-cover"
                src={preview.url}
                alt={preview.file.name}
              />
            ) : (
              <div className="flex size-20 flex-col items-center justify-center gap-1 rounded-md border p-1 text-center">
                <FileText className="size-5 text-muted-foreground" />
                <span className="line-clamp-2 text-[10.5px] text-muted-foreground">
                  {preview.file.name}
                </span>
              </div>
            )}
            {canManage && (
              <Button
                variant="ghost"
                size="icon-sm"
                className="absolute right-0.5 top-0.5 bg-background/90 text-destructive hover:text-destructive"
                title="Bỏ tệp này"
                onClick={() => onPendingFilesChange(pendingFiles.filter((_, i) => i !== index))}
              >
                <X />
              </Button>
            )}
          </div>
        ))}
      </div>
    </section>
  )
}
