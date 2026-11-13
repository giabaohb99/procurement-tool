import { useQueryClient } from '@tanstack/react-query'
import { useRef, useState } from 'react'
import type { UseFormReturn } from 'react-hook-form'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import { employeeConcurrentApi } from '../api/employee-concurrent-api'
import {
  pickWritableProfile,
  type EmployeeProfileFormValues,
  type EmployeeProfileUpdate,
} from '../schemas/employee-schema'
import type { EmployeeDetail } from '../types/employee'
import type { EmployeeConcurrent } from '../types/employee-concurrent'
import type { CompanyChangeConcurrentChoice } from '../utils/company-change-concurrent-choice'
import { concurrentRowsEndingOnCompanyChange, hasOpenCompanyConcurrent } from '../utils/employee-concurrent-display'
import { useSaveEmployee } from './use-employees'

/** Cờ điều khiển gửi kèm PATCH — câu trả lời của các hộp hỏi trước khi lưu (không phải ô hồ sơ). */
export type SaveControls = Pick<EmployeeProfileUpdate, 'keep_old_department' | 'keep_old_company_concurrent'>

/** Lần lưu đang chờ một hộp hỏi — giữ giá trị form + câu trả lời của các hộp TRƯỚC đó. */
export interface PendingSave {
  values: EmployeeProfileFormValues
  controls: SaveControls
}

/** Đổi pháp nhân chính A → C (duoc-CR-756, Q4): hỏi giữ kiêm nhiệm ở A, kèm các dòng sẽ kết thúc. */
export interface PendingCompanyChange extends PendingSave {
  /** Dòng sẽ kết thúc / bị xóa (`concurrentRowsEndingOnCompanyChange`) — có thể rỗng. */
  rows: EmployeeConcurrent[]
  /** Đã có dòng loại Công ty ở công ty cũ còn hiệu lực / sắp tới — không cần (và backend không tạo) dòng giữ thứ hai. */
  oldCompanyKept: boolean
}

interface UseEmployeeProfileSaveFlowArgs {
  employeeId: number
  /** `undefined` khi hồ sơ chưa tải xong — hook vẫn phải gọi trước nhánh return sớm của trang. */
  employee: EmployeeDetail | undefined
  form: UseFormReturn<EmployeeProfileFormValues>
  canReadSensitive: boolean
}

/**
 * Luồng LƯU hồ sơ ở trang chi tiết: ba hộp hỏi nối nhau rồi mới `PATCH`.
 *
 * 1. Chỉ đổi phòng chính (CÙNG công ty) → giữ phòng cũ làm kiêm nhiệm loại Phòng ban hay gỡ (bao-CR-709,
 *    `keep_old_department`).
 * 2. Đổi pháp nhân chính A → C (có hay không đổi phòng) → MỘT câu: vẫn kiêm nhiệm ở công ty cũ A không (duoc-CR-756 Q4,
 *    `keep_old_company_concurrent`), kèm các dòng sẽ kết thúc. Đổi cả pháp nhân lẫn phòng thì KHÔNG hỏi hộp 1 nữa — giữ
 *    phòng cũ ở A nay là giữ cả công ty A (gộp thành một dòng loại Công ty, câu hỏi mở 5). Đã có dòng loại Công ty ở A
 *    còn hiệu lực mà không dòng nào sắp kết thúc thì bỏ qua hộp (backend cũng bỏ qua yêu cầu giữ).
 * 3. Chuyển nghỉ việc / ngừng hoạt động → kiểm việc duyệt đang treo (duoc-CR-665).
 *
 * Mỗi hộp mang theo câu trả lời của hộp TRƯỚC (`controls`); khóa vắng = luật mặc định backend. Tách khỏi trang để trang
 * ngắn lại và để bài kiểm soi được đúng thân PATCH.
 */
export function useEmployeeProfileSaveFlow({ employeeId, employee, form, canReadSensitive }: UseEmployeeProfileSaveFlowArgs) {
  const queryClient = useQueryClient()
  const saveEmployee = useSaveEmployee()
  //  ⚠️ Chặn GỬI HAI LẦN bằng ref, không dựa vào `disabled={isPending}` — `isPending` là state React nên chỉ đúng ở
  //  lần render SAU; bấm 5 lần liền tay từng ra 5 `PATCH` + 5 dòng nhật ký (08/09/2026).
  const submittingRef = useRef(false)
  const [pendingDepartment, setPendingDepartment] = useState<EmployeeProfileFormValues | null>(null)
  const [pendingCompany, setPendingCompany] = useState<PendingCompanyChange | null>(null)
  const [pendingLeave, setPendingLeave] = useState<PendingSave | null>(null)

  async function saveProfile(values: EmployeeProfileFormValues, controls: SaveControls) {
    if (submittingRef.current) return
    submittingRef.current = true
    try {
      //  Bỏ các ô NHẠY CẢM khi người lưu không được xem — backend che bằng chuỗi RỖNG, gửi lên là đè rỗng lên số tài
      //  khoản ngân hàng thật (`pickWritableProfile`).
      await saveEmployee.mutateAsync({
        id: employeeId,
        values: { ...pickWritableProfile(values, canReadSensitive, employee?.extra_phones), ...controls },
      })
      //  Lưu xong coi giá trị vừa gửi là mốc sạch (duoc-CR-627); hai ô lương về "không đụng" (duoc-CR-693).
      form.reset({ ...values, salary_monthly: null, allowance_monthly: null })
    } finally {
      submittingRef.current = false
    }
  }

  async function continueSave(values: EmployeeProfileFormValues, controls: SaveControls) {
    const leaving =
      (values.status === 'resigned' && employee?.status !== 'resigned') ||
      (!values.is_active && employee?.is_active === true)
    if (leaving) {
      setPendingLeave({ values, controls })
      return
    }
    await saveProfile(values, controls)
  }

  /**
   * Đổi pháp nhân chính từ một công ty THẬT sang một công ty THẬT khác → backend kết thúc dòng loại Phòng ban ở công ty
   * cũ và dòng loại Công ty trùng công ty mới (dòng chưa bắt đầu thì xóa). Đọc danh sách MỚI từ máy chủ, không tin bộ
   * đệm, vì câu hỏi này dẫn tới xóa dữ liệu.
   */
  async function continueAfterDepartment(values: EmployeeProfileFormValues, controls: SaveControls) {
    const oldCompany = employee?.company_id ?? 0
    if (oldCompany && values.company_id && values.company_id !== oldCompany) {
      let rows: EmployeeConcurrent[]
      let oldCompanyKept: boolean
      try {
        const list = await queryClient.fetchQuery({
          queryKey: queryKeys.hr.employeeConcurrents(employeeId),
          queryFn: () => employeeConcurrentApi.list(employeeId),
          staleTime: 0,
        })
        rows = concurrentRowsEndingOnCompanyChange(list.items, oldCompany, values.company_id)
        oldCompanyKept = hasOpenCompanyConcurrent(list.items, oldCompany)
      } catch {
        toast.error('Không tải được danh sách kiêm nhiệm để hỏi trước khi đổi pháp nhân. Thử lại sau.')
        return
      }
      if (rows.length > 0 || !oldCompanyKept) {
        setPendingCompany({ values, controls, rows, oldCompanyKept })
        return
      }
    }
    await continueSave(values, controls)
  }

  async function onSubmit(values: EmployeeProfileFormValues) {
    //  Chỉ hỏi khi đổi từ một phòng THẬT sang một phòng THẬT khác TRONG CÙNG công ty. Bỏ trống phòng thì không có gì để
    //  giữ; đổi cả pháp nhân thì câu "giữ ở công ty cũ" của hộp đổi pháp nhân đã thay câu này (duoc-CR-756).
    const oldDepartment = employee?.department_id ?? 0
    const sameCompany = values.company_id === (employee?.company_id ?? 0)
    if (sameCompany && oldDepartment && values.department_id && values.department_id !== oldDepartment) {
      setPendingDepartment(values)
      return
    }
    await continueAfterDepartment(values, {})
  }

  function answerKeepOldDepartment(keepOld: boolean) {
    if (!pendingDepartment) return
    const values = pendingDepartment
    setPendingDepartment(null)
    void continueAfterDepartment(values, { keep_old_department: keepOld })
  }

  function answerCompanyChange(choice: CompanyChangeConcurrentChoice) {
    if (!pendingCompany) return
    const { values, controls } = pendingCompany
    setPendingCompany(null)
    void continueSave(values, { ...controls, ...choice })
  }

  function confirmLeave() {
    if (!pendingLeave) return
    const { values, controls } = pendingLeave
    setPendingLeave(null)
    void saveProfile(values, controls)
  }

  return {
    saveEmployee,
    onSubmit,
    pendingDepartment,
    pendingCompany,
    pendingLeave,
    answerKeepOldDepartment,
    answerCompanyChange,
    confirmLeave,
    cancelDepartment: () => setPendingDepartment(null),
    cancelCompany: () => setPendingCompany(null),
    cancelLeave: () => setPendingLeave(null),
  }
}
