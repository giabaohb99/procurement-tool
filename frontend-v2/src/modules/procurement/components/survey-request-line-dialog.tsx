import { useState } from 'react'

import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { Button } from '@/shared/ui/button'
import { CopyButton } from '@/shared/ui/copy-button'
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
import { formatMoney, formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'
import type { ProductOption } from '../api/purchase-request-support-api'
import {
  usePurchaseRequestItemGroups,
  usePurchaseRequestUnits,
  usePurchaseRequestWarehouses,
} from '../hooks/use-purchase-request-support'
import { VAT_OPTIONS } from '../types/purchase-request-detail'
import type { SurveyRequestLine } from '../types/survey-request-detail'
import { SurveyLineStateBadge } from './document-status-badge'
import { LineAttachments } from './line-attachments'
import { LineImageGallery } from './line-image-gallery'
import { PurchaseRequestProductPicker } from './purchase-request-product-picker'

/** Đính kèm của dòng khảo sát nằm dưới entity riêng, không chung với đầu phiếu. */
const LINE_ATTACHMENT_ENTITY = 'survey_request_line'
/** Ảnh gốc của sản phẩm nằm ở danh mục, không phải ở dòng — chỉ xem, không sửa tại đây. */
const PRODUCT_IMAGE_ENTITY = 'product'

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
  /**
   * bao-CR-291: quyền đính kèm TÁCH khỏi `editing`. Buộc hai thứ vào nhau thì phiếu
   * gửi duyệt xong là không ai gắn được ảnh NCC gửi về — đúng lúc cần đính nhất.
   */
  canManageAttachments: boolean
  /** Có quyền xem danh mục sản phẩm — thiếu thì khối ảnh gốc gọi API là ăn 403. */
  canViewProductImages: boolean
  onOpenChange: (open: boolean) => void
  onChange: (line: SurveyRequestLine) => void
  onAssigneeChange: (line: SurveyRequestLine, assignee: string) => void
  /**
   * bao-CR-289: NSTM/quản lý sửa được Ngày dự kiến có hàng + Chi tiết tiến độ.
   * Hai trường này KHÔNG đi qua nút Lưu phiếu — trang ghi qua endpoint
   * `lines/{id}/progress` riêng nên dialog có nút "Lưu tiến độ" riêng.
   * bao-CR-291: thêm Ghi chú thu mua vào cùng nút lưu đó.
   */
  canEditProgress?: boolean
  onProgressSave?: (
    line: SurveyRequestLine,
    progress: { expectedDate: string; progressNote: string; purchaserNote: string },
  ) => void
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
  canManageAttachments,
  canViewProductImages,
  onOpenChange,
  onChange,
  onAssigneeChange,
  canEditProgress = false,
  onProgressSave,
}: SurveyRequestLineDialogProps) {
  const [draft, setDraft] = useState<SurveyRequestLine | null>(line)
  const units = usePurchaseRequestUnits(editing)
  const itemGroups = usePurchaseRequestItemGroups(editing)
  const warehouses = usePurchaseRequestWarehouses(editing)

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

  /**
   * Chọn mã hàng (bao-CR-289) — bao-CR-291: tên sản phẩm KHÔNG còn bị nhét vào ô Chi
   * tiết thông số nữa, nó đã có ô "Tên vật tư" riêng. Ô thông số để nguyên cho người
   * lập tả thứ mình cần; dòng không chọn mã thì đó là chỗ DUY NHẤT tả được hàng.
   * Điền `product_name` tại chỗ để khỏi chờ tải lại phiếu; backend vẫn tra lại từ danh mục.
   */
  function applyProduct(product: ProductOption | null) {
    if (!product) {
      patch({ product_code: '', product_name: '', product_id: 0, product_thumbnail_url: '' })
      return
    }
    setDraft((current) =>
      current
        ? {
            ...current,
            product_code: product.code,
            product_name: product.name,
            uom: product.unit || current.uom,
            item_group: product.item_group || current.item_group,
          }
        : current,
    )
  }

  const lineTotal =
    draft.request_qty * draft.proposed_price * (1 + (draft.vat_pct || 0) / 100)

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[92dvh] overflow-y-auto sm:max-w-3xl">
        <DialogHeader>
          <DialogTitle>Chi tiết dòng #{lineNumber}</DialogTitle>
          <DialogDescription>
            Mô tả càng rõ thì nhân sự thu mua càng khảo sát đúng thứ bạn cần.
          </DialogDescription>
        </DialogHeader>

        {/* bao-CR-291: hai khối ảnh tách bạch như popup dòng YCMH — ảnh GỐC lấy từ danh
            mục sản phẩm (chỉ xem, sửa ở màn Sản phẩm), ảnh/tài liệu ĐỐI CHIẾU gắn vào
            chính dòng này. Gộp một khối thì không phân biệt được ảnh chuẩn với ảnh NCC gửi. */}
        {(canViewProductImages || !!draft.id) && (
          <div className="grid gap-4 border-b pb-5 md:grid-cols-2">
            {canViewProductImages && (
              <LineImageGallery
                title="Hình ảnh SP (gốc)"
                entity={PRODUCT_IMAGE_ENTITY}
                entityId={draft.product_id ?? 0}
                fallbackUrl={draft.product_thumbnail_url}
                emptyText={
                  draft.product_code
                    ? 'Mã hàng này chưa có ảnh trong danh mục.'
                    : 'Chọn mã hàng để xem ảnh gốc.'
                }
              />
            )}
            <LineAttachments
              entity={LINE_ATTACHMENT_ENTITY}
              lineId={draft.id ?? 0}
              canManage={canManageAttachments}
              pendingFiles={pendingFiles}
              onPendingFilesChange={onPendingFilesChange}
              title="Ảnh đối chiếu / tài liệu (thực tế)"
            />
          </div>
        )}

        <div className="grid gap-4 sm:grid-cols-2">
          <LineField label="Mã hàng">
            {editing ? (
              <div className="flex items-center gap-0.5">
                <div className="min-w-0 flex-1">
                  <PurchaseRequestProductPicker
                    code={draft.product_code}
                    name={draft.requirement_detail}
                    onPick={applyProduct}
                  />
                </div>
                <CopyButton value={draft.product_code} label="mã hàng" className="size-7" />
              </div>
            ) : (
              <ReadOnlyValue>
                {draft.product_code || (
                  <span className="font-normal text-muted-foreground">
                    Điền khi chốt phương án khảo sát
                  </span>
                )}
              </ReadOnlyValue>
            )}
          </LineField>

          {/* bao-CR-291: có mã thì tên tự lấy từ danh mục — dòng không lưu tên hàng nên
              ô này CHỈ XEM ở mọi vai trò. Không mã thì đây là chỗ nhắc người lập rằng
              mô tả hàng phải viết vào ô Chi tiết thông số bên dưới. */}
          <LineField label="Tên vật tư">
            <ReadOnlyValue>
              {draft.product_name || (
                <span className="font-normal text-muted-foreground">
                  Chưa chọn mã — mô tả hàng ở ô Chi tiết thông số
                </span>
              )}
            </ReadOnlyValue>
          </LineField>

          <LineField label="Kho nhận" required>
            {editing ? (
              <CatalogSelect
                value={draft.warehouse}
                placeholder="-- Kho --"
                options={(warehouses.data?.items ?? []).map((warehouse) => ({
                  value: warehouse.name,
                  label: warehouse.code
                    ? `${warehouse.code} - ${warehouse.name}`
                    : warehouse.name,
                }))}
                onChange={(value) => patch({ warehouse: value })}
              />
            ) : (
              <ReadOnlyValue>{draft.warehouse}</ReadOnlyValue>
            )}
          </LineField>

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

          <LineField label="Số lượng dự kiến mua" required>
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

          <LineField label="Giá đề xuất (chưa VAT)">
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

          <LineField label="VAT (%)">
            {editing ? (
              <Select
                value={String(draft.vat_pct ?? 8)}
                onValueChange={(value) => patch({ vat_pct: Number(value) })}
              >
                <SelectTrigger className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent position="popper" align="start">
                  {VAT_OPTIONS.map((vat) => (
                    <SelectItem key={vat} value={String(vat)}>
                      {vat}%
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            ) : (
              <ReadOnlyValue className="tabular-nums">{draft.vat_pct || 0}%</ReadOnlyValue>
            )}
          </LineField>

          <LineField label="Thành tiền (gồm VAT)">
            <ReadOnlyValue className="tabular-nums font-semibold text-navy">
              {formatMoney(lineTotal)}
            </ReadOnlyValue>
          </LineField>

          <LineField label="Ngày cần hàng" required>
            {editing ? (
              <DatePicker
                value={draft.required_date || ''}
                onChange={(value) => patch({ required_date: value })}
              />
            ) : (
              <ReadOnlyValue className="tabular-nums">
                {formatDate(draft.required_date)}
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

          {/* bao-CR-291: dòng lên đơn THẲNG (luồng gộp) không có YCMH nên ô trên rỗng —
              thiếu ô này thì nhìn dòng không biết nó đã thành đơn nào. Giữ ĐMH gần nhất,
              lịch sử đầy đủ nằm ở thẻ chứng từ của phiếu. */}
          {!!draft.po_code && (
            <LineField label="Mã ĐMH liên kết">
              <ReadOnlyValue>{draft.po_code}</ReadOnlyValue>
            </LineField>
          )}

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

          {/* bao-CR-289: khối tiến độ mua hàng của dòng — chỉ có nghĩa khi dòng đã lưu.
              Ngày dự kiến + chi tiết tiến độ ghi qua endpoint progress RIÊNG (không đi
              theo nút Lưu phiếu) nên có nút "Lưu tiến độ" tách hẳn. */}
          {!!draft.id && (
            <div className="sm:col-span-2 grid gap-4 rounded-md border p-3 sm:grid-cols-2">
              <LineField label="Tiến độ (nhận/đặt)">
                <ReadOnlyValue className="tabular-nums">
                  {formatQuantity(draft.qty_received)} / {formatQuantity(draft.qty_ordered)}
                </ReadOnlyValue>
              </LineField>

              <LineField label="Ngày dự kiến có hàng">
                {canEditProgress ? (
                  <DatePicker
                    value={draft.expected_date || ''}
                    onChange={(value) => patch({ expected_date: value })}
                  />
                ) : (
                  <ReadOnlyValue className="tabular-nums">
                    {formatDate(draft.expected_date)}
                  </ReadOnlyValue>
                )}
              </LineField>

              <div className="sm:col-span-2">
                <LineField label="Chi tiết tiến độ">
                  {canEditProgress ? (
                    <Textarea
                      rows={2}
                      value={draft.progress_note}
                      placeholder="Đang chờ NCC báo lịch giao, đã đặt cọc..."
                      onChange={(event) => patch({ progress_note: event.target.value })}
                    />
                  ) : (
                    <ReadOnlyValue multiline>{draft.progress_note}</ReadOnlyValue>
                  )}
                </LineField>
              </div>

              {/* bao-CR-291: ô ghi chú RIÊNG của thu mua. Ô "Yêu cầu khác" bên trên là của
                  người yêu cầu — hai bên ghi chung một ô thì bên nào lưu sau xóa mất bên kia. */}
              <div className="sm:col-span-2">
                <LineField label="Ghi chú của thu mua">
                  {canEditProgress ? (
                    <Textarea
                      rows={2}
                      value={draft.purchaser_note}
                      placeholder="NCC báo hết hàng, đề nghị đổi quy cách..."
                      onChange={(event) => patch({ purchaser_note: event.target.value })}
                    />
                  ) : (
                    <ReadOnlyValue multiline>{draft.purchaser_note}</ReadOnlyValue>
                  )}
                </LineField>
              </div>

              {canEditProgress && (
                <div className="sm:col-span-2 flex justify-end">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() =>
                      onProgressSave?.(draft, {
                        expectedDate: draft.expected_date || '',
                        progressNote: draft.progress_note || '',
                        purchaserNote: draft.purchaser_note || '',
                      })
                    }
                  >
                    Lưu tiến độ
                  </Button>
                </div>
              )}
            </div>
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
