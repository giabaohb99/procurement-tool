import { Loader2 } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'

import { useCrudDelete, useCrudSave } from '@/shared/crud'
import { AuditTimeline } from '@/shared/audit/audit-timeline'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { DeleteConfirmButton } from '@/shared/ui/delete-confirm-button'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { RequiredMark } from '@/shared/ui/required-mark'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { cn } from '@/shared/utils/cn'
import { BookingPageHeader } from './booking-page-header'
import { SUPPLIER_TYPE } from '../types/driver'
import type { Vehicle } from '../types/vehicle'

const API_PATH = '/api/vehicles'
const TITLE = 'Danh mục Xe'
const DELETE_WARNING = 'Xe này có thể đang được phân cho phiếu đặt xe.'

const STATUS_OPTIONS = [
  { value: 'available', label: 'Sẵn sàng' },
  { value: 'maintenance', label: 'Bảo trì' },
  { value: 'inactive', label: 'Ngưng sử dụng' },
]

type Mode = 'internal' | 'external'

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
 * Nguồn Nội bộ / Thuê ngoài; thuê ngoài chọn Doanh nghiệp / Cá nhân + MST · địa chỉ
 * thuế · CCCD. Khóa nguồn + loại NCC khi sửa. Trang sửa có khối Lịch sử thao tác.
 */
export function VehicleForm({ item, title, onDone }: VehicleFormProps) {
  const save = useCrudSave<Vehicle>(API_PATH, TITLE)
  const del = useCrudDelete(API_PATH, TITLE)
  const isEdit = Boolean(item)

  const [mode, setMode] = useState<Mode>(item?.is_external ? 'external' : 'internal')
  const [form, setForm] = useState<FormState>(() => initialState(item))

  const set = <K extends keyof FormState>(key: K, value: FormState[K]) =>
    setForm((prev) => ({ ...prev, [key]: value }))

  const pending = save.isPending || del.isPending

  function validate(): string {
    if (!form.license_plate.trim()) return 'Thiếu biển số / tên xe.'
    if (mode === 'external' && form.supplier_type === SUPPLIER_TYPE.enterprise) {
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
    const isEnterprise = mode === 'external' && form.supplier_type === SUPPLIER_TYPE.enterprise
    const isIndividual = mode === 'external' && form.supplier_type === SUPPLIER_TYPE.individual
    await save.mutateAsync({
      id: item?.id,
      values: {
        license_plate: form.license_plate.trim(),
        model: form.model.trim(),
        type: form.type.trim(),
        capacity: Number(form.capacity) || 0,
        status: form.status,
        is_external: mode === 'external',
        supplier_type: mode === 'external' ? form.supplier_type : SUPPLIER_TYPE.none,
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
        title={title}
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
            <Button onClick={submit} disabled={pending}>
              {pending && <Loader2 className="size-4 animate-spin" />}
              {isEdit ? 'Lưu thay đổi' : 'Tạo mới'}
            </Button>
          </>
        }
      />
      <div className="flex flex-col gap-5">
      <Card className="flex flex-col gap-4 p-5">
        {/* Nút chọn nguồn: Nội bộ (xanh) | Thuê ngoài (hổ phách) — khóa khi SỬA. */}
        <div className="grid grid-cols-2 gap-2 sm:max-w-md">
          <ModeButton active={mode === 'internal'} tone="blue" disabled={isEdit} onClick={() => setMode('internal')}>
            Nội bộ
          </ModeButton>
          <ModeButton active={mode === 'external'} tone="amber" disabled={isEdit} onClick={() => setMode('external')}>
            Thuê ngoài
          </ModeButton>
        </div>
        {isEdit && (
          <p className="-mt-2 text-xs text-muted-foreground">
            Không đổi được nguồn (nội bộ / thuê ngoài) của xe đã tạo.
          </p>
        )}

        {mode === 'external' && (
          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label>Loại nhà cung cấp</Label>
              <div className="grid grid-cols-2 gap-2 sm:max-w-md">
                <ModeButton active={form.supplier_type === SUPPLIER_TYPE.enterprise} tone="blue" disabled={isEdit} onClick={() => set('supplier_type', SUPPLIER_TYPE.enterprise)}>
                  Doanh nghiệp
                </ModeButton>
                <ModeButton active={form.supplier_type === SUPPLIER_TYPE.individual} tone="amber" disabled={isEdit} onClick={() => set('supplier_type', SUPPLIER_TYPE.individual)}>
                  Cá nhân
                </ModeButton>
              </div>
              {isEdit && (
                <p className="text-xs text-muted-foreground">
                  Không đổi được loại nhà cung cấp của xe đã tạo.
                </p>
              )}
            </div>

            {form.supplier_type === SUPPLIER_TYPE.individual ? (
              <Field label="CCCD">
                <Input value={form.id_number} onChange={(e) => set('id_number', e.target.value)} placeholder="Số căn cước công dân" />
              </Field>
            ) : (
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Tên doanh nghiệp" required>
                  <Input value={form.external_company} onChange={(e) => set('external_company', e.target.value)} placeholder="VD: Công ty Vận tải ABC" />
                </Field>
                <Field label="Mã số thuế" required>
                  <Input value={form.tax_code} onChange={(e) => set('tax_code', e.target.value)} placeholder="VD: 0312345678" />
                </Field>
                <Field label="Địa chỉ thuế" required fullWidth>
                  <Input value={form.tax_address} onChange={(e) => set('tax_address', e.target.value)} placeholder="Địa chỉ đăng ký thuế" />
                </Field>
              </div>
            )}
          </div>
        )}

        <div className="grid gap-4 sm:grid-cols-2">
          <Field label={mode === 'external' ? 'Biển số / Tên xe' : 'Biển số xe'} required>
            <Input value={form.license_plate} onChange={(e) => set('license_plate', e.target.value)} placeholder={mode === 'external' ? 'VD: Xe 7 chỗ thuê' : 'VD: 65C-172.76'} />
          </Field>
          <Field label="Mẫu xe">
            <Input value={form.model} onChange={(e) => set('model', e.target.value)} placeholder="VD: Toyota Hilux" />
          </Field>
          <Field label="Loại xe">
            <Input value={form.type} onChange={(e) => set('type', e.target.value)} placeholder="VD: Xe con, Xe tải, Xe bán tải" />
          </Field>
          <Field label="Tải (người/tấn)">
            <Input type="number" min={0} step="0.1" value={form.capacity} onChange={(e) => set('capacity', e.target.value)} placeholder="Số chỗ hoặc tải trọng" />
          </Field>
          <Field label="Trạng thái" fullWidth>
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
          </Field>
        </div>

      </Card>

      {isEdit && item && (
        <AuditTimeline entity="vehicle" entityId={item.id} dense showMessage />
      )}
      </div>
    </div>
  )
}

function ModeButton({
  active,
  tone,
  disabled,
  onClick,
  children,
}: {
  active: boolean
  tone: 'blue' | 'amber'
  disabled?: boolean
  onClick: () => void
  children: React.ReactNode
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      className={cn(
        'flex h-10 items-center justify-center rounded-lg text-sm font-semibold transition-colors',
        'disabled:cursor-not-allowed disabled:opacity-60',
        !active && 'border border-input bg-background text-muted-foreground hover:bg-accent',
        active && tone === 'blue' && 'border-2 border-blue-500 bg-blue-50 text-blue-600 dark:bg-blue-950/40',
        active && tone === 'amber' && 'border-2 border-amber-500 bg-amber-50 text-amber-600 dark:bg-amber-950/40',
      )}
    >
      {children}
    </button>
  )
}

function Field({
  label,
  required,
  fullWidth,
  children,
}: {
  label: string
  required?: boolean
  fullWidth?: boolean
  children: React.ReactNode
}) {
  return (
    <div className={cn('flex flex-col gap-1.5', fullWidth && 'sm:col-span-2')}>
      <Label>
        {label}
        {required && <RequiredMark />}
      </Label>
      {children}
    </div>
  )
}
