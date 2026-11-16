import {
  AtSign,
  BriefcaseBusiness,
  Building,
  Building2,
  IdCard,
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
import { ChangePasswordDialog } from './change-password-dialog'
import { ProfileFieldGroup } from './profile-field-group'
import { ProfileFieldRow } from './profile-field-row'

interface ProfileField {
  key: keyof AuthUser
  label: string
  icon: LucideIcon
}

// Hồ sơ nhân sự do bộ phận Nhân sự quản lý — thẻ này chỉ HIỂN THỊ, không sửa.
const HR_FIELDS: ProfileField[] = [
  { key: 'full_name', label: 'Họ và tên', icon: User },
  { key: 'emp_code', label: 'Mã nhân viên', icon: IdCard },
  { key: 'company_name', label: 'Công ty / Pháp nhân', icon: Building2 },
  { key: 'department_name', label: 'Phòng ban', icon: Building },
  { key: 'position', label: 'Vị trí / Chức vụ', icon: BriefcaseBusiness },
  // Kiêm nhiệm = các dòng ĐANG HIỆU LỰC của tab Kiêm nhiệm, câu do backend dựng: "Phòng X (Chức vụ)" với
  // loại Phòng ban, "Công ty B (Chức vụ)" với loại Công ty (duoc-CR-756). Đặt ngay dưới Vị trí.
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

/** Một trường của phiên đăng nhập thành một dòng hồ sơ. `kiem_nhiem` là mảng câu: mỗi câu một dòng. */
function Row({ field, profile }: { field: ProfileField; profile: AuthUser }) {
  const value = profile[field.key]
  if (Array.isArray(value)) {
    const lines = value.filter((line): line is string => typeof line === 'string')
    return <ProfileFieldRow icon={field.icon} label={field.label} lines={lines} />
  }
  return (
    <ProfileFieldRow icon={field.icon} label={field.label} value={typeof value === 'string' ? value : ''} />
  )
}

/**
 * Nhóm TỔ CHỨC trong thẻ Hồ sơ nhân sự — căn cước của người đó trong công ty (mã NV, pháp nhân,
 * phòng ban, chức vụ, kiêm nhiệm, vai trò). CHỈ XEM: đây là dữ liệu gốc của phân hệ Nhân sự, sửa ở
 * hai nơi thì sớm muộn cũng lệch nhau. Đọc từ phiên đăng nhập nên có cả với tài khoản chưa gắn hồ sơ.
 */
export function ProfileOrgFields({ profile }: { profile: AuthUser }) {
  return (
    <ProfileFieldGroup title="Tổ chức" icon={User}>
      {HR_FIELDS.map((field) => (
        <Row key={field.key} field={field} profile={profile} />
      ))}
    </ProfileFieldGroup>
  )
}

/**
 * Thẻ TÀI KHOẢN — tên đăng nhập, email, số điện thoại và nút Đổi mật khẩu. Số điện thoại ở đây chỉ
 * xem; nó đọc từ phiên đăng nhập và được nạp lại sau khi người dùng tự sửa ở nhóm Liên hệ.
 */
export function ProfileAccountCard({ profile }: { profile: AuthUser }) {
  return (
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
  )
}
