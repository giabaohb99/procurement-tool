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
import { concurrentRowsAtOldCompany } from '../utils/employee-concurrent-display'
import { useSaveEmployee } from './use-employees'

/** Cờ điều khiển gửi kèm PATCH — câu trả lời của các hộp hỏi trước khi lưu (không phải ô hồ sơ). */
export type SaveControls = Pick<
  EmployeeProfileUpdate,
  'keep_old_department' | 'end_old_company_concurrent' | 'keep_concurrent_ids'
>

/** Lần lưu đang chờ một hộp hỏi — giữ giá trị form + câu trả lời của các hộp TRƯỚC đó. */
export interface PendingSave {
  values: EmployeeProfileFormValues
  controls: SaveControls
}

/** Đổi pháp nhân chính mà còn dòng kiêm nhiệm ở công ty cũ (duoc-CR-755, Q4). */
export interface PendingCompanyChange extends PendingSave {
  rows: EmployeeConcurrent[]
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
 * 1. Đổi phòng chính → giữ phòng cũ làm kiêm nhiệm hay gỡ (bao-CR-709, `keep_old_department`).
 * 2. Đổi pháp nhân chính → dòng kiêm nhiệm nào ở công ty cũ được GIỮ (duoc-CR-755 Q4, `end_old_company_concurrent` +
 *    `keep_concurrent_ids`). Không còn dòng nào chưa hết hạn ở đó thì bỏ qua hộp.
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
   * Đổi pháp nhân chính sang một công ty THẬT khác → backend kết thúc dòng kiêm nhiệm ở công ty cũ (dòng chưa bắt đầu
   * thì xóa). Đọc danh sách MỚI từ máy chủ, không tin bộ đệm, vì câu hỏi này dẫn tới xóa dữ liệu.
   */
  async function continueAfterDepartment(values: EmployeeProfileFormValues, controls: SaveControls) {
    const oldCompany = employee?.company_id ?? 0
    if (oldCompany && values.company_id && values.company_id !== oldCompany) {
      let rows: EmployeeConcurrent[]
      try {
        const list = await queryClient.fetchQuery({
          queryKey: queryKeys.hr.employeeConcurrents(employeeId),
          queryFn: () => employeeConcurrentApi.list(employeeId),
          staleTime: 0,
        })
        rows = concurrentRowsAtOldCompany(list.items, oldCompany)
      } catch {
        toast.error('Không tải được danh sách kiêm nhiệm để hỏi trước khi đổi pháp nhân. Thử lại sau.')
        return
      }
      if (rows.length > 0) {
        setPendingCompany({ values, controls, rows })
        return
      }
    }
    await continueSave(values, controls)
  }

  async function onSubmit(values: EmployeeProfileFormValues) {
    //  Chỉ hỏi khi đổi từ một phòng THẬT sang một phòng THẬT khác. Bỏ trống phòng thì không có gì để giữ.
    const oldDepartment = employee?.department_id ?? 0
    if (oldDepartment && values.department_id && values.department_id !== oldDepartment) {
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
