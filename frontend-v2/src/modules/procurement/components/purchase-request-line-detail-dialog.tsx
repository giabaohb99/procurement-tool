import { Image, Loader2, Save, Trash2, Upload } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'

import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
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
import { Skeleton } from '@/shared/ui/skeleton'
import { Textarea } from '@/shared/ui/textarea'
import { formatMoney, formatQuantity } from '@/shared/utils/format-money'
import {
  useDeletePurchaseRequestAttachment,
  usePurchaseRequestAttachments,
  useUploadPurchaseRequestAttachments,
} from '../hooks/use-purchase-request-support'
import type { PurchaseRequestItem } from '../types/purchase-request-detail'

interface PurchaseRequestLineDetailDialogProps {
  item: PurchaseRequestItem | null
  lineNumber: number
  open: boolean
  editing: boolean
  showAssignee: boolean
  canEditProgress: boolean
  canAssign: boolean
  canManageAttachments: boolean
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
  onOpenChange,
  onChange,
  onSaveOperational,
}: PurchaseRequestLineDetailDialogProps) {
  const [draft, setDraft] = useState<PurchaseRequestItem | null>(item)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (open) setDraft(item)
  }, [item, open])

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
          <LineField label="Mã vật tư *">
            <Input
              value={draft.product_code}
              disabled={!editing}
              onChange={(event) => patch({ product_code: event.target.value })}
            />
          </LineField>
          <LineField label="Tên vật tư *">
            <Textarea
              rows={2}
              value={draft.product_name}
              disabled={!editing}
              onChange={(event) => patch({ product_name: event.target.value })}
            />
          </LineField>
          <LineField label="Phân loại">
            <Input
              value={draft.item_group}
              disabled={!editing}
              onChange={(event) => patch({ item_group: event.target.value })}
            />
          </LineField>
          <LineField label="Mô tả phân loại">
            <Input value={draft.group_desc} disabled />
          </LineField>
          <LineField label="Số lượng mua *">
            <Input
              type="number"
              min={0}
              step="0.001"
              value={draft.qty || ''}
              disabled={!editing}
              onChange={(event) => patch({ qty: Number(event.target.value) })}
            />
          </LineField>
          <LineField label="Giá đề xuất (chưa VAT)">
            <Input
              type="number"
              min={0}
              step="0.0001"
              value={draft.price || ''}
              disabled={!editing}
              onChange={(event) => patch({ price: Number(event.target.value) })}
            />
          </LineField>
          <LineField label="VAT (%)">
            <Input
              type="number"
              min={0}
              value={draft.vat_pct || 0}
              disabled={!editing}
              onChange={(event) => patch({ vat_pct: Number(event.target.value) })}
            />
          </LineField>
          <LineField label="ĐVT">
            <Input
              value={draft.unit}
              disabled={!editing}
              onChange={(event) => patch({ unit: event.target.value })}
            />
          </LineField>
          <LineField label="Thành tiền (gồm VAT)">
            <Input value={lineTotal ? `${formatMoney(lineTotal)} đ` : ''} disabled />
          </LineField>
          <LineField label="Kho nhận *">
            <Input
              value={draft.warehouse}
              disabled={!editing}
              onChange={(event) => patch({ warehouse: event.target.value })}
            />
          </LineField>
          <LineField label="Ngày cần hàng *">
            <DatePicker
              value={draft.required_date}
              disabled={!editing}
              onChange={(value) => patch({ required_date: value })}
            />
          </LineField>
          <LineField label="Thời gian dự kiến có hàng">
            <DatePicker
              value={draft.expected_date}
              disabled={!canEditProgress}
              onChange={(value) => patch({ expected_date: value })}
            />
          </LineField>
          {showAssignee && (
            <LineField label="Nhân sự phụ trách">
              <Input
                value={draft.assignee}
                disabled={!canAssign}
                placeholder="Mã nhân sự thu mua"
                onChange={(event) => patch({ assignee: event.target.value })}
              />
            </LineField>
          )}
          <LineField label="Trạng thái xử lý">
            <div className="flex min-h-9 items-center gap-2">
              <Badge variant="outline">{draft.line_status || 'Chưa đặt hàng'}</Badge>
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
              <Textarea
                rows={3}
                value={draft.progress_note}
                disabled={!editing && !canEditProgress}
                onChange={(event) => patch({ progress_note: event.target.value })}
              />
            </LineField>
          </div>
          <div className="sm:col-span-2">
            <LineField label="Ghi chú khác">
              <Textarea
                rows={3}
                value={draft.note}
                disabled={!editing && !canEditProgress}
                onChange={(event) => patch({ note: event.target.value })}
              />
            </LineField>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Đóng
          </Button>
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

function LineField({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <Label>{label}</Label>
      {children}
    </div>
  )
}

function LineImageGallery({
  title,
  entity,
  entityId,
  fallbackUrl,
  canManage,
}: {
  title: string
  entity: string
  entityId: number
  fallbackUrl?: string
  canManage?: boolean
}) {
  const inputRef = useRef<HTMLInputElement>(null)
  const { data, isLoading } = usePurchaseRequestAttachments(entity, entityId)
  const upload = useUploadPurchaseRequestAttachments(entity, entityId)
  const remove = useDeletePurchaseRequestAttachment(entity, entityId)
  const images = (data ?? []).filter(
    (file) => file.content_type.startsWith('image/') || /\.(jpe?g|png|webp|gif)$/i.test(file.filename),
  )

  return (
    <section className="rounded-lg border p-3">
      <div className="mb-3 flex items-center justify-between gap-2">
        <h4 className="flex items-center gap-2 text-sm font-semibold text-navy dark:text-foreground">
          <Image className="size-4 text-primary" />
          {title}
        </h4>
        {canManage && entityId > 0 && (
          <>
            <input
              ref={inputRef}
              className="hidden"
              type="file"
              accept="image/*"
              multiple
              onChange={(event) => {
                const files = Array.from(event.target.files ?? [])
                if (files.length) void upload.mutateAsync({ files })
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
              Thêm ảnh
            </Button>
          </>
        )}
      </div>
      {isLoading && entityId > 0 && <Skeleton className="h-20 w-full" />}
      {!isLoading && !images.length && fallbackUrl && (
        <a href={fallbackUrl} target="_blank" rel="noreferrer">
          <img className="size-20 rounded-md border object-cover" src={fallbackUrl} alt={title} />
        </a>
      )}
      {!isLoading && !images.length && !fallbackUrl && (
        <p className="text-xs text-muted-foreground">Chưa có ảnh.</p>
      )}
      {!!images.length && (
        <div className="flex flex-wrap gap-2">
          {images.map((file) => (
            <div key={file.id} className="group relative">
              <a href={file.url} target="_blank" rel="noreferrer">
                <img
                  className="size-20 rounded-md border object-cover"
                  src={file.url}
                  alt={file.filename}
                />
              </a>
              {canManage && (
                <div className="absolute right-1 top-1 rounded-md bg-background/90 opacity-0 shadow-sm transition-opacity group-hover:opacity-100 focus-within:opacity-100">
                  <ConfirmIconButton
                    icon={Trash2}
                    title="Xóa ảnh"
                    confirmTitle={`Xóa ảnh ${file.filename}?`}
                    confirmDescription="Ảnh đối chiếu sẽ bị gỡ khỏi dòng sản phẩm."
                    confirmLabel="Xóa"
                    destructive
                    disabled={remove.isPending}
                    onConfirm={() => void remove.mutateAsync(file.id)}
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </section>
  )
}
