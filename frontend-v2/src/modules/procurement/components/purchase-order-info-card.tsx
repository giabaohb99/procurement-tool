import { ExternalLink } from 'lucide-react'
import { Link } from 'react-router-dom'

import type { Company } from '@/modules/hr/types/company'
import type { Employee } from '@/modules/hr/types/employee'
import type { Supplier } from '@/modules/production/types/supplier'
import { appRoutes } from '@/shared/constants/app-routes'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { Checkbox } from '@/shared/ui/checkbox'
import { DatePicker } from '@/shared/ui/date-picker'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Textarea } from '@/shared/ui/textarea'
import { formatDate } from '@/shared/utils/format-date'
import { DOCUMENT_STATUSES } from '../types/purchase-document'
import {
  PAYMENT_TERMS_OPTIONS,
  type PurchaseOrderDetail,
} from '../types/purchase-order-detail'

interface PurchaseOrderInfoCardProps {
  data: PurchaseOrderDetail
  /** Đơn chưa chốt + có quyền ghi thì cho sửa phần đầu. */
  editable: boolean
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
    })
  }

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
          {editable ? (
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
            Công ty nhận hóa đơn <span className="text-destructive">*</span>
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
            Nhà cung cấp bán hàng <span className="text-destructive">*</span>
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
                {DOCUMENT_STATUSES.map((option) => (
                  <SelectItem key={option} value={option}>
                    {option}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ) : (
            <ReadOnlyValue>{data.document_status || '—'}</ReadOnlyValue>
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
