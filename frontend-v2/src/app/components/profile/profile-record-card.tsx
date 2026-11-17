import { Info, Printer, UserRound } from 'lucide-react'
import { Link } from 'react-router-dom'

import type { AuthUser } from '@/core/auth/auth-types'
import type { Employee } from '@/modules/hr/types/employee'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { FormCard } from '@/shared/ui/form-card'
import { ProfileContactCard } from './profile-contact-card'
import { ProfileHrDetails } from './profile-hr-details'
import { ProfileOrgFields } from './profile-info-card'

interface ProfileRecordCardProps {
  profile: AuthUser
  /** Hồ sơ nhân sự đầy đủ (`/api/employees/me`). Rỗng khi tài khoản chưa gắn hồ sơ. */
  employee?: Employee | null
}

/**
 * THẺ HỒ SƠ NHÂN SỰ của Trang cá nhân (duoc-CR-766) — MỘT thẻ, các nhóm trường chảy theo hai cột.
 *
 * Trước đây mỗi nhóm là một thẻ riêng xếp lưới (Hồ sơ nhân sự, Thông tin cá nhân, Công việc, CCCD,
 * Ngân hàng, Bảo hiểm, Liên hệ): bảy thẻ cao thấp khác nhau, lưới chừa khoảng trống lớn và nút In
 * phiếu nằm lơ lửng giữa trang. `columns-2` xếp các nhóm nối đuôi nhau trong cột nên không còn lỗ.
 *
 * Thứ tự nhóm: Tổ chức (luôn có, đọc từ phiên đăng nhập) → Liên hệ (nhóm DUY NHẤT tự sửa được, nút
 * Sửa nằm ngay tiêu đề nhóm) → nhân thân → công việc → giấy tờ, ngân hàng, bảo hiểm.
 */
export function ProfileRecordCard({ profile, employee }: ProfileRecordCardProps) {
  return (
    <FormCard
      title="Hồ sơ nhân sự"
      icon={UserRound}
      iconClassName="text-muted-foreground"
      actions={
        employee && (
          //  duoc-CR-676 — in Phiếu thông tin nhân viên của chính mình (BM00../QT01/NS).
          <Button variant="outline" size="sm" asChild>
            <Link to={appRoutes.hr.myEmployeeInfoPrint}>
              <Printer className="size-4" />
              In phiếu thông tin
            </Link>
          </Button>
        )
      }
    >
      <div className="gap-x-10 lg:columns-2 [&>section]:mb-6">
        <ProfileOrgFields profile={profile} />
        {/*  Liên hệ ngay sau Tổ chức: nhóm DUY NHẤT tự sửa được, đừng để cuối thẻ. */}
        {employee && <ProfileContactCard employee={employee} />}
        {employee && <ProfileHrDetails employee={employee} />}
      </div>

      <p className="flex gap-2 rounded-lg bg-accent px-3 py-2 text-xs text-muted-foreground">
        <Info className="mt-0.5 size-3.5 shrink-0" />
        {employee ? (
          <span>
            Hồ sơ nhân sự và vai trò do bộ phận Nhân sự / Quản trị hệ thống cập nhật. Thông tin chưa
            đúng thì gửi <strong>Đề nghị sửa hồ sơ</strong> bên dưới hoặc liên hệ bộ phận Nhân sự.
            Số điện thoại, địa chỉ và người báo tin thì bạn tự sửa ở nhóm <strong>Liên hệ</strong>.
          </span>
        ) : (
          <span>
            Tài khoản này chưa gắn hồ sơ nhân sự. Thông tin tổ chức và vai trò do bộ phận Nhân sự /
            Quản trị hệ thống cập nhật.
          </span>
        )}
      </p>
    </FormCard>
  )
}
