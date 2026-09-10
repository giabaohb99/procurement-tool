import { TriangleAlert } from 'lucide-react'

import type { DataTableColumn } from '@/shared/data-table'
import { Avatar, AvatarFallback, AvatarImage } from '@/shared/ui/avatar'
import { Badge } from '@/shared/ui/badge'
import { formatDateTime } from '@/shared/utils/format-date'
import { employeeInitials, type Employee } from '../types/employee'

/**
 * Cột của bảng DANH SÁCH NHÂN SỰ ở khổ rộng.
 *
 * Tách khỏi trang vì nó là HẰNG — không đọc state nào của màn — và mười hai cột
 * khai tay chiếm hơn một phần ba tệp trang. Cùng cách `company-columns.tsx` và
 * `department-columns.tsx`.
 *
 * ⚠️ Ở khổ điện thoại bảng này KHÔNG dựng — `DataTable` đổi sang `EmployeeCard`.
 * Thêm cột ở đây thì cân nhắc luôn xem thẻ có cần nói điều đó không; hai bên cố
 * ý không giống nhau, nhưng lệch thì phải là lệch có chủ ý.
 */
export const EMPLOYEE_COLUMNS: DataTableColumn<Employee>[] = [
  {
    key: 'avatar',
    // Có nhãn để còn hiện được trong menu "Cột" (mục không tên là mục trống).
    header: 'Ảnh',
    width: 72,
    minWidth: 56,
    cell: (employee) => (
      <Avatar className="size-7">
        <AvatarImage src={employee.avatar} alt={employee.full_name} />
        <AvatarFallback className="text-xs">{employeeInitials(employee.full_name)}</AvatarFallback>
      </Avatar>
    ),
  },
  { key: 'code', header: 'Mã NV', width: 140, sortable: true, cell: (e) => e.code },
  {
    key: 'full_name',
    header: 'Họ tên',
    width: 260,
    sortable: true,
    // Ẩn cột tên thì bảng không còn nhận ra ai với ai.
    hideable: false,
    cell: (e) => <span className="truncate">{e.full_name}</span>,
  },
  {
    key: 'email',
    header: 'Email',
    width: 220,
    cell: (e) => <span className="text-muted-foreground">{e.email || '—'}</span>,
  },
  {
    //  Cột `company_id` vốn có trong bảng nhưng chưa bao giờ ra tới màn hình
    //  (26/08/2026). Đứng TRƯỚC phòng ban vì pháp nhân là cấp trên của
    //  phòng ban, và cùng tên phòng có thể tồn tại ở nhiều pháp nhân.
    key: 'company_name',
    header: 'Công ty',
    width: 180,
    cell: (e) => e.company_name || '—',
  },
  {
    key: 'department_name',
    header: 'Phòng ban',
    width: 180,
    cell: (e) => e.department_name || '—',
  },
  //  Cột đọc NHÃN (`position`) chứ không join sang danh mục: backend chép
  //  sẵn tên vào đó và giữ đồng bộ khi đổi tên (duoc-CR-320), nên một câu
  //  truy vấn là đủ. Bộ lọc thì ngược lại — lọc theo KHÓA, xem
  //  `hr-filter-fields.ts`.
  { key: 'position', header: 'Chức vụ', width: 180, cell: (e) => e.position || '—' },
  {
    //  Ba cột của HRM Đợt 2. `compactHidden` không có ở `DataTable` (đó là
    //  của `LinesTable`), nên để mặc định HIỆN — người dùng ẩn bớt bằng menu
    //  "Cột" và `storageKey` nhớ lựa chọn đó.
    key: 'employment_type_label',
    header: 'Hình thức',
    width: 150,
    cell: (e) => e.employment_type_label || '—',
  },
  {
    key: 'job_level_label',
    header: 'Cấp bậc',
    width: 150,
    cell: (e) => e.job_level_label || '—',
  },
  {
    //  ⚠️ K5 — cảnh báo hồ sơ THIẾU người quản lý trực tiếp. Ô này là thứ bộ
    //  máy duyệt đọc để tìm người ký; bỏ trống thì đơn từ lặng lẽ chạy về
    //  trưởng bộ phận, không ai biết là đã đi sai đường. Cột hiện thẳng cảnh
    //  báo chứ không phải một dấu gạch ngang như mọi ô rỗng khác.
    key: 'direct_manager_name',
    header: 'Quản lý trực tiếp',
    width: 200,
    cell: (e) =>
      e.direct_manager_name ? (
        e.direct_manager_name
      ) : (
        <span className="inline-flex items-center gap-1 text-destructive">
          <TriangleAlert className="size-3.5" />
          Chưa gán
        </span>
      ),
  },
  {
    key: 'status',
    header: 'Tình trạng',
    width: 140,
    cell: (e) => (
      // B-03: so với MÃ, hiện NHÃN. Bản cũ so với chuỗi 'Chính thức' — sau khi
      // chuyển mã thì không dòng nào còn tô đậm nữa mà chẳng có lỗi nào nổ ra.
      <Badge variant={e.status === 'official' ? 'default' : 'secondary'}>
        {e.status_label || e.status || '—'}
      </Badge>
    ),
  },
  {
    // bao-CR-300 (ticket 21) — cột "Ngày cập nhật", bấm lần đầu ra mới nhất trước.
    key: 'updated_at',
    header: 'Ngày cập nhật',
    width: 150,
    sortable: true,
    sortDescFirst: true,
    cell: (e) => formatDateTime(e.updated_at) || '',
  },
]
