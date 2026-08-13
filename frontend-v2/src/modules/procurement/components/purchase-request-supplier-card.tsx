import { usePermission } from '@/core/authorization/use-permission'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import type {
  PurchaseRequestDetail,
  SupplierCluster,
} from '../types/purchase-request-detail'

interface PurchaseRequestSupplierCardProps {
  data: PurchaseRequestDetail
  editing: boolean
  onChange: (changes: Partial<PurchaseRequestDetail>) => void
}

/** Hai nguồn NCC phải tách riêng vì quyền xem/sửa và ý nghĩa nghiệp vụ khác nhau. */
export function PurchaseRequestSupplierCard({
  data,
  editing,
  onChange,
}: PurchaseRequestSupplierCardProps) {
  const { can } = usePermission()
  const canReadPurchasingSupplier = can('supplier', 'read')
  const canWritePurchasingSupplier =
    editing && data.can_edit_supplier_pur && can('supplier', 'write')

  function patchCluster(
    key: 'supplier_req' | 'supplier_pur',
    field: keyof SupplierCluster,
    value: string,
  ) {
    onChange({
      [key]: { ...data[key], [field]: value },
    })
  }

  return (
    <Card className="gap-4 py-4">
      {/* Xem ghi chú về `pb-3!` ở `purchase-request-attachments-card.tsx`. */}
      <CardHeader className="min-h-9 flex flex-row items-center gap-3 border-b px-4 pb-3!">
        <CardTitle className="text-base text-navy dark:text-foreground">
          Nhà cung cấp
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-5 px-4">
        <SupplierFields
          title="NCC do bộ phận đề xuất (nếu có)"
          value={data.supplier_req}
          editable={editing}
          onChange={(field, value) => patchCluster('supplier_req', field, value)}
        />

        {canReadPurchasingSupplier && (
          <div className="border-t pt-5">
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <h4 className="text-sm font-semibold text-primary">
                NCC từ khảo sát / thu mua
              </h4>
              {data.supplier_from_survey && (
                <span className="text-xs text-muted-foreground">
                  Nguồn: Yêu cầu báo giá
                </span>
              )}
              {!canWritePurchasingSupplier && (
                <span className="text-xs text-muted-foreground">Chỉ xem</span>
              )}
            </div>
            <SupplierFields
              value={data.supplier_pur}
              editable={canWritePurchasingSupplier}
              onChange={(field, value) => patchCluster('supplier_pur', field, value)}
            />
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function SupplierFields({
  title,
  value,
  editable,
  onChange,
}: {
  title?: string
  value: SupplierCluster
  editable: boolean
  onChange: (field: keyof SupplierCluster, value: string) => void
}) {
  return (
    <section>
      {title && <h4 className="mb-3 text-sm font-semibold text-navy">{title}</h4>}
      <div className="grid gap-4 sm:grid-cols-2">
        <SupplierField
          label="Tên nhà cung cấp"
          value={value?.name}
          editable={editable}
          placeholder="Nhà cung cấp tối ưu nhất"
          onChange={(next) => onChange('name', next)}
        />
        <SupplierField
          label="Mã số thuế NCC"
          value={value?.tax_code}
          editable={editable}
          placeholder="Mã số thuế NCC"
          onChange={(next) => onChange('tax_code', next)}
        />
        <div className="sm:col-span-2">
          <SupplierField
            label="Liên hệ NCC (SĐT / Email / Địa chỉ...)"
            value={value?.contact}
            editable={editable}
            placeholder="Thông tin liên hệ nhà cung cấp"
            onChange={(next) => onChange('contact', next)}
          />
        </div>
      </div>
    </section>
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
        <p className="flex min-h-9 items-center rounded-lg border bg-muted/35 px-3 py-2 text-sm font-medium text-muted-foreground">
          {value || placeholder}
        </p>
      )}
    </div>
  )
}
