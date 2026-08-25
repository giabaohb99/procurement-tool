import { Loader2, Save } from 'lucide-react'
import { useState } from 'react'

import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { DepartmentMultiSelect } from '@/shared/ui/department-multi-select'
import { Skeleton } from '@/shared/ui/skeleton'
import { useDepartments } from '../hooks/use-departments'
import { useEmployeeDepartments, useSaveEmployeeDepartments } from '../hooks/use-employees'

interface EmployeeDepartmentCardProps {
  employeeId: number
  /** Nhân sự thuộc pháp nhân nào — chỉ chọn được phòng của chính pháp nhân đó. */
  companyId: number
  canWrite: boolean
  /** Đúng tài khoản đang đăng nhập: khóa lại, không ai tự đổi phòng của mình. */
  laChinhMinh: boolean
}

/**
 * KIÊM NHIỆM PHÒNG BAN — một nhân sự có chân ở nhiều phòng.
 *
 * Thẻ RIÊNG chứ không nhét vào form hồ sơ, vì đây không phải một ô thông tin
 * như «Vị trí / Chức vụ»: phòng ban quyết định **phạm vi dữ liệu** người đó nhìn
 * thấy, và backend gác nó bằng ba chốt chống vượt quyền mà form hồ sơ không có
 * (xem `employee/department_service.py`). Trộn vào cùng nút Lưu là làm mờ đúng
 * chỗ cần rõ.
 *
 * Phòng ĐẦU TIÊN trong danh sách là **phòng chính** — nó khớp với
 * `tab_employee.department_id`, thứ mà bối cảnh phiếu và thông báo cho trưởng
 * phòng vẫn đọc.
 */
export function EmployeeDepartmentCard({
  employeeId,
  companyId,
  canWrite,
  laChinhMinh,
}: EmployeeDepartmentCardProps) {
  const { data, isLoading } = useEmployeeDepartments(employeeId)
  const { data: departments } = useDepartments({ page_size: 500, is_active: true })
  const luu = useSaveEmployeeDepartments(employeeId)

  const [dangChon, setDangChon] = useState<number[]>([])
  //  Chỉ đồng bộ khi người dùng CHƯA tick dở — cùng lỗi đã gặp ở màn Phân quyền
  //  (CR-156): một lượt nạp lại rơi vào giữa lúc đang chọn là mất thứ vừa chọn.
  const [dangChonDo, setDangChonDo] = useState(false)
  if (useHasChanged(data) && !dangChonDo) setDangChon(data?.department_ids ?? [])

  //  Chỉ phòng CÙNG PHÁP NHÂN — backend chặn gán chéo pháp nhân, bày ra ở đây
  //  rồi để người dùng ăn lỗi lúc bấm Lưu là bắt họ đoán luật.
  const chonDuoc = (departments?.items ?? []).filter(
    (item) => !companyId || !item.company_id || item.company_id === companyId,
  )

  if (isLoading) return <Skeleton className="h-40 w-full" />

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Phòng ban &amp; kiêm nhiệm</CardTitle>
        <p className="text-sm text-muted-foreground">
          Phòng <strong>đầu tiên</strong> là phòng chính. Thêm phòng là mở rộng phạm vi
          dữ liệu người này nhìn thấy — không phải chỉ đổi chức danh.
        </p>
      </CardHeader>

      <CardContent className="space-y-3">
        {laChinhMinh && (
          <p className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
            Đây là hồ sơ của chính bạn nên chỉ xem được. Phòng ban quyết định phạm vi dữ
            liệu bạn nhìn thấy, nên phải nhờ một quản trị khác đổi — chốt hai người.
          </p>
        )}

        <DepartmentMultiSelect
          value={dangChon}
          onChange={(ids) => {
            setDangChonDo(true)
            setDangChon(ids)
          }}
          departments={chonDuoc}
          placeholder="Chưa gán phòng ban nào"
          disabled={!canWrite || laChinhMinh}
        />

        {canWrite && !laChinhMinh && (
          <Button
            size="sm"
            onClick={() =>
              luu.mutate(
                { ids: dangChon, primaryId: dangChon[0] },
                { onSuccess: () => setDangChonDo(false) },
              )
            }
            disabled={luu.isPending}
          >
            {luu.isPending ? <Loader2 className="animate-spin" /> : <Save />}
            Lưu phòng ban
          </Button>
        )}
      </CardContent>
    </Card>
  )
}
