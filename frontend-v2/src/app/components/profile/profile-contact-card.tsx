import { Home, Info, MapPin, Phone, PhoneCall } from 'lucide-react'

import type { Employee } from '@/modules/hr/types/employee'
import { FormCard } from '@/shared/ui/form-card'
import { ProfileFieldRow } from './profile-field-row'
import { SelfContactDialog } from './self-contact-dialog'

interface ProfileContactCardProps {
  employee: Employee
}

/**
 * Thẻ «Liên hệ» ở Trang cá nhân — nhóm DUY NHẤT người dùng tự sửa được trên hồ
 * sơ của chính mình (bao-CR-508, khách chốt 28/09/2026).
 *
 * Thay cho thẻ «Địa chỉ» chỉ-xem trước đây: gom số điện thoại + hai địa chỉ về
 * một chỗ, kèm nút «Sửa». Người báo tin nằm ở bảng riêng ngay dưới
 * (`ProfileEmergencyContacts`) vì nó đi cửa API khác và có nút Lưu riêng.
 *
 * Nhãn hai địa chỉ lấy đúng chữ của tab «Liên hệ & Ngân hàng» ở phân hệ Nhân
 * sự — người dùng và phòng Nhân sự nói về cùng một ô bằng cùng một tên.
 */
export function ProfileContactCard({ employee }: ProfileContactCardProps) {
  return (
    <FormCard
      title="Liên hệ"
      icon={PhoneCall}
      iconClassName="text-muted-foreground"
      actions={<SelfContactDialog employee={employee} />}
    >
      <ProfileFieldRow icon={Phone} label="Số điện thoại" value={employee.phone} />
      <ProfileFieldRow icon={Home} label="Địa chỉ thường trú" value={employee.permanent_address} />
      <ProfileFieldRow
        icon={MapPin}
        label="Địa chỉ hiện nay (tạm trú)"
        value={employee.current_address}
      />

      <p className="mt-3 flex gap-2 rounded-lg bg-accent px-3 py-2 text-xs text-muted-foreground">
        <Info className="mt-0.5 size-3.5 shrink-0" />
        <span>
          Bạn tự cập nhật được số điện thoại, địa chỉ và người báo tin. Thay đổi áp dụng ngay và
          được ghi vào lịch sử hồ sơ.
        </span>
      </p>
    </FormCard>
  )
}
