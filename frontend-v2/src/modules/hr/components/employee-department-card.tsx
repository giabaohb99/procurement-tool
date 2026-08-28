import { Loader2, Save } from 'lucide-react'
import { useState } from 'react'

import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader } from '@/shared/ui/card'
import { DepartmentMultiSelect } from '@/shared/ui/department-multi-select'
import { SectionHeading } from '@/shared/ui/section-heading'
import { Skeleton } from '@/shared/ui/skeleton'
import { useDepartments } from '../hooks/use-departments'
import { useEmployeeDepartments, useSaveEmployeeDepartments } from '../hooks/use-employees'

interface EmployeeDepartmentCardProps {
  employeeId: number
  /** Nhân sự thuộc pháp nhân nào — chỉ chọn được phòng của chính pháp nhân đó. */
  companyId: number
  /** Phòng CHÍNH, lấy từ ô «Phòng ban» của hồ sơ. Chỉ để loại khỏi danh sách chọn. */
  primaryDepartmentId: number
  canWrite: boolean
  /** Đúng tài khoản đang đăng nhập: khóa lại, không ai tự đổi phòng của mình. */
  isSelf: boolean
  className?: string
}

/**
 * KIÊM NHIỆM — những phòng người này phụ trách **THÊM**, ngoài phòng chính.
 *
 * ⚠️ Phòng CHÍNH không nằm ở đây. Nó là ô «Phòng ban» trong khối *Công việc*
 * của hồ sơ, và vẫn đổi ở đúng chỗ đó. Bản đầu gộp cả hai vào một ô rồi quy ước
 * «phần tử đầu là phòng chính» — một luật ngầm mà người dùng không có cách nào
 * biết, và làm ô «Phòng ban» của hồ sơ thành thừa (khách bác 25/08/2026).
 *
 * Thẻ RIÊNG chứ không nhét vào form hồ sơ: backend gác cửa này bằng ba chốt
 * chống vượt quyền (xem `employee/department_service.py`), trộn chung vào cùng
 * một nút Lưu là làm mờ đúng chỗ cần rõ.
 */
export function EmployeeDepartmentCard({
  employeeId,
  companyId,
  primaryDepartmentId,
  canWrite,
  isSelf,
  className,
}: EmployeeDepartmentCardProps) {
  const { data, isLoading } = useEmployeeDepartments(employeeId)
  const { data: departments } = useDepartments({ page_size: 500, is_active: true })
  const save = useSaveEmployeeDepartments(employeeId)

  const [selection, setSelection] = useState<number[]>([])
  //  Chỉ đồng bộ khi người dùng CHƯA chọn dở — cùng lỗi đã gặp ở màn Phân quyền
  //  (CR-156): một lượt nạp lại rơi vào giữa lúc đang chọn là mất thứ vừa chọn.
  const [dangChonDo, setDangChonDo] = useState(false)
  if (useHasChanged(data) && !dangChonDo) setSelection(data?.extra_department_ids ?? [])

  //  Bỏ PHÒNG CHÍNH khỏi danh sách chọn: nó không phải kiêm nhiệm, và chọn lại
  //  chính nó ở đây thì backend cũng lọc ra.
  //  Chỉ phòng CÙNG PHÁP NHÂN — backend chặn gán chéo pháp nhân, bày ra rồi để
  //  người dùng ăn lỗi lúc bấm Lưu là bắt họ đoán luật.
  const selectable = (departments?.items ?? []).filter(
    (item) =>
      item.id !== primaryDepartmentId &&
      (!companyId || !item.company_id || item.company_id === companyId),
  )

  if (isLoading) return <Skeleton className="h-40 w-full" />

  return (
    <Card className={className}>
      <CardHeader>
        <SectionHeading>Kiêm nhiệm</SectionHeading>
        <p className="text-sm text-muted-foreground">
          Những phòng người này phụ trách thêm, ngoài phòng ban chính.
        </p>
      </CardHeader>

      <CardContent className="space-y-3">
        {isSelf && (
          <p className="rounded-md border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
            Đây là hồ sơ của chính bạn nên chỉ xem được — nhờ một quản trị khác đổi.
          </p>
        )}

        <DepartmentMultiSelect
          value={selection}
          onChange={(ids) => {
            setDangChonDo(true)
            setSelection(ids)
          }}
          departments={selectable}
          placeholder="Không kiêm nhiệm phòng nào"
          disabled={!canWrite || isSelf}
        />

        {canWrite && !isSelf && (
          <Button
            // ⚠️ Cùng cái bẫy với nút ở `employee-account-card`: thẻ này nằm
            // TRONG `<form>` của trang chi tiết, thiếu `type` là mặc định
            // `submit` — bấm «Lưu kiêm nhiệm» kéo theo một lần lưu cả hồ sơ.
            type="button"
            size="sm"
            onClick={() => save.mutate(selection, { onSuccess: () => setDangChonDo(false) })}
            disabled={save.isPending}
          >
            {save.isPending ? <Loader2 className="animate-spin" /> : <Save />}
            Lưu kiêm nhiệm
          </Button>
        )}
      </CardContent>
    </Card>
  )
}
