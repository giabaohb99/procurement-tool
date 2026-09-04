import { DoorOpen } from 'lucide-react'

import { usePermission } from '@/core/authorization/use-permission'
import { FormCard } from '@/shared/ui/form-card'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { NumberInput } from '@/shared/ui/number-input'
import { RequiredMark } from '@/shared/ui/required-mark'
import { EmployeeMultiSelect } from '@/shared/ui/employee-multi-select'
import { Textarea } from '@/shared/ui/textarea'
import { useEmployees } from '../hooks/use-employees'
import type { RoomBookingFormValues } from '../utils/room-form-values'
import { RoomPickerField } from './room-picker-field'
import { toApiTime } from '../utils/room-time'

interface RoomBookingFormProps {
  value: RoomBookingFormValues
  onChange: (values: RoomBookingFormValues) => void
  /** Mở từ ô trống trên LỊCH: phòng đã được chỉ đích danh, xem `RoomPickerField`. */
  lockedRoom?: boolean
}

/**
 * FORM ĐẶT PHÒNG — **chỉ dùng khi phiếu còn SỬA ĐƯỢC**.
 *
 * Phiếu đã gửi duyệt thì trang chi tiết dựng phần tóm tắt chỉ-xem, KHÔNG dựng
 * form này với cờ `disabled`: `disabled` gỡ khả năng nhận con trỏ nên người
 * dùng không bôi đen, không copy được giá trị (luật chung của bộ ERP).
 *
 * Thứ tự ô đi theo đúng thứ tự người ta nghĩ: **họp về gì · lúc nào · ở đâu ·
 * bao nhiêu người · mời ai**. Phòng đứng SAU giờ là có chủ ý — chọn phòng trước
 * rồi mới biết giờ đó nó bận thì phải quay lại sửa.
 *
 * ⚠️ Dải «phòng còn trống» KHÔNG nằm ở đây nữa (dời 04/09/2026) mà ở cột phải
 * (`RoomBookingSidePanel`): nó là công cụ QUYẾT ĐỊNH, không phải ô nhập, và để
 * xen giữa hai ô giờ thì form bị cắt làm đôi bởi một khối xám chạy suốt bề ngang.
 */
export function RoomBookingForm({ value, onChange, lockedRoom }: RoomBookingFormProps) {
  const { can } = usePermission()

  //  Danh bạ nhân sự là dữ liệu của phân hệ khác: chỉ gọi khi có `employee.read`,
  //  không thì người dùng ăn toast 403 ngay lúc mở form (bài học tab NCC).
  const canPickEmployee = can('employee', 'read')
  const { data: employeeData } = useEmployees(
    { page: 1, page_size: 500, is_active: 'true' },
    { enabled: canPickEmployee },
  )
  const employees = employeeData?.items ?? []

  const set = <K extends keyof RoomBookingFormValues>(
    key: K,
    v: RoomBookingFormValues[K],
  ) => onChange({ ...value, [key]: v })

  return (
    <FormCard title="Thông tin cuộc họp" icon={DoorOpen}>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="space-y-1.5 sm:col-span-2">
          <Label htmlFor="room-title">
            Nội dung cuộc họp
            <RequiredMark hint="Người duyệt đọc đúng dòng này để quyết định" />
          </Label>
          <Input
            id="room-title"
            value={value.title}
            maxLength={255}
            placeholder="VD: Họp giao ban tuần 37"
            onChange={(e) => set('title', e.target.value)}
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="room-start">
            Bắt đầu
            <RequiredMark />
          </Label>
          <Input
            id="room-start"
            type="datetime-local"
            value={value.startAt}
            onChange={(e) => set('startAt', e.target.value)}
          />
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="room-end">
            Kết thúc
            <RequiredMark />
          </Label>
          <Input
            id="room-end"
            type="datetime-local"
            value={value.endAt}
            onChange={(e) => set('endAt', e.target.value)}
          />
          {value.startAt && value.endAt && value.endAt <= value.startAt && (
            <p className="text-xs text-destructive">
              «Kết thúc» phải sau «Bắt đầu».
            </p>
          )}
        </div>

        <div className="space-y-1.5 sm:col-span-2">
          <Label>
            Phòng họp
            <RequiredMark />
          </Label>
          <RoomPickerField
            roomId={value.roomId}
            onChange={(id) => set('roomId', id)}
            startAt={toApiTime(value.startAt)}
            endAt={toApiTime(value.endAt)}
            lockedFromCalendar={lockedRoom}
          />
        </div>

        <div className="space-y-1.5">
          <Label>Số người dự (dự kiến)</Label>
          <NumberInput
            value={value.attendeeCount}
            decimals={false}
            onChange={(v) => set('attendeeCount', v)}
          />
          <p className="text-xs text-muted-foreground">
            Ghi quá sức chứa của phòng thì phiếu bị chặn lúc lưu.
          </p>
        </div>

        <div className="space-y-1.5 sm:col-span-2">
          <Label>Mời tham dự</Label>
          <EmployeeMultiSelect
            value={value.attendeeIds}
            onChange={(ids) => set('attendeeIds', ids)}
            employees={employees}
            placeholder={
              canPickEmployee ? 'Chọn người được mời…' : 'Không có quyền xem danh bạ nhân sự'
            }
            disabled={!canPickEmployee}
          />
          <p className="text-xs text-muted-foreground">
            Người được mời nhận thông báo <strong>sau khi phiếu được duyệt</strong> — chưa
            duyệt thì cuộc họp chưa chắc diễn ra.
          </p>
        </div>

        <div className="space-y-1.5 sm:col-span-2">
          <Label htmlFor="room-purpose">Ghi chú / chuẩn bị</Label>
          <Textarea
            id="room-purpose"
            rows={3}
            value={value.purpose}
            placeholder="VD: cần máy chiếu, in sẵn 10 bộ tài liệu"
            onChange={(e) => set('purpose', e.target.value)}
          />
        </div>
      </div>
    </FormCard>
  )
}
