import { Loader2, Pencil, Save } from 'lucide-react'
import { useState } from 'react'

import { PR_LINE_STATUS, labelOf } from '@/shared/constants/statuses'
import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { DatePicker } from '@/shared/ui/date-picker'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { RequiredMark } from '@/shared/ui/required-mark'
import { Textarea } from '@/shared/ui/textarea'
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney, formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'
import type { PurchaseRequestItem } from '../types/purchase-request-detail'
import { LineImageGallery } from './line-image-gallery'

interface PurchaseRequestLineDetailDialogProps {
  item: PurchaseRequestItem | null
  lineNumber: number
  open: boolean
  editing: boolean
  showAssignee: boolean
  canEditProgress: boolean
  canAssign: boolean
  canManageAttachments: boolean
  /** Phiếu còn sửa nội dung được (nháp / bị trả lại) nhưng trang đang ở chế độ xem. */
  documentEditable?: boolean
  /** Bật chế độ sửa của cả phiếu; hộp thoại đang mở sẽ hóa ô nhập ngay tại chỗ. */
  onStartEditing?: () => void
  onOpenChange: (open: boolean) => void
  onChange: (item: PurchaseRequestItem) => void
  onSaveOperational: (item: PurchaseRequestItem) => Promise<void>
}

/**
 * Popup chi tiết dòng giữ lại các trường v1 không thể đặt hết trên bảng ngang:
 * mô tả phân loại, ngày cần hàng, ghi chú tiến độ và hai nhóm ảnh đối chiếu.
 */
export function PurchaseRequestLineDetailDialog({
  item,
  lineNumber,
  open,
  editing,
  showAssignee,
  canEditProgress,
  canAssign,
  canManageAttachments,
  documentEditable = false,
  onStartEditing,
  onOpenChange,
  onChange,
  onSaveOperational,
}: PurchaseRequestLineDetailDialogProps) {
  const [draft, setDraft] = useState<PurchaseRequestItem | null>(item)
  const [saving, setSaving] = useState(false)

  // Mở dòng khác (hoặc dữ liệu dòng đổi) -> nạp lại bản nháp đang sửa.
  // Gọi hook ra biến riêng: `||` sẽ short-circuit, làm hook thứ hai không chạy.
  const itemChanged = useHasChanged(item)
  const openChanged = useHasChanged(open)
  if ((itemChanged || openChanged) && open) setDraft(item)

  if (!draft) return null

  function patch(changes: Partial<PurchaseRequestItem>) {
    setDraft((current) => (current ? { ...current, ...changes } : current))
  }

  async function save() {
    if (!draft) return
    if (editing) {
      onChange(draft)
      onOpenChange(false)
      return
    }
    setSaving(true)
    try {
      await onSaveOperational(draft)
      onOpenChange(false)
    } finally {
      setSaving(false)
    }
  }

  const canSave = editing || canEditProgress || canAssign
  const lineTotal = draft.qty * draft.price * (1 + (draft.vat_pct || 0) / 100)

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[92dvh] overflow-y-auto sm:max-w-4xl">
        <DialogHeader>
          <DialogTitle>Chi tiết dòng #{lineNumber}</DialogTitle>
          <DialogDescription>
            Thông tin yêu cầu, tiến độ đặt hàng và ảnh đối chiếu của sản phẩm.
          </DialogDescription>
        </DialogHeader>

        {!!draft.id && (
          <div className="grid gap-4 border-b pb-5 md:grid-cols-2">
            <LineImageGallery
              title="Hình ảnh SP (gốc)"
              entity="product"
              entityId={draft.product_id}
              fallbackUrl={draft.product_thumbnail_url}
            />
            <LineImageGallery
              title="Ảnh đối chiếu (thực tế)"
              entity="purchase_request_line_image"
              entityId={draft.id}
              canManage={canManageAttachments}
            />
          </div>
        )}

        <div className="grid gap-4 sm:grid-cols-2">
          <LineField label="Mã vật tư" required>
            {editing ? (
              <Input
                value={draft.product_code}
                onChange={(event) => patch({ product_code: event.target.value })}
              />
            ) : (
              <ReadOnlyValue>{draft.product_code}</ReadOnlyValue>
            )}
          </LineField>
          <LineField label="Tên vật tư" required>
            {editing ? (
              <Textarea
                rows={2}
                value={draft.product_name}
                onChange={(event) => patch({ product_name: event.target.value })}
              />
            ) : (
              <ReadOnlyValue multiline>{draft.product_name}</ReadOnlyValue>
            )}
          </LineField>
          <LineField label="Phân loại">
            {editing ? (
              <Input
                value={draft.item_group}
                onChange={(event) => patch({ item_group: event.target.value })}
              />
            ) : (
              <ReadOnlyValue>{draft.item_group}</ReadOnlyValue>
            )}
          </LineField>
          <LineField label="Mô tả phân loại">
            <ReadOnlyValue>{draft.group_desc}</ReadOnlyValue>
          </LineField>
          <LineField label="Số lượng mua" required>
            {editing ? (
              <Input
                type="number"
                min={0}
                step="0.001"
                value={draft.qty || ''}
                onChange={(event) => patch({ qty: Number(event.target.value) })}
              />
            ) : (
              // Chỉ xem thì hiện số đã ngăn cách hàng nghìn — ô nhập bắt buộc để
              // số trần (2000), đọc lướt qua rất dễ nhầm bậc.
              <ReadOnlyValue className="tabular-nums">{formatQuantity(draft.qty)}</ReadOnlyValue>
            )}
          </LineField>
          <LineField label="Giá đề xuất (chưa VAT)">
            {editing ? (
              <Input
                type="number"
                min={0}
                step="0.0001"
                value={draft.price || ''}
                onChange={(event) => patch({ price: Number(event.target.value) })}
              />
            ) : (
              <ReadOnlyValue className="tabular-nums">{formatUnitPrice(draft.price)}</ReadOnlyValue>
            )}
          </LineField>
          <LineField label="VAT (%)">
            {editing ? (
              <Input
                type="number"
                min={0}
                value={draft.vat_pct || 0}
                onChange={(event) => patch({ vat_pct: Number(event.target.value) })}
              />
            ) : (
              <ReadOnlyValue className="tabular-nums">{`${draft.vat_pct || 0}%`}</ReadOnlyValue>
            )}
          </LineField>
          <LineField label="ĐVT">
            {editing ? (
              <Input
                value={draft.unit}
                onChange={(event) => patch({ unit: event.target.value })}
              />
            ) : (
              <ReadOnlyValue>{draft.unit}</ReadOnlyValue>
            )}
          </LineField>
          <LineField label="Thành tiền (gồm VAT)">
            <ReadOnlyValue className="tabular-nums">
              {lineTotal ? `${formatMoney(lineTotal)} đ` : ''}
            </ReadOnlyValue>
          </LineField>
          <LineField label="Kho nhận" required>
            {editing ? (
              <Input
                value={draft.warehouse}
                onChange={(event) => patch({ warehouse: event.target.value })}
              />
            ) : (
              <ReadOnlyValue>{draft.warehouse}</ReadOnlyValue>
            )}
          </LineField>
          <LineField label="Ngày cần hàng" required>
            {editing ? (
              <DatePicker
                value={draft.required_date}
                onChange={(value) => patch({ required_date: value })}
              />
            ) : (
              <ReadOnlyValue className="tabular-nums">
                {formatDate(draft.required_date)}
              </ReadOnlyValue>
            )}
          </LineField>
          <LineField label="Thời gian dự kiến có hàng">
            {canEditProgress ? (
              <DatePicker
                value={draft.expected_date}
                onChange={(value) => patch({ expected_date: value })}
              />
            ) : (
              <ReadOnlyValue className="tabular-nums">
                {formatDate(draft.expected_date)}
              </ReadOnlyValue>
            )}
          </LineField>
          {showAssignee && (
            <LineField label="Nhân sự phụ trách">
              {canAssign ? (
                <Input
                  value={draft.assignee}
                  placeholder="Mã nhân sự thu mua"
                  onChange={(event) => patch({ assignee: event.target.value })}
                />
              ) : (
                <ReadOnlyValue>{draft.assignee}</ReadOnlyValue>
              )}
            </LineField>
          )}
          <LineField label="Trạng thái xử lý">
            <div className="flex min-h-9 items-center gap-2">
              <Badge variant="outline">{labelOf(PR_LINE_STATUS, draft.line_status) || 'Chưa tạo đơn mua hàng'}</Badge>
              <span className="text-xs text-muted-foreground">Tự đồng bộ từ ĐMH</span>
            </div>
          </LineField>
          <LineField label="Tiến độ (nhận / đặt)">
            <p className="min-h-9 py-2 text-sm tabular-nums">
              <b className="text-emerald-600">{formatQuantity(draft.qty_received)}</b>
              <span className="text-muted-foreground">
                {' '}/ {formatQuantity(draft.qty_ordered)} {draft.unit}
              </span>
            </p>
          </LineField>
          <div className="sm:col-span-2">
            <LineField label="Chi tiết tiến độ">
              {editing || canEditProgress ? (
                <Textarea
                  rows={3}
                  value={draft.progress_note}
                  onChange={(event) => patch({ progress_note: event.target.value })}
                />
              ) : (
                <ReadOnlyValue multiline>{draft.progress_note}</ReadOnlyValue>
              )}
            </LineField>
          </div>
          <div className="sm:col-span-2">
            <LineField label="Ghi chú khác">
              {editing || canEditProgress ? (
                <Textarea
                  rows={3}
                  value={draft.note}
                  onChange={(event) => patch({ note: event.target.value })}
                />
              ) : (
                <ReadOnlyValue multiline>{draft.note}</ReadOnlyValue>
              )}
            </LineField>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Đóng
          </Button>
          {/*
            Phiếu nháp mở hộp thoại ra là chữ chết hết — người dùng đọc thành
            "hết quyền sửa". Cho bật chế độ sửa ngay tại đây: hộp thoại không
            đóng, các ô hóa ô nhập tại chỗ.
          */}
          {!editing && documentEditable && onStartEditing && (
            <Button variant="outline" onClick={onStartEditing}>
              <Pencil />
              Sửa dòng này
            </Button>
          )}
          {canSave && (
            <Button onClick={() => void save()} disabled={saving}>
              {saving ? <Loader2 className="animate-spin" /> : <Save />}
              {editing ? 'Xong' : 'Lưu dòng'}
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
