import {
  AtSign,
  BriefcaseBusiness,
  Building,
  Building2,
  IdCard,
  Info,
  KeyRound,
  Layers,
  Mail,
  Phone,
  ShieldCheck,
  User,
  type LucideIcon,
} from 'lucide-react'

import type { AuthUser } from '@/core/auth/auth-types'
import { FormCard } from '@/shared/ui/form-card'
import { cn } from '@/shared/utils/cn'
import { ChangePasswordDialog } from './change-password-dialog'

interface ProfileField {
  key: keyof AuthUser
  label: string
  icon: LucideIcon
}

// Hồ sơ nhân sự do bộ phận Nhân sự quản lý — trang này chỉ HIỂN THỊ, không sửa.
const HR_FIELDS: ProfileField[] = [
  { key: 'full_name', label: 'Họ và tên', icon: User },
  { key: 'emp_code', label: 'Mã nhân viên', icon: IdCard },
  { key: 'company_name', label: 'Công ty / Pháp nhân', icon: Building2 },
  { key: 'department_name', label: 'Phòng ban', icon: Building },
  { key: 'position', label: 'Vị trí / Chức vụ', icon: BriefcaseBusiness },
  // Kiêm nhiệm = các phòng phụ (tab_employee_department). Đặt ngay dưới Vị trí.
  { key: 'kiem_nhiem', label: 'Kiêm nhiệm', icon: Layers },
  { key: 'role_name', label: 'Vai trò', icon: ShieldCheck },
]

// Khối "Tài khoản": trường "Tài khoản" hiện MÃ NV (cũng là tên đăng nhập) — khác
// hẳn dòng Email bên dưới.
const ACCOUNT_FIELDS: ProfileField[] = [
  { key: 'emp_code', label: 'Tài khoản', icon: AtSign },
  { key: 'email', label: 'Email', icon: Mail },
  { key: 'phone', label: 'Số điện thoại', icon: Phone },
]

function Row({ field, profile }: { field: ProfileField; profile: AuthUser }) {
  const value = profile[field.key]
  // kiem_nhiem/role_names là mảng — nối lại; còn lại là chuỗi.
  const text = Array.isArray(value) ? value.join(', ') : typeof value === 'string' ? value : ''
  return (
    <div className="flex items-center gap-3 border-b border-dashed py-2 last:border-b-0">
      <field.icon className="size-4 shrink-0 text-muted-foreground" />
      <span className="w-40 shrink-0 text-[13px] text-muted-foreground">{field.label}</span>
      <span
        className={cn(
          'min-w-0 flex-1 truncate text-sm',
          text ? 'font-medium text-navy dark:text-foreground' : 'text-muted-foreground italic',
        )}
      >
        {text || 'Chưa cập nhật'}
      </span>
    </div>
  )
}

/**
 * Hồ sơ nhân sự + khối Tài khoản — CHỈ XEM (trừ nút Đổi mật khẩu).
 *
 * Cố ý không cho sửa hồ sơ tại đây: mã nhân viên, phòng ban và vai trò là dữ liệu
 * gốc của phân hệ Nhân sự, sửa ở hai nơi thì sớm muộn cũng lệch nhau.
 */
export function ProfileInfoCard({ profile }: { profile: AuthUser }) {
  return (
    <>
      <FormCard title="Thông tin cá nhân" icon={User} iconClassName="text-muted-foreground">
        {HR_FIELDS.map((field) => (
          <Row key={field.key} field={field} profile={profile} />
        ))}

        <p className="mt-3 flex gap-2 rounded-lg bg-accent px-3 py-2 text-xs text-muted-foreground">
          <Info className="mt-0.5 size-3.5 shrink-0" />
          <span>
            Hồ sơ nhân sự và vai trò do bộ phận Nhân sự / Quản trị hệ thống cập nhật. Nếu thông tin
            chưa đúng, hãy liên hệ bộ phận Nhân sự để được chỉnh sửa.
          </span>
        </p>
      </FormCard>

      <FormCard
        title="Tài khoản"
        icon={KeyRound}
        iconClassName="text-muted-foreground"
        actions={<ChangePasswordDialog />}
      >
        {ACCOUNT_FIELDS.map((field) => (
          <Row key={field.key} field={field} profile={profile} />
        ))}
      </FormCard>
    </>
  )
}
