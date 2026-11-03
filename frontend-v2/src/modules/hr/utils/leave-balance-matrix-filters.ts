import type { LeaveBalanceMatrixEmployeeStatus } from '../api/leave-balance-matrix-api'

/** Mốc "Tất cả phòng ban" là CHUỖI, không phải `0` — `0` là nhóm "chưa gắn phòng" thật (bẫy CR-322). */
export const MATRIX_ALL_DEPARTMENTS = 'all'
export const MATRIX_STATUS_WORKING: LeaveBalanceMatrixEmployeeStatus = 'working'
export const MATRIX_STATUS_OPTIONS: { value: LeaveBalanceMatrixEmployeeStatus; label: string }[] = [
  { value: 'working', label: 'Đang làm' },
  { value: 'resigned', label: 'Đã nghỉ' },
  { value: 'all', label: 'Tất cả nhân sự' },
]
