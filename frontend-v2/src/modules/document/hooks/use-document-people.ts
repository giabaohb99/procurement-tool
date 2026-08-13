import { useMemo } from 'react'

import { useDepartments } from '@/modules/hr/hooks/use-departments'
import { useEmployees } from '@/modules/hr/hooks/use-employees'

/**
 * Nguồn NGƯỜI và PHÒNG BAN cho các ô chọn của phân hệ Văn bản.
 *
 * Lấy thẳng từ phân hệ Nhân sự (API thật) thay vì dựng danh mục riêng: người
 * phê duyệt, người xử lý… đều là nhân sự trong công ty, chép ra một danh sách
 * thứ hai thì hôm sau ai nghỉ việc bên này vẫn còn tên bên kia.
 *
 * Giá trị lưu xuống bản ghi văn bản là TÊN chứ không phải id — phân hệ Văn bản
 * chưa có backend nên không có ràng buộc khóa ngoại nào để giữ id cho đúng.
 */

/** Tên nhân sự đang làm việc, xếp theo bảng chữ cái. */
export function useEmployeeNames(): string[] {
  const { data } = useEmployees({ page_size: 1000, is_active: true })

  return useMemo(() => {
    const names = (data?.items ?? []).map((employee) => employee.full_name).filter(Boolean)
    return [...new Set(names)].sort((a, b) => a.localeCompare(b, 'vi'))
  }, [data])
}

/** Tên phòng ban đang hoạt động. */
export function useDepartmentNames(): string[] {
  const { data } = useDepartments({ page_size: 500 })

  return useMemo(() => {
    const names = (data?.items ?? [])
      .filter((department) => department.is_active)
      .map((department) => department.name)
    return [...new Set(names)].sort((a, b) => a.localeCompare(b, 'vi'))
  }, [data])
}
