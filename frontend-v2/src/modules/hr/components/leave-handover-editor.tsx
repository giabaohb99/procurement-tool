import { usePermission } from '@/core/authorization/use-permission'
import { Label } from '@/shared/ui/label'
import { SearchSelect } from '@/shared/ui/search-select'
import { useEmployees } from '../hooks/use-employees'
import type { LeaveHandoverValue } from '../utils/leave-form-values'

interface LeaveHandoverEditorProps {
  value: LeaveHandoverValue[]
  onChange: (rows: LeaveHandoverValue[]) => void
  /** Người đang xin nghỉ — không được tự bàn giao cho chính mình. */
  excludeEmployeeId?: number
}

/**
 * BÀN GIAO CÔNG VIỆC — chỉ **một ô chọn người**, đúng như giấy GNP đang dùng.
 *
 * Không có ô "nội dung bàn giao": người duyệt đã biết người nghỉ làm gì, ghi lại
 * phần việc chỉ là một ô nữa phải gõ mà không ai đọc. Cột `content` của
 * `tab_leave_handover` vẫn còn để dữ liệu cũ hiện được ở bản chỉ xem — form gửi
 * lên chuỗi rỗng.
 *
 * Bảng dưới đáy vẫn là bảng con nhiều dòng và API vẫn nhận danh sách, nên chỗ
 * này giữ kiểu mảng để không phải sửa hợp đồng gửi lên; màn hình chỉ dựng **dòng
 * đầu**.
 *
 * ⚠️ Danh bạ nhân sự là dữ liệu của phân hệ khác: chỉ gọi khi có `employee.read`,
 * nếu không thì cứ mount là ăn toast 403 (bẫy đã dính ở tab «Công nợ» của Nhà
 * cung cấp — CR-106). Thiếu quyền thì tên người đã cử vẫn hiện, chỉ ô chọn là
 * khóa.
 */
export function LeaveHandoverEditor({
  value,
  onChange,
  excludeEmployeeId = 0,
}: LeaveHandoverEditorProps) {
  const { can } = usePermission()
  const canPickEmployee = can('employee', 'read')

  //  Lấy rộng tay: người nhận bàn giao có thể ở phòng khác, và ô chọn đã có sẵn
  //  ô gõ tìm nên danh sách dài không phiền.
  const { data: employeeData } = useEmployees(
    { page_size: 1000, is_active: true },
    { enabled: canPickEmployee },
  )
  const employees = employeeData?.items ?? []

  const row = value[0] ?? { employee_id: 0, employee_name: '', content: '' }

  const pick = (id: string) => {
    const employeeId = Number(id) || 0
    if (!employeeId) return onChange([])
    const picked = employees.find((e) => e.id === employeeId)
    //  Giữ nguyên `content` của dữ liệu cũ: form không cho sửa nữa, nhưng xóa
    //  trắng phần việc đã ghi từ trước chỉ vì người dùng đổi người là mất dữ liệu.
    onChange([{ ...row, employee_id: employeeId, employee_name: picked?.full_name ?? '' }])
  }

  const options = employees
    .filter((e) => e.id !== excludeEmployeeId)
    .map((e) => ({ value: String(e.id), label: `${e.full_name} (${e.code})` }))

  //  Trả về ĐÚNG MỘT ô, không kèm lưới bao ngoài: form đơn nghỉ phép chỉ còn một
  //  thẻ duy nhất và ô này nằm chung lưới với các ô khác của nó.
  return (
    <div className="space-y-1.5">
      <Label>Người nhận bàn giao</Label>
      {canPickEmployee ? (
        <SearchSelect
          value={row.employee_id ? String(row.employee_id) : ''}
          onChange={pick}
          options={options}
          placeholder="Chọn người nhận bàn giao"
          searchPlaceholder="Tìm theo tên hoặc mã…"
          emptyMessage="Không tìm thấy nhân sự nào."
          clearable
        />
      ) : (
        //  Không có quyền đọc danh bạ: hiện tên đã lưu, không dựng ô chọn rỗng
        //  để người dùng bấm vào rồi thấy danh sách trống.
        <span className="block truncate rounded-md border bg-muted/30 px-3 py-2 text-sm text-muted-foreground">
          {row.employee_name || (row.employee_id ? `#${row.employee_id}` : 'Chưa cử ai')}
        </span>
      )}
    </div>
  )
}
