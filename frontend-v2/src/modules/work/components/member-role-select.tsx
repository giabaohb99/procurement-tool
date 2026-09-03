import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { ASSIGNABLE_ROLES } from '../config/member-roles'

interface MemberRoleSelectProps {
  value: number
  onChange: (role: number) => void
  disabled?: boolean
  /** Nội dung cho trình đọc màn hình — ô này lặp lại trên mỗi dòng thành viên. */
  ariaLabel: string
  className?: string
}

/**
 * Ô chọn vai trò dùng chung cho HÀNG MỜI và TỪNG DÒNG thành viên.
 *
 * Tách ra vì trước đây hai chỗ chép cùng một danh sách ba mục — thêm vai trò thứ
 * tư thì sửa một chỗ, quên chỗ kia, và hai ô cùng màn hình lệch nhau.
 */
export function MemberRoleSelect({
  value,
  onChange,
  disabled,
  ariaLabel,
  className,
}: MemberRoleSelectProps) {
  return (
    <Select value={String(value)} onValueChange={(v) => onChange(Number(v))} disabled={disabled}>
      <SelectTrigger className={className} aria-label={ariaLabel}>
        {/*  ⚠️ Truyền children TƯỜNG MINH cho `SelectValue`. Mặc định Radix chép
             nguyên children của mục đang chọn vào ô — mà mục ở đây có hai dòng
             (nhãn + câu giải thích), nên ô cao gấp đôi và câu giải thích bị cắt
             giữa chừng thành «Mời và gỡ người,». Câu giải thích chỉ thuộc về lúc
             ĐANG CHỌN, không thuộc về ô đã chọn xong. */}
        <SelectValue>{ASSIGNABLE_ROLES.find((r) => r.value === value)?.label}</SelectValue>
      </SelectTrigger>
      <SelectContent>
        {ASSIGNABLE_ROLES.map((role) => (
          <SelectItem key={role.value} value={String(role.value)}>
            {/*  Nhãn và câu giải thích xếp dọc trong cùng một mục: quản trị chọn
                 vai trò cho người khác mà phải nhớ thuộc lòng ba vai làm được gì
                 thì họ chọn bừa, và sai vai là người ta mất quyền sửa việc. */}
            <span className="flex flex-col items-start">
              <span>{role.label}</span>
              <span className="text-xs text-muted-foreground">{role.hint}</span>
            </span>
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}
