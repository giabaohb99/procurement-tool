import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { cn } from '@/shared/utils/cn'
import type { SurveyRequestDetail } from '../types/survey-request-detail'

interface SurveyRequestSupplierCardProps {
  data: SurveyRequestDetail
  editing: boolean
  onChange: (changes: Partial<SurveyRequestDetail>) => void
}

/** bao-CR-289: cụm NCC đề xuất tách ra thẻ riêng cho khớp bố cục YCMH
 * (`purchase-request-supplier-card.tsx`). YCBG chỉ có MỘT cụm — NCC do người
 * yêu cầu đề xuất, lưu ở ba trường phẳng suggested_supplier* thay vì object. */
export function SurveyRequestSupplierCard({
  data,
  editing,
  onChange,
}: SurveyRequestSupplierCardProps) {
  return (
    <Card className="gap-4 py-4">
      {/* Xem ghi chú về `pb-3!` ở `purchase-request-attachments-card.tsx`. */}
      <CardHeader className="min-h-9 flex flex-row items-center gap-3 border-b px-4 pb-3!">
        <CardTitle className="text-base text-navy dark:text-foreground">
          Nhà cung cấp
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-5 px-4">
        <section>
          <h4 className="mb-3 text-sm font-semibold text-navy">
            NCC do bộ phận đề xuất (nếu có)
          </h4>
          <div className="grid gap-4 sm:grid-cols-2">
            <SupplierField
              label="Tên nhà cung cấp"
              value={data.suggested_supplier}
              editable={editing}
              placeholder="Nhà cung cấp tối ưu nhất"
              onChange={(next) => onChange({ suggested_supplier: next })}
            />
            <SupplierField
              label="Mã số thuế NCC"
              value={data.suggested_supplier_tax_code}
              editable={editing}
              placeholder="Mã số thuế NCC"
              onChange={(next) => onChange({ suggested_supplier_tax_code: next })}
            />
            <div className="sm:col-span-2">
              <SupplierField
                label="Liên hệ NCC (SĐT / Email / Địa chỉ...)"
                value={data.suggested_supplier_contact}
                editable={editing}
                placeholder="Thông tin liên hệ nhà cung cấp"
                onChange={(next) => onChange({ suggested_supplier_contact: next })}
              />
            </div>
          </div>
        </section>
      </CardContent>
    </Card>
  )
}

function SupplierField({
  label,
  value,
  editable,
  placeholder,
  onChange,
}: {
  label: string
  value?: string
  editable: boolean
  placeholder: string
  onChange: (value: string) => void
}) {
  return (
    <div className="space-y-1.5">
      <Label>{label}</Label>
      {editable ? (
        <Input
          value={value ?? ''}
          placeholder={placeholder}
          onChange={(event) => onChange(event.target.value)}
        />
      ) : (
        <ReadOnlyValue className={cn(!value && 'text-muted-foreground')}>
          {value || placeholder}
        </ReadOnlyValue>
      )}
    </div>
  )
}
