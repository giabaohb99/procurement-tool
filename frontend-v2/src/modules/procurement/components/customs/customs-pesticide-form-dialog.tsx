// Hộp THÊM / SỬA một thuốc BVTV (duoc-CR-490). Khóa `customs_pesticide` (create / write).
//
// Ba điều hộp này phải nói ra, vì người dùng không tự đoán được:
//   · sửa thuốc LẤY TỪ NGUỒN thì lần «Nạp danh mục» sau ghi đè chỗ sửa theo tệp mới;
//   · tên thương mại / hoạt chất vừa sửa chưa vào dòng hàng hải quan cho tới khi bấm «Gắn lại nhãn»
//     ở mục Cấu hình (backend cố ý không quét lại ~18 nghìn dòng mỗi lần sửa một thuốc);
//   · lưu là thay TOÀN BỘ phạm vi sử dụng bằng bảng đang thấy.
// Chặn bấm đúp bằng `useRef` (đổi ngay trong lượt bấm) — `disabled` chỉ đổi ở lượt vẽ sau.
import { Info, TriangleAlert } from 'lucide-react'
import { useRef, useState, type FormEvent, type KeyboardEvent } from 'react'
import { toast } from 'sonner'

import { Button } from '@/shared/ui/button'
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
import { RequiredMark } from '@/shared/ui/required-mark'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { Textarea } from '@/shared/ui/textarea'

import { useSaveCustomsPesticide } from '../../hooks/use-customs-pesticides'
import type { CustomsPesticideDetail, CustomsPesticideInput } from '../../types/customs-pesticide'
import {
  buildPesticidePayload,
  PESTICIDE_LIMITS,
  PESTICIDE_STATUS_OPTIONS,
  validatePesticideInput,
} from '../../utils/customs-pesticide-form'
import { CustomsNotice } from './customs-controls'
import { CustomsPesticideUsesEditor } from './customs-pesticide-uses-editor'

type TextField = Exclude<keyof typeof PESTICIDE_LIMITS, 'resistance' | 'summary'>

const TEXT_FIELDS: { key: TextField; label: string; required?: boolean; wide?: boolean }[] = [
  { key: 'trade_name', label: 'Tên thuốc', required: true },
  { key: 'registration_no', label: 'Số đăng ký' },
  { key: 'active_ingredient', label: 'Hoạt chất', required: true, wide: true },
  { key: 'concentration', label: 'Hàm lượng' },
  { key: 'pest_group', label: 'Phân nhóm' },
  { key: 'registrant', label: 'Công ty đăng ký' },
  { key: 'sector', label: 'Lĩnh vực' },
  { key: 'toxicity', label: 'Nhóm độc', wide: true },
  { key: 'source_url', label: 'Đường dẫn nguồn', wide: true },
]

function blockEnter(event: KeyboardEvent<HTMLInputElement>) {
  //  Enter trong ô một dòng không được lưu cả thuốc khi người dùng chưa xong (duoc-CR-317).
  if (event.key === 'Enter') event.preventDefault()
}

interface CustomsPesticideFormDialogProps {
  /** `null` = thêm mới. */
  pesticideId: number | null
  initial: CustomsPesticideInput
  /** Thuốc lấy từ nguồn (không phải tự thêm) — sửa sẽ bị lần nạp sau ghi đè. */
  fromSource: boolean
  onClose: () => void
  onSaved: (saved: CustomsPesticideDetail) => void
}

export function CustomsPesticideFormDialog({
  pesticideId,
  initial,
  fromSource,
  onClose,
  onSaved,
}: CustomsPesticideFormDialogProps) {
  const [value, setValue] = useState(initial)
  const [error, setError] = useState<string | null>(null)
  const busy = useRef(false)
  const save = useSaveCustomsPesticide()
  const pending = save.isPending
  const isEdit = pesticideId !== null

  function patch(changes: Partial<CustomsPesticideInput>) {
    setValue((current) => ({ ...current, ...changes }))
  }

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (busy.current) return
    const problem = validatePesticideInput(value)
    setError(problem)
    if (problem) return
    busy.current = true
    try {
      const saved = await save.mutateAsync({ id: pesticideId, body: buildPesticidePayload(value) })
      toast.success(isEdit ? 'Đã lưu thuốc BVTV' : 'Đã thêm thuốc BVTV')
      onSaved(saved)
    } catch {
      //  `httpClient` đã báo lỗi 422 / 403 bằng toast — giữ hộp mở để người dùng sửa tiếp.
    } finally {
      busy.current = false
    }
  }

  return (
    <Dialog open onOpenChange={(open) => !open && !pending && onClose()}>
      <DialogContent className="flex max-h-[92dvh] flex-col gap-4 sm:max-w-4xl">
        <DialogHeader>
          <DialogTitle>{isEdit ? `Sửa thuốc «${initial.trade_name}»` : 'Thêm thuốc BVTV'}</DialogTitle>
          <DialogDescription>
            Thuốc thêm trên màn được giữ lại qua các lần «Nạp danh mục».
          </DialogDescription>
        </DialogHeader>

        <form
          id="customs-pesticide-form"
          className="min-h-0 flex-1 space-y-4 overflow-y-auto pr-1"
          onSubmit={(event) => void submit(event)}
          noValidate
        >
          {isEdit && fromSource && (
            <CustomsNotice tone="warning" icon={<TriangleAlert className="size-4" />}>
              Thuốc này lấy từ bản cào — lần «Nạp danh mục» sau sẽ ghi đè chỗ sửa tay theo nguồn.
            </CustomsNotice>
          )}
          <CustomsNotice icon={<Info className="size-4" />}>
            Tên thuốc / hoạt chất mới chỉ vào nhãn của dòng hàng hải quan sau khi bấm «Gắn lại nhãn»
            ở mục Cấu hình, hoặc ở lần nạp danh mục kế tiếp.
          </CustomsNotice>

          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1 sm:col-span-2">
              <Label htmlFor="pesticide-summary">Mô tả tóm tắt</Label>
              <Textarea
                id="pesticide-summary"
                rows={3}
                placeholder="Vd: Thuốc trừ bệnh … hoạt chất …, sử dụng trên …, phòng trừ …, đăng ký bởi …"
                value={value.summary}
                maxLength={PESTICIDE_LIMITS.summary}
                disabled={pending}
                onChange={(event) => patch({ summary: event.target.value })}
              />
            </div>
            {TEXT_FIELDS.map((field) => (
              <div key={field.key} className={field.wide ? 'space-y-1 sm:col-span-2' : 'space-y-1'}>
                <Label htmlFor={`pesticide-${field.key}`}>
                  {field.label}
                  {field.required && <RequiredMark hint="Bắt buộc" />}
                </Label>
                <Input
                  id={`pesticide-${field.key}`}
                  value={value[field.key]}
                  maxLength={PESTICIDE_LIMITS[field.key]}
                  disabled={pending}
                  onKeyDown={blockEnter}
                  onChange={(event) => patch({ [field.key]: event.target.value })}
                />
              </div>
            ))}
            <div className="space-y-1">
              <Label htmlFor="pesticide-status">Tình trạng</Label>
              <Select
                value={String(value.status)}
                onValueChange={(status) => patch({ status: Number(status) })}
                disabled={pending}
              >
                <SelectTrigger id="pesticide-status" className="w-full">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {PESTICIDE_STATUS_OPTIONS.map((option) => (
                    <SelectItem key={option.value} value={String(option.value)}>
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div className="space-y-1">
                <Label htmlFor="pesticide-registered-on">Ngày cấp</Label>
                <DatePicker
                  id="pesticide-registered-on"
                  value={value.registered_on ?? ''}
                  clearable
                  disabled={pending}
                  onChange={(date) => patch({ registered_on: date || null })}
                />
              </div>
              <div className="space-y-1">
                <Label htmlFor="pesticide-expires-on">Hết hạn đăng ký</Label>
                <DatePicker
                  id="pesticide-expires-on"
                  value={value.expires_on ?? ''}
                  clearable
                  disabled={pending}
                  onChange={(date) => patch({ expires_on: date || null })}
                />
              </div>
            </div>
            <div className="space-y-1 sm:col-span-2">
              <Label htmlFor="pesticide-resistance">Nhóm kháng (quản lý tính kháng)</Label>
              <Textarea
                id="pesticide-resistance"
                rows={2}
                value={value.resistance}
                maxLength={PESTICIDE_LIMITS.resistance}
                disabled={pending}
                onChange={(event) => patch({ resistance: event.target.value })}
              />
            </div>
          </div>

          <CustomsPesticideUsesEditor
            uses={value.uses}
            disabled={pending}
            onChange={(uses) => patch({ uses })}
          />
        </form>

        {error && (
          <p role="alert" className="text-sm text-destructive">
            {error}
          </p>
        )}
        <DialogFooter>
          <Button type="button" variant="outline" disabled={pending} onClick={onClose}>
            Hủy
          </Button>
          <Button type="submit" form="customs-pesticide-form" disabled={pending}>
            {pending ? 'Đang lưu…' : isEdit ? 'Lưu' : 'Thêm thuốc'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
