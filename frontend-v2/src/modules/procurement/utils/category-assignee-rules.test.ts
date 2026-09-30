import { describe, expect, it } from 'vitest'

import { EMPLOYEE_STATUS } from '@/shared/constants/statuses'

import {
  OFFICIAL_EMPLOYEE_STATUS,
  assigneeOptions,
  isOfficialEmployee,
  validateAssigneePair,
  type AssigneeEmployee,
} from './category-assignee-rules'

const official: AssigneeEmployee = {
  id: 1, full_name: 'Nguyễn Văn Chính', code: 'NV01', status: 'official', status_label: 'Chính thức', is_active: true,
}
const other: AssigneeEmployee = {
  id: 2, full_name: 'Lê Thị Phụ', code: 'NV02', status: 'official', status_label: 'Chính thức', is_active: true,
}
const maternity: AssigneeEmployee = {
  id: 3, full_name: 'Trần Thị Bận', code: 'NV03', status: 'maternity_leave', status_label: 'Nghỉ thai sản', is_active: true,
}
const disabled: AssigneeEmployee = {
  id: 4, full_name: 'Phạm Văn Tắt', code: 'NV04', status: 'official', status_label: 'Chính thức', is_active: false,
}
const collaborator: AssigneeEmployee = {
  id: 5, full_name: 'Hồ Cộng Tác', status: 'collaborator', status_label: 'Cộng tác viên', is_active: true,
}
const employees = [official, other, maternity, disabled, collaborator]

describe('isOfficialEmployee — bao-CR-527', () => {
  it('uses the generated status catalog code, not a guessed one', () => {
    //  Đổi mã ở backend mà quên chạy gen_status_ts thì bài này đỏ trước khi ô chọn rỗng im lặng.
    expect(EMPLOYEE_STATUS.map((s) => s.value)).toContain(OFFICIAL_EMPLOYEE_STATUS)
  })

  it('only official AND active counts', () => {
    expect(isOfficialEmployee(official)).toBe(true)
    expect(isOfficialEmployee(maternity)).toBe(false)
    expect(isOfficialEmployee(disabled)).toBe(false)
    expect(isOfficialEmployee(collaborator)).toBe(false)
    expect(isOfficialEmployee({ id: 9, full_name: 'Thiếu mã' })).toBe(false)
    expect(isOfficialEmployee(null)).toBe(false)
  })
})

describe('assigneeOptions — bao-CR-527', () => {
  it('offers only official active staff', () => {
    expect(assigneeOptions(employees).map((o) => o.value)).toEqual([1, 2])
  })

  it('keeps a currently assigned non-official person, labelled with their status', () => {
    const options = assigneeOptions(employees, [3, 0])
    const kept = options.find((o) => o.value === 3)
    expect(kept).toEqual({ value: 3, label: 'Trần Thị Bận · NV03 (Nghỉ thai sản)', official: false })
    expect(options.some((o) => o.value === 4)).toBe(false)
  })

  it('empty catalog → empty list', () => {
    expect(assigneeOptions([], [1])).toEqual([])
  })
})

describe('validateAssigneePair — bao-CR-527', () => {
  it('primary is required', () => {
    expect(validateAssigneePair(0, 0, employees)).toMatch(/NSTM chính/)
    expect(validateAssigneePair(0, 2, employees)).toMatch(/NSTM chính/)
  })

  it('backup is optional but must differ from primary', () => {
    expect(validateAssigneePair(1, 0, employees)).toBeNull()
    expect(validateAssigneePair(1, 2, employees)).toBeNull()
    expect(validateAssigneePair(1, 1, employees)).toMatch(/khác NSTM chính/)
  })

  it('names the person and the status when either side is no longer official', () => {
    expect(validateAssigneePair(3, 0, employees)).toMatch(/Trần Thị Bận.*Nghỉ thai sản/)
    expect(validateAssigneePair(1, 4, employees)).toMatch(/NSTM dự phòng Phạm Văn Tắt.*ngừng hoạt động/)
  })

  it('a person missing from the loaded catalog is left for the backend to judge', () => {
    expect(validateAssigneePair(99, 0, employees)).toBeNull()
  })
})
