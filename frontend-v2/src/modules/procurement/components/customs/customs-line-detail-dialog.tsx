// bao-CR-470 — chi tiết MỘT DÒNG HÀNG (không phải một tờ khai: tệp GTT02 không có số tờ
// khai, xem doc/erp/hai-quan/02-thiet-ke-ky-thuat.md §2.2). POPUP giữa màn (đại ca chốt
// 23/09/2026 — bản đầu là ngăn kéo bên phải), đủ 32 cột của tệp gốc xếp thành 6 nhóm. Giá trị là chữ thường — bôi đen và chép được, không dùng
// ô nhập bị khóa. Chân popup có hai lối đổ ngược bộ lọc vào màn: cùng doanh nghiệp / cùng
// đối tác.
//
// bao-CR-608 (đại ca 07/10/2026): thêm nút «Sửa» (quyền `customs_price.write`) — chuyển hộp sang
// biểu mẫu sửa ngay tại chỗ — và «Xóa» (quyền `customs_price.delete`, hỏi xác nhận). Nút ẩn theo
// quyền; backend gác lại bằng `require` tương ứng.
import { Building2, CalendarSync, Handshake, Pencil } from 'lucide-react'
import { useRef, useState } from 'react'
import { toast } from 'sonner'

import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { DeleteConfirmButton } from '@/shared/ui/delete-confirm-button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Skeleton } from '@/shared/ui/skeleton'
import { TONE_CLASS } from '@/shared/ui/status-tone'
import { formatDate } from '@/shared/utils/format-date'
import { formatQuantity } from '@/shared/utils/format-money'
import { cn } from '@/shared/utils/cn'

import { useCustomsLine, useDeleteCustomsLine } from '../../hooks/use-customs'
import type { CustomsLine } from '../../types/customs'
import { formatCustomsUnit, formatUsd, formatVnd } from '../../utils/customs'
import { CustomsLineEditForm } from './customs-line-edit-form'

type FieldFormatter = (line: CustomsLine) => string

interface DetailField {
  key: string
  label: string
  format: FieldFormatter
}

function text(value: unknown): string {
  return value === null || value === undefined || value === '' ? '—' : String(value)
}

function percent(value: number | null): string {
  return value === null ? '—' : `${value}%`
}

/** bao-CR-603 — giá trị kèm nguồn: «(từ tệp)» khi lấy từ cột tùy chọn của tệp nạp, không thì «(suy ra)» / «(tính)». */
function withSource(value: string, fromFile: boolean | undefined, derivedNote: string): string {
  return value === '—' ? value : `${value} ${fromFile ? '(từ tệp)' : derivedNote}`
}

const GROUPS: { title: string; fields: DetailField[] }[] = [
  {
    title: 'Tờ khai',
    fields: [
      { key: 'reg_date', label: 'Ngày đăng ký', format: (l) => formatDate(l.reg_date) || '—' },
      { key: 'office_code', label: 'Nơi mở tờ khai', format: (l) => text(l.office_code) },
      { key: 'line_no', label: 'Số thứ tự hàng', format: (l) => text(l.line_no) },
      { key: 'import_country', label: 'Nước nhận hàng', format: (l) => text(l.import_country) },
    ],
  },
  {
    title: 'Doanh nghiệp',
    fields: [
      { key: 'importer_name', label: 'Doanh nghiệp', format: (l) => text(l.importer_name) },
      { key: 'importer_tax_code', label: 'Mã số thuế', format: (l) => text(l.importer_tax_code) },
      { key: 'partner_name', label: 'Đối tác (bên bán)', format: (l) => text(l.partner_name) },
      { key: 'origin_country', label: 'Nước xuất xứ', format: (l) => text(l.origin_country) },
    ],
  },
  {
    title: 'Hàng hóa',
    fields: [
      { key: 'product_name', label: 'Tên hàng', format: (l) => text(l.product_name) },
      { key: 'hs_code', label: 'Mã HS', format: (l) => text(l.hs_code) },
      {
        key: 'active_ingredient',
        label: 'Hoạt chất',
        format: (l) => withSource(text(l.active_ingredient), l.active_ingredient_from_file, '(suy ra)'),
      },
      {
        key: 'formulation',
        label: 'Hàm lượng / dạng',
        format: (l) => withSource(text(l.formulation), l.formulation_from_file, '(suy ra)'),
      },
      {
        key: 'quantity',
        label: 'Lượng',
        format: (l) =>
          l.quantity === null
            ? '—'
            : `${formatQuantity(l.quantity)} ${formatCustomsUnit(l.unit_code)}`.trim(),
      },
      { key: 'unit_code', label: 'Đơn vị tính', format: (l) => text(l.unit_code) },
    ],
  },
  {
    title: 'Giá',
    fields: [
      { key: 'price_usd', label: 'Đơn giá khai báo (USD)', format: (l) => formatUsd(l.price_usd) },
      { key: 'adj_price_usd', label: 'Đơn giá điều chỉnh (USD)', format: (l) => formatUsd(l.adj_price_usd) },
      { key: 'price_nt', label: 'Đơn giá nguyên tệ khai báo', format: (l) => formatUsd(l.price_nt) },
      { key: 'adj_price_nt', label: 'Đơn giá nguyên tệ điều chỉnh', format: (l) => formatUsd(l.adj_price_nt) },
      { key: 'currency', label: 'Nguyên tệ', format: (l) => text(l.currency) },
      { key: 'fx_rate', label: 'Tỷ giá nguyên tệ', format: (l) => formatUsd(l.fx_rate) },
      { key: 'usd_rate', label: 'Tỷ giá USD', format: (l) => formatUsd(l.usd_rate) },
      //  bao-CR-493 — hai cột VND theo yêu cầu phòng Thu mua: 7% tạm tính và theo thuế suất dòng.
      //  bao-CR-603 — tệp nạp có cột VND thì lấy của tệp («từ tệp»), không thì tính.
      {
        key: 'price_vnd_flat',
        label: 'Đơn giá VND (thuế NK 7%)',
        format: (l) => withSource(formatVnd(l.price_vnd_flat), l.price_vnd_flat_from_file, '(tính)'),
      },
      {
        key: 'price_vnd_line_tax',
        label: 'Đơn giá VND (theo thuế suất XNK)',
        format: (l) => withSource(formatVnd(l.price_vnd_line_tax), l.price_vnd_line_tax_from_file, '(tính)'),
      },
    ],
  },
  {
    title: 'Hợp đồng & vận chuyển',
    fields: [
      { key: 'contract_no', label: 'Số hợp đồng', format: (l) => text(l.contract_no) },
      { key: 'contract_date', label: 'Ngày hợp đồng', format: (l) => formatDate(l.contract_date) || '—' },
      { key: 'incoterm', label: 'Điều kiện giao hàng', format: (l) => text(l.incoterm) },
      {
        key: 'transport_mode',
        label: 'Phương tiện vận chuyển',
        format: (l) => text(l.transport_label || l.transport_mode),
      },
    ],
  },
  {
    title: 'Thuế',
    fields: [
      { key: 'rate_import', label: 'Thuế suất XNK', format: (l) => percent(l.rate_import) },
      { key: 'tax_import', label: 'Thuế XNK', format: (l) => formatUsd(l.tax_import) },
      { key: 'rate_vat', label: 'Thuế suất VAT', format: (l) => percent(l.rate_vat) },
      { key: 'tax_vat', label: 'Thuế VAT', format: (l) => formatUsd(l.tax_vat) },
      { key: 'rate_excise', label: 'Thuế suất TTĐB', format: (l) => percent(l.rate_excise) },
      { key: 'tax_excise', label: 'Thuế TTĐB', format: (l) => formatUsd(l.tax_excise) },
      { key: 'rate_safeguard', label: 'Thuế suất tự vệ', format: (l) => percent(l.rate_safeguard) },
      { key: 'tax_safeguard', label: 'Thuế tự vệ', format: (l) => formatUsd(l.tax_safeguard) },
      { key: 'tax_environment', label: 'Thuế môi trường', format: (l) => formatUsd(l.tax_environment) },
    ],
  },
]

interface CustomsLineDetailDialogProps {
  lineId: number | null
  onClose: () => void
  onFilterImporter: (id: number, name: string) => void
  onFilterPartner: (id: number, name: string) => void
  /** bao-CR-608 — `customs_price.write`: hiện nút «Sửa». */
  canEdit?: boolean
  /** bao-CR-608 — `customs_price.delete`: hiện nút «Xóa». */
  canDelete?: boolean
}

export function CustomsLineDetailDialog({
  lineId,
  onClose,
  onFilterImporter,
  onFilterPartner,
  canEdit = false,
  canDelete = false,
}: CustomsLineDetailDialogProps) {
  const { data, isLoading, isError } = useCustomsLine(lineId)
  //  Nhớ ĐANG SỬA dòng nào (không phải cờ true/false): mở dòng khác là tự về chế độ xem, không
  //  cần effect đặt lại.
  const [editingId, setEditingId] = useState<number | null>(null)
  const editing = data !== undefined && editingId === data.id
  const remove = useDeleteCustomsLine()
  //  Chặn bấm đúp ngay trong lượt bấm — `pending` chỉ đổi ở lượt vẽ sau (duoc-CR-317).
  const deleting = useRef(false)

  async function deleteLine(line: CustomsLine) {
    if (deleting.current) return
    deleting.current = true
    try {
      await remove.mutateAsync(line.id)
      toast.success(`Đã xóa dòng hàng ID ${line.id}`)
      onClose()
    } catch {
      //  `httpClient` đã báo lỗi bằng toast.
    } finally {
      deleting.current = false
    }
  }

  function close() {
    setEditingId(null)
    onClose()
  }

  return (
    <Dialog open={lineId !== null} onOpenChange={(open) => !open && close()}>
      {/*  Không đặt max-h / overflow lên DialogContent: overlay của Dialog đã là khung cuộn,
       *  lồng thêm khung thứ hai là con lăn chuột chết (xem ghi chú trong shared/ui/dialog.tsx). */}
      <DialogContent className="gap-0 p-0 sm:max-w-5xl">
        <DialogHeader className="border-b p-5 pr-12">
          <DialogTitle>
            {editing ? 'Sửa dòng hàng' : 'Chi tiết dòng hàng'}
            {data && <span className="ml-2 text-sm font-normal text-muted-foreground">ID {data.id}</span>}
          </DialogTitle>
          <DialogDescription>
            Một dòng hàng trong tệp GTT02 — một tờ khai có thể gồm nhiều dòng; tệp không có số tờ
            khai.
            {data && (
              <>
                {' '}
                Lô nạp #{data.batch_id}, dòng {data.source_row} của tệp gốc.
              </>
            )}
          </DialogDescription>
          {data?.date_fixed && (
            <p className="flex flex-wrap items-center gap-2 text-sm">
              <Badge className={cn(TONE_CLASS.pending)}>
                <CalendarSync />
                Đã vá ngày
              </Badge>
              <span className="text-muted-foreground">
                Ngày đăng ký trong tệp bị đảo ngày/tháng, hệ thống đã đọc lại.
              </span>
            </p>
          )}
        </DialogHeader>

        {data && editing && (
          <CustomsLineEditForm line={data} onCancel={() => setEditingId(null)} onSaved={() => setEditingId(null)} />
        )}

        <div className={cn('p-5', editing && 'hidden')}>
          {isLoading && (
            <div className="space-y-3">
              <Skeleton className="h-24 w-full" />
              <Skeleton className="h-40 w-full" />
            </div>
          )}
          {isError && (
            <p className="rounded-lg border border-dashed border-input p-4 text-center text-sm text-muted-foreground">
              Không đọc được dòng hàng này — có thể lô nạp chứa nó vừa được hoàn tác.
            </p>
          )}
          {data && (
            <div className="grid gap-3 md:grid-cols-2">
              {GROUPS.map((group) => (
                <section key={group.title} className="min-w-0 rounded-lg border p-3">
                  <h3 className="mb-2 text-sm font-semibold text-navy dark:text-foreground">
                    {group.title}
                  </h3>
                  <dl className="space-y-1.5 text-sm">
                    {group.fields.map((field) => (
                      <div key={field.key} className="grid grid-cols-[minmax(0,11rem)_minmax(0,1fr)] gap-2">
                        <dt className="text-muted-foreground">{field.label}</dt>
                        <dd className="break-words select-text">{field.format(data)}</dd>
                      </div>
                    ))}
                  </dl>
                </section>
              ))}
            </div>
          )}
        </div>

        {data && !editing && (data.importer_id || data.partner_id || canEdit || canDelete) ? (
          <DialogFooter className="flex-wrap border-t p-4 sm:justify-end">
            {canDelete && (
              <DeleteConfirmButton
                recordName={`dòng hàng ID ${data.id} — ${data.product_name}`}
                pending={remove.isPending}
                warning="Bản trước khi xóa được lưu trong nhật ký thay đổi của dòng hàng."
                onConfirm={() => deleteLine(data)}
              />
            )}
            {canEdit && (
              <Button type="button" variant="outline" onClick={() => setEditingId(data.id)}>
                <Pencil className="size-4" />
                Sửa
              </Button>
            )}
            {data.importer_id ? (
              <Button
                type="button"
                variant="outline"
                onClick={() => onFilterImporter(data.importer_id ?? 0, data.importer_name)}
              >
                <Building2 className="size-4" />
                Các lần nhập khác của doanh nghiệp này
              </Button>
            ) : null}
            {data.partner_id ? (
              <Button
                type="button"
                variant="outline"
                onClick={() => onFilterPartner(data.partner_id ?? 0, data.partner_name)}
              >
                <Handshake className="size-4" />
                Các lần nhập khác của đối tác này
              </Button>
            ) : null}
          </DialogFooter>
        ) : null}
      </DialogContent>
    </Dialog>
  )
}
