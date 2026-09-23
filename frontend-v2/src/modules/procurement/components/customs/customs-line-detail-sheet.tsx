// bao-CR-470 — chi tiết MỘT DÒNG HÀNG (không phải một tờ khai: tệp GTT02 không có số tờ
// khai, xem doc/erp/hai-quan/02-thiet-ke-ky-thuat.md §2.2). Ngăn kéo bên phải, đủ 32 cột
// của tệp gốc xếp thành 6 nhóm. Giá trị là chữ thường — bôi đen và chép được, không dùng
// ô nhập bị khóa. Chân ngăn có hai lối đổ ngược bộ lọc vào màn: cùng doanh nghiệp / cùng
// đối tác.
import { Building2, CalendarSync, Handshake } from 'lucide-react'

import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/shared/ui/sheet'
import { Skeleton } from '@/shared/ui/skeleton'
import { TONE_CLASS } from '@/shared/ui/status-tone'
import { formatDate } from '@/shared/utils/format-date'
import { formatQuantity } from '@/shared/utils/format-money'
import { cn } from '@/shared/utils/cn'

import { useCustomsLine } from '../../hooks/use-customs'
import type { CustomsLine } from '../../types/customs'
import { formatCustomsUnit, formatUsd } from '../../utils/customs'

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

const GROUPS: { title: string; fields: DetailField[] }[] = [
  {
    title: 'Tờ khai',
    fields: [
      { key: 'reg_date', label: 'Ngày đăng ký', format: (l) => formatDate(l.reg_date) || '—' },
      { key: 'office_code', label: 'Nơi mở tờ khai', format: (l) => text(l.office_code) },
      { key: 'line_no', label: 'Số thứ tự hàng', format: (l) => text(l.line_no) },
      { key: 'import_country', label: 'Nước nhập khẩu', format: (l) => text(l.import_country) },
    ],
  },
  {
    title: 'Doanh nghiệp',
    fields: [
      { key: 'importer_name', label: 'Doanh nghiệp nhập khẩu', format: (l) => text(l.importer_name) },
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
      { key: 'active_ingredient', label: 'Hoạt chất (suy ra)', format: (l) => text(l.active_ingredient) },
      { key: 'formulation', label: 'Hàm lượng / dạng (suy ra)', format: (l) => text(l.formulation) },
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
      { key: 'rate_import', label: 'Thuế suất nhập khẩu', format: (l) => percent(l.rate_import) },
      { key: 'tax_import', label: 'Thuế nhập khẩu', format: (l) => formatUsd(l.tax_import) },
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

interface CustomsLineDetailSheetProps {
  lineId: number | null
  onClose: () => void
  onFilterImporter: (id: number, name: string) => void
  onFilterPartner: (id: number, name: string) => void
}

export function CustomsLineDetailSheet({
  lineId,
  onClose,
  onFilterImporter,
  onFilterPartner,
}: CustomsLineDetailSheetProps) {
  const { data, isLoading, isError } = useCustomsLine(lineId)

  return (
    <Sheet open={lineId !== null} onOpenChange={(open) => !open && onClose()}>
      <SheetContent side="right" className="flex w-full flex-col gap-0 sm:max-w-3xl">
        <SheetHeader className="border-b pr-12">
          <SheetTitle>Chi tiết dòng hàng</SheetTitle>
          <SheetDescription>
            Một dòng hàng trong tệp GTT02 — một tờ khai có thể gồm nhiều dòng; tệp không có số tờ
            khai.
            {data && (
              <>
                {' '}
                Lô nạp #{data.batch_id}, dòng {data.source_row} của tệp gốc.
              </>
            )}
          </SheetDescription>
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
        </SheetHeader>

        <div className="min-h-0 flex-1 overflow-y-auto p-4">
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

        {data && (data.importer_id || data.partner_id) ? (
          <div className="flex flex-wrap items-center justify-end gap-2 border-t p-4">
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
          </div>
        ) : null}
      </SheetContent>
    </Sheet>
  )
}
