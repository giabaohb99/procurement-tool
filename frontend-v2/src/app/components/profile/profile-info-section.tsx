import type { AuthUser } from '@/core/auth/auth-types'
import { SelfChangeRequestCard } from '@/modules/hr/components/self-change-request-card'
import type { Employee } from '@/modules/hr/types/employee'
import { AuditTimeline } from '@/shared/audit'
import { EmailNotificationCard } from './email-notification-card'
import { ProfileEmergencyContacts } from './profile-emergency-contacts'
import { ProfileAccountCard } from './profile-info-card'
import { ProfileLeaveCard } from './profile-leave-card'
import { ProfileRecordCard } from './profile-record-card'
import { ProfileSalaryCard } from './profile-salary-card'
import { ProfileShiftCard } from './profile-shift-card'
import { SignatureCard } from './signature-card'

interface ProfileInfoSectionProps {
  profile: AuthUser
  /** Hồ sơ nhân sự đầy đủ. Rỗng khi tài khoản chưa gắn hồ sơ (admin, tài khoản hệ thống). */
  employee?: Employee | null
}

/**
 * Mục THÔNG TIN CÁ NHÂN (mặc định) của Trang cá nhân — bố cục duoc-CR-766, đọc từ trên xuống:
 *
 * 1. Hai thẻ ngắn cao bằng nhau: Quỹ phép · Lương của tôi — câu hỏi hay gặp nhất, trả lời ngay
 *    đầu trang. Không nhét thêm thẻ thứ ba: cột nội dung chỉ ~830px, ba thẻ thì dòng email của thẻ
 *    Tài khoản bị bẻ vụn.
 * 2. MỘT thẻ Hồ sơ nhân sự, các nhóm trường chảy hai cột (`ProfileRecordCard`).
 * 3. Ca làm việc tuần này bên trái; Tài khoản + Chữ ký bên phải — hai cột cao xấp xỉ nhau. Tài
 *    khoản chưa gắn hồ sơ (không có ca) thì Tài khoản sang trái để hai cột vẫn cân.
 * 4. Email thông báo, Người báo tin khẩn cấp, Đề nghị sửa hồ sơ, Lịch sử thao tác — chạy hết bề
 *    ngang. Email thông báo từng đứng chung cột phải và làm cột đó dài gấp đôi cột ca.
 *
 * Thẻ nào phụ thuộc hồ sơ nhân sự (quỹ phép, ca, lương, người báo tin, đề nghị sửa) chỉ dựng khi có
 * `employee`; quỹ phép còn tự tắt khi thiếu `leave_balance.read`. Lưới hàng 1 tự co số cột theo số
 * thẻ thật có, không chừa ô trống.
 *
 * ⚠️ `min-w-0` ở các ô lưới là bắt buộc: ô lưới mặc định `min-width: auto`, một dòng chữ dài không
 * khoảng trắng (tên pháp nhân, email) kéo cả cột tràn khỏi màn ở khổ 390px.
 */
export function ProfileInfoSection({ profile, employee }: ProfileInfoSectionProps) {
  return (
    <div className="space-y-4">
      {employee && (
        <div className="grid gap-4 md:grid-cols-2 [&>*]:min-w-0">
          <ProfileLeaveCard employeeId={employee.id} hasHireDate={Boolean(employee.hire_date)} />
          <ProfileSalaryCard employee={employee} />
        </div>
      )}

      <ProfileRecordCard profile={profile} employee={employee} />

      <div className="grid items-start gap-4 lg:grid-cols-2 [&>*]:min-w-0">
        {/*  duoc-CR-761 — ca làm việc của chính mình theo tuần. Chuông "ca được xếp / đổi" mở về `/me`,
             nên thẻ đứng ngay trong mục mặc định này. */}
        {employee ? <ProfileShiftCard /> : <ProfileAccountCard profile={profile} />}
        <div className="flex flex-col gap-4">
          {employee && <ProfileAccountCard profile={profile} />}
          <SignatureCard signature={profile.signature} />
        </div>
      </div>

      {/*  bao-CR-349 — công tắc email thông báo của chính mình. */}
      <EmailNotificationCard value={profile.notify_email} />

      {employee && (
        <>
          <ProfileEmergencyContacts employeeId={employee.id} />
          {/*  duoc-CR-676 (C6) — phần hồ sơ còn lại: ĐỀ NGHỊ sửa, phòng Nhân sự duyệt rồi mới áp. */}
          <SelfChangeRequestCard employee={employee} />
        </>
      )}

      {/*  Gọi TRẦN, đừng bọc `FormCard`: `AuditTimeline` tự dựng thẻ kèm tiêu đề của nó. */}
      <AuditTimeline entity="user" entityId={profile.id} />
    </div>
  )
}
