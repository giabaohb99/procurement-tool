import { ArrowLeft, Lock, Printer } from 'lucide-react'
import { useNavigate, useParams } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { ErrorState } from '@/shared/ui/error-state'
import { Skeleton } from '@/shared/ui/skeleton'
import { EmployeeInfoPrintSheet } from '../components/employee-info-print-sheet'
import { useMyFamilies } from '../hooks/use-employee-change-requests'
import {
  useCanReadSensitive,
  useEmployeeContacts,
  useEmployeeFamilies,
} from '../hooks/use-employee-profile'
import { useEmployee, useMyEmployee } from '../hooks/use-employees'
import { useMyContacts } from '../hooks/use-my-contact'
import type { Employee, EmployeeContact, EmployeeFamily } from '../types/employee'

/** CSS in — cùng khuôn trang in đơn nghỉ phép: A4 dọc, lề do tờ giấy tự mang, giấu mọi thứ ngoài tờ. */
const PRINT_STYLES = `
  @page { size: A4 portrait; margin: 0; }
  @media print {
    html, body { margin: 0 !important; padding: 0 !important; background: #fff !important; }
    .no-print, .tsqd-parent-container, [class*="tsqd"], [data-sonner-toaster] { display: none !important; }
    .a4-print-page { padding: 0 !important; background: transparent !important; min-height: 0 !important; }
    .a4-print-sheet {
      margin: 0 !important;
      box-shadow: none !important;
      border: none !important;
      width: 100% !important;
      min-height: 0 !important;
    }
  }
`

interface PrintFrameProps {
  employee: Employee | null | undefined
  contacts: readonly EmployeeContact[]
  families: readonly EmployeeFamily[]
  isLoading: boolean
  /** Hai bảng con bị chặn vì thiếu quyền nhạy cảm — nói ra để người in khỏi tưởng hồ sơ trống. */
  peopleHidden?: boolean
  onBack: () => void
}

function EmployeeInfoPrintFrame({
  employee,
  contacts,
  families,
  isLoading,
  peopleHidden = false,
  onBack,
}: PrintFrameProps) {
  if (!isLoading && !employee) {
    return (
      <ErrorState
        fullScreen
        title="Không có hồ sơ để in"
        description="Hồ sơ không tồn tại, bạn không có quyền xem, hoặc tài khoản chưa gắn hồ sơ nhân sự."
      >
        <Button variant="outline" onClick={onBack}>
          <ArrowLeft className="size-4" />
          Quay lại
        </Button>
      </ErrorState>
    )
  }

  return (
    <main className="a4-print-page min-h-[100dvh] bg-slate-200 p-6 max-md:p-2">
      <style>{PRINT_STYLES}</style>

      <div className="no-print mx-auto mb-4 flex max-w-[210mm] flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Button onClick={() => window.print()} disabled={isLoading}>
            <Printer className="size-4" />
            In phiếu / Lưu PDF
          </Button>
          <Button variant="outline" onClick={onBack}>
            <ArrowLeft className="size-4" />
            Quay lại
          </Button>
        </div>
        {employee && (
          <span className="text-sm font-medium text-slate-700">
            {employee.code} · Khổ A4 chuẩn
          </span>
        )}
      </div>

      {peopleHidden && (
        <p
          role="note"
          className="no-print mx-auto mb-4 flex max-w-[210mm] items-start gap-2 rounded-md border bg-white px-3 py-2 text-sm text-slate-700"
        >
          <Lock className="mt-0.5 size-4 shrink-0" />
          Bạn chưa có quyền xem thông tin nhạy cảm: các ô CCCD, ngân hàng, địa chỉ, người báo tin và
          hộ gia đình in ra để trống dù hồ sơ có thể đã có dữ liệu.
        </p>
      )}

      {isLoading || !employee ? (
        <div className="mx-auto max-w-[210mm]">
          <Skeleton className="h-[297mm] w-full bg-white shadow-xl" />
        </div>
      ) : (
        //  Khổ hẹp: tờ A4 rộng 210mm, cho cuộn ngang thay vì bóp méo bản in.
        <div className="overflow-x-auto">
          <EmployeeInfoPrintSheet employee={employee} contacts={contacts} families={families} />
        </div>
      )}
    </main>
  )
}

/**
 * Bản in Phiếu thông tin nhân viên của MỘT hồ sơ — phòng Nhân sự in từ màn chi tiết nhân sự
 * (duoc-CR-676). Cổng quyền `employee.read` khai ở `print-route-access.ts`.
 *
 * Hai bảng con chỉ nạp khi xem được nhóm nhạy cảm (cửa của chúng trả 403 khi thiếu quyền); không
 * xem được thì in bảng trống kèm dòng nhắc trên thanh công cụ.
 */
export function EmployeeInfoPrintPage() {
  const navigate = useNavigate()
  const { id } = useParams()
  const employeeId = Number(id) || 0
  const canReadSensitive = useCanReadSensitive(employeeId)
  const { data: employee, isLoading } = useEmployee(employeeId)
  const contacts = useEmployeeContacts(employeeId, canReadSensitive)
  const families = useEmployeeFamilies(employeeId, canReadSensitive)

  return (
    <EmployeeInfoPrintFrame
      employee={employeeId > 0 ? employee : null}
      contacts={contacts.data ?? []}
      families={families.data ?? []}
      isLoading={employeeId > 0 && (isLoading || contacts.isLoading || families.isLoading)}
      peopleHidden={!canReadSensitive}
      onBack={() =>
        employeeId > 0 ? navigate(appRoutes.hr.employeeDetail(employeeId)) : navigate(-1)
      }
    />
  )
}

/**
 * Bản in phiếu của CHÍNH MÌNH — mở từ Trang cá nhân. Dữ liệu đi ba cửa `/me` (chỉ đòi đăng
 * nhập), nên ai đã gắn hồ sơ cũng in được phiếu của mình mà không cần `employee.read`.
 */
export function MyEmployeeInfoPrintPage() {
  const navigate = useNavigate()
  const { data: employee, isLoading } = useMyEmployee()
  const hasProfile = Boolean(employee)
  const contacts = useMyContacts(hasProfile)
  const families = useMyFamilies(hasProfile)

  return (
    <EmployeeInfoPrintFrame
      employee={employee}
      contacts={contacts.data ?? []}
      families={families.data ?? []}
      isLoading={isLoading || (hasProfile && (contacts.isLoading || families.isLoading))}
      onBack={() => navigate(appRoutes.me)}
    />
  )
}
