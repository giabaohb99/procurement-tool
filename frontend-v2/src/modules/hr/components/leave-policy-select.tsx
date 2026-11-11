import { Link } from 'react-router-dom'
import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'

interface LeavePolicySelectProps {
  id: string
  policies: readonly { id: number; code: string; name: string }[]
  /** Đang tải danh sách: chưa được báo "không có" kẻo câu báo nháy lên rồi tắt. */
  isLoading: boolean
  value: number
  onChange: (id: number) => void
}

/**
 * Ô chọn chính sách nghỉ phép ĐANG DÙNG — dùng chung cho hộp Phân bổ một người và trang Phân bổ hàng loạt
 * (duoc-CR-744 lượt f). Danh sách rỗng thì ô tắt và nói thẳng là chưa có chính sách nào, kèm đường sang
 * Thiết lập > Chính sách nghỉ phép cho người có quyền tạo (`leave_type.write`, cùng tab đó). Trước đây ô vẫn
 * mời "Chọn chính sách đang dùng" rồi mở ra trống trơn, người dùng tưởng ô bị hỏng.
 */
export function LeavePolicySelect({ id, policies, isLoading, value, onChange }: LeavePolicySelectProps) {
  const { can } = usePermission()
  const isEmpty = !isLoading && policies.length === 0

  return (
    <>
      <Select value={value ? String(value) : ''} onValueChange={(v) => onChange(Number(v))} disabled={isEmpty}>
        <SelectTrigger id={id} className="w-full">
          <SelectValue placeholder={isEmpty ? 'Chưa có chính sách nào đang dùng' : 'Chọn chính sách đang dùng'} />
        </SelectTrigger>
        <SelectContent>
          {policies.map((p) => (
            <SelectItem key={p.id} value={String(p.id)}>
              {p.name} ({p.code})
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {isEmpty && (
        <p className="text-xs text-muted-foreground">
          {can('leave_type', 'write') ? (
            <>
              Tạo chính sách và để trạng thái đang dùng ở{' '}
              <Link to={appRoutes.hr.leavePolicies} className="font-medium text-primary underline">
                Thiết lập › Chính sách nghỉ phép
              </Link>
              .
            </>
          ) : (
            'Nhờ quản trị nhân sự tạo chính sách nghỉ phép trước khi phân bổ.'
          )}
        </p>
      )}
    </>
  )
}
