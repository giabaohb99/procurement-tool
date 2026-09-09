import { ExternalLink } from 'lucide-react'
import { Link } from 'react-router-dom'

import type { Company } from '@/modules/hr/types/company'
import type { Employee } from '@/modules/hr/types/employee'
import type { Supplier } from '@/modules/production/types/supplier'
import { appRoutes } from '@/shared/constants/app-routes'
import { PO_DOCUMENT_STATUS, labelOf } from '@/shared/constants/statuses'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { Checkbox } from '@/shared/ui/checkbox'
import { DatePicker } from '@/shared/ui/date-picker'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { NumberInput } from '@/shared/ui/number-input'
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

import {
  CURRENCY_OPTIONS,
  DEFAULT_CURRENCY,
  isImportOrder,
  ORDER_TYPE_DOMESTIC,
  ORDER_TYPE_OPTIONS,
  PAYMENT_TERMS_OPTIONS,
  type PurchaseOrderDetail,
} from '../types/purchase-order-detail'
import { DEFAULT_PRINT_TERMS } from '../utils/purchase-order-print-terms'
import { switchOrderType } from '../utils/purchase-order-import-cost'

/** Tỷ giá nhập tới 6 số lẻ (1 JPY = 0,0065 USD kiểu vậy) — 3 số mặc định là mất. */
const EXCHANGE_RATE_MAX_DECIMALS = 6

interface PurchaseOrderInfoCardProps {
  data: PurchaseOrderDetail
  /** Đơn chưa chốt + có quyền ghi thì cho sửa phần đầu. */
  editable: boolean
  /**
   * Mã đơn MISA sửa được cả khi đơn ĐÃ DUYỆT: kế toán đẩy đơn sang phần mềm MISA
   * sau khi duyệt xong rồi mới có mã đó, khóa lại thì không ai điền vào được nữa.
   * Backend cũng cho qua (`ORDER_FIELDS_EDITABLE_AFTER_APPROVAL`).
   */
  misaEditable?: boolean
  companies?: Company[]
  /** Chỉ NCC bán hàng — đơn vị vận chuyển chọn ở từng lần giao. */
  suppliers?: Supplier[]
  employees?: Employee[]
  /** Chỉ người có quyền duyệt mới giao được NSPT phụ trách. */
  canPickNspt: boolean
  /** Id YCMH nguồn (dò theo `pr_code`) để mở nhanh phiếu gốc. */
  purchaseRequestId?: number
  onChange: (changes: Partial<PurchaseOrderDetail>) => void
  /** Hồ sơ chứng từ đổi qua endpoint riêng, sửa được cả khi đơn đã hoàn thành. */
  onDocumentStatusChange?: (value: string) => void
  documentStatusEditable?: boolean
}

/**
 * Thẻ "Thông tin chung" của ĐMH — giữ nguyên thứ tự và nhãn của bản v1
 * (`frontend/src/pages/PurchaseOrderDetail.tsx`) để người dùng khỏi học lại.
 *
 * Chọn NCC thì kéo theo VAT mặc định và hình thức thanh toán của NCC đó: hai ô
 * này gần như luôn theo hợp đồng khung, gõ lại tay là nguồn sai số.
 */
export function PurchaseOrderInfoCard({
  data,
  editable,
  misaEditable,
  companies = [],
  suppliers = [],
  employees = [],
  canPickNspt,
  purchaseRequestId,
  onChange,
  onDocumentStatusChange,
  documentStatusEditable,
}: PurchaseOrderInfoCardProps) {
  function pickSupplier(code: string) {
    const supplier = suppliers.find((option) => option.code === code)
    onChange({
      supplier_code: code,
      supplier_name: supplier?.name ?? '',
      vat_rate: supplier?.vat || data.vat_rate,
      payment_terms: supplier?.payment_terms || data.payment_terms,
      // bao-CR-321: NCC có khai điều khoản riêng thì kéo theo, không thì giữ số đang có.
      inspection_days: supplier?.inspection_days || data.inspection_days,
      return_days: supplier?.return_days || data.return_days,
      invoice_deadline: supplier?.invoice_deadline || data.invoice_deadline,
    })
  }

  const importOrder = isImportOrder(data)
  const currency = data.currency || DEFAULT_CURRENCY
  const showExchangeRate = importOrder || currency !== DEFAULT_CURRENCY
  /** Đơn cũ có thể ghi đồng tiền ngoài danh sách gợi ý — vẫn phải chọn lại được. */
  const currencyOptions = CURRENCY_OPTIONS.includes(currency)
    ? CURRENCY_OPTIONS
    : [...CURRENCY_OPTIONS, currency]

  return (
    <Card className="gap-4 py-4">
      {/* Xem ghi chú về `pb-3!` ở `purchase-request-attachments-card.tsx`. */}
      <CardHeader className="min-h-9 flex flex-row items-center gap-3 border-b px-4 pb-3!">
        <CardTitle className="text-base text-navy dark:text-foreground">
          Thông tin chung
        </CardTitle>
      </CardHeader>

      <CardContent className="grid gap-x-4 gap-y-3 px-4 md:grid-cols-2">
        <ReadOnlyField label="Mã đơn mua hàng">
          {data.code || '— (tự sinh khi tạo)'}
        </ReadOnlyField>

        <div className="space-y-1.5">
          <Label className="flex items-center gap-1.5">
            Mã YCMH nguồn
            {purchaseRequestId ? (
              <Link
                to={appRoutes.procurement.purchaseRequestDetail(purchaseRequestId)}
                className="text-primary"
                title="Mở phiếu yêu cầu mua hàng"
              >
                <ExternalLink className="size-3.5" />
              </Link>
            ) : null}
          </Label>
          {editable ? (
            <Input
              value={data.pr_code || ''}
              placeholder="Nhập mã YCMH…"
              onChange={(event) => onChange({ pr_code: event.target.value })}
            />
          ) : (
            <ReadOnlyValue>{data.pr_code || '—'}</ReadOnlyValue>
          )}
        </div>

        <div className="space-y-1.5">
          <Label>Mã đơn MISA</Label>
          {editable || misaEditable ? (
            <Input
              value={data.misa_code || ''}
              placeholder="(nếu có)"
              onChange={(event) => onChange({ misa_code: event.target.value })}
            />
          ) : (
            <ReadOnlyValue>{data.misa_code || '—'}</ReadOnlyValue>
          )}
        </div>

        <div className="space-y-1.5">
          <Label>
            Công ty nhận hóa đơn
            <RequiredMark />
          </Label>
          {editable && companies.length ? (
            <Select
              value={data.company_id ? String(data.company_id) : undefined}
              onValueChange={(value) => onChange({ company_id: Number(value) })}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Chọn công ty" />
              </SelectTrigger>
              <SelectContent>
                {/*
                  Đơn cũ có thể trỏ tới công ty đã bị xóa khỏi danh mục. Không
                  chèn dòng giữ chỗ thì ô hiện TRỐNG TRƠN — người dùng tưởng
                  chưa chọn và sửa nhầm dữ liệu lịch sử.
                */}
                {data.company_id > 0 &&
                  !companies.some((company) => company.id === data.company_id) && (
                    <SelectItem value={String(data.company_id)}>
                      #{data.company_id} — không còn trong danh mục
                    </SelectItem>
                  )}
                {companies.map((company) => (
                  <SelectItem key={company.id} value={String(company.id)}>
                    {company.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ) : (
            <ReadOnlyValue>
              {companies.find((company) => company.id === data.company_id)?.name ||
                'Chưa chọn công ty'}
            </ReadOnlyValue>
          )}
        </div>

        <div className="space-y-1.5">
          <Label>
            Nhà cung cấp bán hàng
            <RequiredMark />
          </Label>
          {editable && suppliers.length ? (
            <Select
              value={data.supplier_code || undefined}
              onValueChange={pickSupplier}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Chọn nhà cung cấp" />
              </SelectTrigger>
              <SelectContent>
                {suppliers.map((supplier) => (
                  <SelectItem key={supplier.id} value={supplier.code}>
                    {supplier.code} — {supplier.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ) : (
            <ReadOnlyValue>
              {data.supplier_name || data.supplier_code || 'Chưa chọn nhà cung cấp'}
            </ReadOnlyValue>
          )}
        </div>

        <div className="space-y-1.5">
          <Label>Ngày đặt hàng</Label>
          {editable ? (
            <DatePicker
              value={data.order_date || ''}
              onChange={(value) => onChange({ order_date: value })}
            />
          ) : (
            <ReadOnlyValue>{formatDate(data.order_date) || '—'}</ReadOnlyValue>
          )}
        </div>

        <div className="space-y-1.5">
          <Label>NSPT phụ trách</Label>
          {editable && canPickNspt && employees.length ? (
            <Select
              value={data.nspt || undefined}
              onValueChange={(value) => onChange({ nspt: value })}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Chọn nhân sự phụ trách" />
              </SelectTrigger>
              <SelectContent>
                {employees.map((employee) => (
                  <SelectItem key={employee.id} value={employee.full_name}>
                    {employee.full_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ) : (
            <ReadOnlyValue>{data.nspt || '—'}</ReadOnlyValue>
          )}
        </div>

        <div className="space-y-1.5">
          <Label>Hình thức thanh toán NCC</Label>
          {editable ? (
            <Select
              value={data.payment_terms || undefined}
              onValueChange={(value) => onChange({ payment_terms: value })}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Chọn hình thức thanh toán" />
              </SelectTrigger>
              <SelectContent>
                {PAYMENT_TERMS_OPTIONS.map((option) => (
                  <SelectItem key={option} value={option}>
                    {option}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ) : (
            <ReadOnlyValue>{data.payment_terms || '—'}</ReadOnlyValue>
          )}
        </div>

        {/* bao-CR-321: ba điều khoản in ở mục 2 và mục 5 bản in Đơn đặt hàng. 0 / rỗng
            = bản in dùng mặc định cũ; chọn NCC thì kéo theo điều khoản NCC đó khai. */}
        <div className="space-y-1.5">
          <Label>Số ngày kiểm tra hàng (bản in)</Label>
          {editable ? (
            <NumberInput
              value={data.inspection_days || 0}
              placeholder={String(DEFAULT_PRINT_TERMS.inspection_days)}
              onChange={(value) => onChange({ inspection_days: Math.max(0, Math.trunc(value)) })}
            />
          ) : (
            <ReadOnlyValue>{printDaysLabel(data.inspection_days, DEFAULT_PRINT_TERMS.inspection_days)}</ReadOnlyValue>
          )}
        </div>

        <div className="space-y-1.5">
          <Label>Số ngày thu hồi / đổi trả (bản in)</Label>
          {editable ? (
            <NumberInput
              value={data.return_days || 0}
              placeholder={String(DEFAULT_PRINT_TERMS.return_days)}
              onChange={(value) => onChange({ return_days: Math.max(0, Math.trunc(value)) })}
            />
          ) : (
            <ReadOnlyValue>{printDaysLabel(data.return_days, DEFAULT_PRINT_TERMS.return_days)}</ReadOnlyValue>
          )}
        </div>

        <div className="space-y-1.5 md:col-span-2">
          <Label>Thời gian nhận hóa đơn (bản in)</Label>
          {editable ? (
            <Input
              value={data.invoice_deadline || ''}
              placeholder={DEFAULT_PRINT_TERMS.invoice_deadline}
              onChange={(event) => onChange({ invoice_deadline: event.target.value })}
            />
          ) : (
            <ReadOnlyValue>
              {data.invoice_deadline || DEFAULT_PRINT_TERMS.invoice_deadline}
            </ReadOnlyValue>
          )}
        </div>

        {/* bao-CR-319: loại đơn + đồng tiền. Đổi loại đơn kéo theo dòng hàng và chi phí
            lô hàng (xem `switchOrderType`), nên gửi cả cụm trong một lần onChange. */}
        <div className="space-y-1.5">
          <Label>Loại đơn</Label>
          {editable ? (
            <Select
              value={String(data.order_type || ORDER_TYPE_DOMESTIC)}
              onValueChange={(value) => onChange(switchOrderType(data, Number(value)))}
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {ORDER_TYPE_OPTIONS.map((option) => (
                  <SelectItem key={option.value} value={String(option.value)}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ) : (
            <ReadOnlyValue>
              {data.order_type_label ||
                ORDER_TYPE_OPTIONS.find((option) => option.value === data.order_type)?.label ||
                '—'}
            </ReadOnlyValue>
          )}
        </div>

        <div className="space-y-1.5">
          <Label>Đồng tiền</Label>
          {editable ? (
            <Select
              value={currency}
              onValueChange={(value) =>
                onChange({
                  currency: value,
                  // Về VND thì tỷ giá chỉ có thể là 1, đừng bắt người dùng sửa tay.
                  exchange_rate: value === DEFAULT_CURRENCY ? 1 : data.exchange_rate,
                })
              }
            >
              <SelectTrigger className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {currencyOptions.map((option) => (
                  <SelectItem key={option} value={option}>
                    {option}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ) : (
            <ReadOnlyValue>{currency}</ReadOnlyValue>
          )}
        </div>

        {showExchangeRate && (
          <div className="space-y-1.5">
            <Label>
              Tỷ giá (1 {currency} = ? VND)
              {importOrder && <RequiredMark />}
            </Label>
            {editable ? (
              <NumberInput
                value={data.exchange_rate || 0}
                decimals
                maxDecimals={EXCHANGE_RATE_MAX_DECIMALS}
                onChange={(value) => onChange({ exchange_rate: value })}
              />
            ) : (
              <ReadOnlyValue className="tabular-nums">{data.exchange_rate || '—'}</ReadOnlyValue>
            )}
          </div>
        )}

        {importOrder && (
          <>
            <div className="space-y-1.5">
              <Label>Số tờ khai hải quan</Label>
              {editable ? (
                <Input
                  value={data.customs_decl_no || ''}
                  placeholder="Số tờ khai"
                  onChange={(event) => onChange({ customs_decl_no: event.target.value })}
                />
              ) : (
                <ReadOnlyValue>{data.customs_decl_no || '—'}</ReadOnlyValue>
              )}
            </div>

            <div className="space-y-1.5">
              <Label>Ngày tờ khai</Label>
              {editable ? (
                <DatePicker
                  value={data.customs_decl_date || ''}
                  onChange={(value) => onChange({ customs_decl_date: value })}
                />
              ) : (
                <ReadOnlyValue>{formatDate(data.customs_decl_date) || '—'}</ReadOnlyValue>
              )}
            </div>
          </>
        )}

        <div className="space-y-1.5">
          <Label>Hồ sơ chứng từ</Label>
          {documentStatusEditable && onDocumentStatusChange ? (
            <Select
              value={data.document_status || undefined}
              onValueChange={onDocumentStatusChange}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Chọn tình trạng hồ sơ" />
              </SelectTrigger>
              <SelectContent>
                {PO_DOCUMENT_STATUS.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ) : (
            <ReadOnlyValue>{labelOf(PO_DOCUMENT_STATUS, data.document_status) || '—'}</ReadOnlyValue>
          )}
        </div>

        <div className="space-y-1.5">
          <Label>Tùy chọn đơn</Label>
          <label className="flex cursor-pointer items-center gap-2 text-sm text-destructive">
            <Checkbox
              checked={data.is_urgent}
              disabled={!editable}
              onCheckedChange={(checked) => onChange({ is_urgent: checked === true })}
            />
            Đơn gấp
          </label>
        </div>

        <div className="space-y-1.5 md:col-span-2">
          <Label>Ghi chú</Label>
          {editable ? (
            <Textarea
              rows={2}
              value={data.note || ''}
              placeholder="Ghi chú cho đơn mua hàng…"
              onChange={(event) => onChange({ note: event.target.value })}
            />
          ) : (
            <ReadOnlyValue multiline>{data.note || '—'}</ReadOnlyValue>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

/**
 * "15 ngày". Ô trống thì bày thẳng con số bản in sẽ dùng, KHÔNG chú thêm chữ
 * "Mặc định bản in" — khách đọc ra thành một trạng thái lạ chứ không ra con số
 * (09/09/2026). Số hiện ở đây luôn đúng bằng số in ra giấy.
 */
function printDaysLabel(days: number, fallback: number): string {
  return `${days > 0 ? days : fallback} ngày`
}

function ReadOnlyField({
  label,
  children,
}: {
  label: string
  children: React.ReactNode
}) {
  return (
    <div className="space-y-1.5">
      <Label className="text-muted-foreground">{label}</Label>
      <ReadOnlyValue>{children}</ReadOnlyValue>
    </div>
  )
}
