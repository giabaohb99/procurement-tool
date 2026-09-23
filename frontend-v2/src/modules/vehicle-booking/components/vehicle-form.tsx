import { Loader2 } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'

import { DocumentComments } from '@/modules/procurement/components/document-comments'
import { useCrudDelete, useCrudSave } from '@/shared/crud'
import { AuditTimeline } from '@/shared/audit/audit-timeline'
import { useSingleFlight } from '@/shared/hooks/use-single-flight'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { DeleteConfirmButton } from '@/shared/ui/delete-confirm-button'
import { Input } from '@/shared/ui/input'
import { SectionHeading } from '@/shared/ui/section-heading'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { cn } from '@/shared/utils/cn'
import { BookingPageHeader } from './booking-page-header'
import { CatalogFormField } from './catalog-form-field'
import { CatalogRecordTitle } from './catalog-record-title'
import { CatalogSourceSection } from './catalog-source-section'
import { AvailabilityBadge, SourceBadge } from './status-pill'
import { SUPPLIER_TYPE } from '../types/driver'
import { VEHICLE_STATUS_LABELS, type Vehicle } from '../types/vehicle'
import { formatVehicleCapacity } from '../utils/format-vehicle-capacity'
import { isCargoVehicle } from '../utils/is-cargo-vehicle'

const API_PATH = '/api/vehicles'
const TITLE = 'Danh mục Xe'
const DELETE_WARNING = 'Xe này có thể đang được phân cho phiếu đặt xe.'

const STATUS_OPTIONS = [
  { value: 'available', label: 'Sẵn sàng' },
  { value: 'maintenance', label: 'Bảo trì' },
  { value: 'inactive', label: 'Ngưng sử dụng' },
]

interface FormState {
  license_plate: string
  model: string
  type: string
  capacity: string
  status: string
  external_company: string
  supplier_type: number
  tax_code: string
  tax_address: string
  id_number: string
}

function initialState(item?: Vehicle | null): FormState {
  return {
    license_plate: item?.license_plate ?? '',
    model: item?.model ?? '',
    type: item?.type ?? '',
    capacity: item?.capacity != null ? String(item.capacity) : '4',
    status: item?.status ?? 'available',
    external_company: item?.external_company ?? '',
    supplier_type: item?.supplier_type || SUPPLIER_TYPE.enterprise,
    tax_code: item?.tax_code ?? '',
    tax_address: item?.tax_address ?? '',
    id_number: item?.id_number ?? '',
  }
}

interface VehicleFormProps {
  /** Có = SỬA xe này; bỏ trống = THÊM mới. */
  item?: Vehicle | null
  /** Tiêu đề trang (vd "Chỉnh sửa thông tin xe"). */
  title: string
  /** Gọi sau khi lưu/xóa thành công hoặc bấm Hủy/back — thường điều hướng về danh sách. */
  onDone: () => void
}

/**
 * Biểu mẫu XE dùng trên TRANG (tạo mới `/vehicles/new` và sửa `/vehicles/:id`).
 *
 * Bố cục chia hai khối có tiêu đề: *Thông tin xe* trước, *Nguồn xe* sau. Thứ tự
 * đó là cố ý — bản cũ mở đầu bằng bốn nút nguồn và ba ô giấy tờ nhà cung cấp,
 * nên người mở trang sửa phải cuộn qua hết phần của BÊN CHO THUÊ mới tới biển
 * số của chính chiếc xe mình đang sửa.
 *
 * ⚠️ Đầu trang hiện BIỂN SỐ chứ không phải chữ "Chỉnh sửa thông tin xe": mở một
 * trang sửa mà không biết đang sửa bản ghi nào là lỗi nặng hơn mọi lỗi bố cục.
 */
export function VehicleForm({ item, title, onDone }: VehicleFormProps) {
  const save = useCrudSave<Vehicle>(API_PATH, TITLE)
  const del = useCrudDelete(API_PATH, TITLE)
  const isEdit = Boolean(item)

  const [isExternal, setIsExternal] = useState(Boolean(item?.is_external))
  const [form, setForm] = useState<FormState>(() => initialState(item))
  //  ⚠️ `disabled={pending}` KHÔNG chặn được bấm đúp: `isPending` là state React
  //  nên chỉ bật ở lượt render SAU, còn hai cú bấm liền tay nằm trong cùng một
  //  nhịp. Danh mục Xe có ràng buộc biển số duy nhất nên lần thứ hai chỉ ra
  //  toast đỏ, nhưng khi SỬA thì không có ràng buộc nào đỡ — hai lệnh PATCH đi
  //  qua và nhật ký thao tác ghi hai dòng cho một lần lưu.
  const runOnce = useSingleFlight()

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) =>
    setForm((prev) => ({ ...prev, [key]: value }))

  const pending = save.isPending || del.isPending

  function validate(): string {
    if (!form.license_plate.trim()) return 'Thiếu biển số / tên xe.'
    if (isExternal && form.supplier_type === SUPPLIER_TYPE.enterprise) {
      if (!form.external_company.trim()) return 'Thiếu tên doanh nghiệp.'
      if (!form.tax_code.trim()) return 'Thiếu mã số thuế.'
      if (!form.tax_address.trim()) return 'Thiếu địa chỉ thuế.'
    }
    return ''
  }

  async function submit() {
    const msg = validate()
    if (msg) {
      toast.error(msg)
      return
    }
    const isEnterprise = isExternal && form.supplier_type === SUPPLIER_TYPE.enterprise
    const isIndividual = isExternal && form.supplier_type === SUPPLIER_TYPE.individual
    await save.mutateAsync({
      id: item?.id,
      values: {
        license_plate: form.license_plate.trim(),
        model: form.model.trim(),
        type: form.type.trim(),
        capacity: Number(form.capacity) || 0,
        status: form.status,
        is_external: isExternal,
        supplier_type: isExternal ? form.supplier_type : SUPPLIER_TYPE.none,
        external_company: isEnterprise ? form.external_company.trim() : '',
        tax_code: isEnterprise ? form.tax_code.trim() : '',
        tax_address: isEnterprise ? form.tax_address.trim() : '',
        id_number: isIndividual ? form.id_number.trim() : '',
      },
    })
    onDone()
  }

  async function handleDelete() {
    if (!item) return
    await del.mutateAsync(item.id)
    onDone()
  }

  return (
    <div className="flex w-full flex-col">
      <BookingPageHeader
        //  Khi SỬA: đầu trang là BIỂN SỐ + một dòng tóm tắt đọc theo giá trị
        //  ĐANG NHẬP (không phải giá trị đã lưu), nên sửa loại xe hay sức chứa
        //  là dòng đó đổi theo ngay — người dùng thấy trước hệ quả của thứ mình
        //  vừa gõ mà không phải bấm Lưu để kiểm chứng.
        title={
          isEdit ? (
            <CatalogRecordTitle
              title={form.license_plate.trim() || 'Xe chưa đặt tên'}
              summary={
                [form.model, form.type, formatVehicleCapacity(form.type, Number(form.capacity))]
                  .filter((part) => part && part !== '—')
                  .join(' · ') || title
              }
            />
          ) : (
            title
          )
        }
        badge={
          isEdit ? (
            <div className="flex items-center gap-2">
              <SourceBadge isExternal={isExternal} />
              <AvailabilityBadge
                status={form.status}
                label={VEHICLE_STATUS_LABELS[form.status] ?? form.status}
              />
            </div>
          ) : undefined
        }
        onBack={onDone}
        actions={
          <>
            {isEdit && (
              <DeleteConfirmButton
                recordName={form.license_plate || 'xe này'}
                pending={del.isPending}
                onConfirm={handleDelete}
                warning={DELETE_WARNING}
              />
            )}
            <Button variant="outline" onClick={onDone} disabled={pending}>
              Hủy
            </Button>
            <Button onClick={() => void runOnce(submit)} disabled={pending}>
              {pending && <Loader2 className="size-4 animate-spin" />}
              {isEdit ? 'Lưu thay đổi' : 'Tạo mới'}
            </Button>
          </>
        }
      />
      {/*  Khi SỬA: 2 cột như trang chi tiết phiếu (C-03) — biểu mẫu trái, Trao đổi
          + Lịch sử thao tác dồn cột phải. Khi THÊM mới: một cột (chưa có gì để trao đổi). */}
      {/*  ⚠️ Trang THÊM MỚI không có cột phải nên phải tự CHẶN BỀ NGANG. Thả cho
          giãn hết màn 24" thì mỗi ô nhập rộng gần 500px — ô gõ một biển số 10 ký
          tự dài bằng nửa màn hình, và mắt phải chạy hết chiều ngang mới nối được
          nhãn với ô của nó. Trang sửa không cần vì cột phải đã bó nó lại. */}
      <div
        className={cn(
          'grid gap-5',
          isEdit && item ? 'lg:grid-cols-[minmax(0,1fr)_360px]' : 'max-w-3xl',
        )}
      >
        <div className="flex min-w-0 flex-col gap-5">
          <Card className="flex flex-col gap-6 p-5">
            <section className="flex flex-col gap-4">
              <SectionHeading>Thông tin xe</SectionHeading>

              <div className="grid gap-4 sm:grid-cols-2">
                <CatalogFormField
                  label={isExternal ? 'Biển số / Tên xe' : 'Biển số xe'}
                  required
                  hint={isExternal ? 'Chưa có biển số thì đặt tên gợi nhớ.' : undefined}
                >
                  <Input
                    value={form.license_plate}
                    onChange={(e) => set('license_plate', e.target.value)}
                    placeholder={isExternal ? 'VD: Xe 7 chỗ thuê' : 'VD: 65C-172.76'}
                  />
                </CatalogFormField>
                <CatalogFormField label="Mẫu xe">
                  <Input
                    value={form.model}
                    onChange={(e) => set('model', e.target.value)}
                    placeholder="VD: Toyota Hilux"
                  />
                </CatalogFormField>
                <CatalogFormField label="Loại xe" hint="Có chữ «tải» → sức chứa tính bằng tấn.">
                  <Input
                    value={form.type}
                    onChange={(e) => set('type', e.target.value)}
                    placeholder="VD: Xe con, Xe tải, Xe bán tải"
                  />
                </CatalogFormField>
                {/*  ⚠️ Nhãn nói rõ ĐANG TÍNH BẰNG GÌ, đọc theo loại xe vừa gõ.
                    Bản cũ ghi cứng "Tải (người/tấn)" nên người khai phải tự đoán
                    con số mình gõ đang được hiểu là chỗ ngồi hay là tấn. */}
                {/*  Đơn vị nằm ngay trong NHÃN nên không cần thêm dòng chú thích
                    lặp lại nó. */}
                <CatalogFormField
                  label={isCargoVehicle(form.type) ? 'Sức chứa (tấn)' : 'Sức chứa (chỗ)'}
                >
                  <Input
                    type="number"
                    min={0}
                    step="0.1"
                    value={form.capacity}
                    onChange={(e) => set('capacity', e.target.value)}
                    placeholder={isCargoVehicle(form.type) ? 'VD: 2.4' : 'VD: 7'}
                  />
                </CatalogFormField>
                <CatalogFormField
                  label="Trạng thái"
                  fullWidth
                  hint="Xe «Bảo trì» / «Ngưng sử dụng» vẫn nằm trong danh mục nhưng không nên điều đi."
                >
                  <Select value={form.status} onValueChange={(v) => set('status', v)}>
                    <SelectTrigger className="w-full">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {STATUS_OPTIONS.map((s) => (
                        <SelectItem key={s.value} value={s.value}>
                          {s.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </CatalogFormField>
              </div>
            </section>

            <CatalogSourceSection
              unitLabel="xe"
              idNumberHint="Căn cước của người cho thuê xe."
              isEdit={isEdit}
              isExternal={isExternal}
              onExternalChange={setIsExternal}
              supplierType={form.supplier_type}
              onSupplierTypeChange={(v) => set('supplier_type', v)}
              values={form}
              onChange={(key, value) => set(key, value)}
            />
          </Card>
        </div>

        {/*  Cột phải chỉ khi SỬA: Trao đổi trên bản ghi + Lịch sử thao tác (như phiếu). */}
        {isEdit && item && (
          <div className="flex flex-col gap-5">
            <DocumentComments entity="vehicle" entityId={item.id} />
            <AuditTimeline entity="vehicle" entityId={item.id} dense showMessage />
          </div>
        )}
      </div>
    </div>
  )
}
