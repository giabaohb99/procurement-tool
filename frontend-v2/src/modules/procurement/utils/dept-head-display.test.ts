import { describe, expect, it } from 'vitest'

import { fillApproverDefaults, resolveShownDeptHead } from './dept-head-display'

const DEFAULT_HEAD = { head_of_dept: 'Trưởng phòng mặc định', head_of_dept_id: 7 }

describe('resolveShownDeptHead — ô TBP luôn hiện một người (bao-CR-474)', () => {
  it('phiếu mới chưa chọn TBP: hiện trưởng phòng mặc định thay vì để trống', () => {
    expect(resolveShownDeptHead({ head_of_dept: '', head_of_dept_id: 0 }, true, DEFAULT_HEAD)).toEqual(
      DEFAULT_HEAD,
    )
  })

  it('đã chọn một người khác mặc định: giữ đúng người đã chọn', () => {
    const chosen = { head_of_dept: 'Phó phòng', head_of_dept_id: 9 }
    expect(resolveShownDeptHead(chosen, true, DEFAULT_HEAD)).toEqual(chosen)
  })

  it('phiếu đã khóa (không sửa): hiện đúng tên đã lưu, không đoán thêm', () => {
    const saved = { head_of_dept: 'Tên đã in', head_of_dept_id: 0 }
    expect(resolveShownDeptHead(saved, false, DEFAULT_HEAD)).toEqual(saved)
  })

  it('phòng chưa gán trưởng: không có gì để lùi về thì giữ nguyên', () => {
    const empty = { head_of_dept: '', head_of_dept_id: 0 }
    expect(resolveShownDeptHead(empty, true, { head_of_dept: '', head_of_dept_id: 0 })).toEqual(empty)
    expect(resolveShownDeptHead(empty, true, undefined)).toEqual(empty)
  })
})

describe('fillApproverDefaults — ghi thật người đang hiện xuống phiếu (bao-CR-590)', () => {
  const shown = { head_of_dept: 'Trưởng phòng mặc định', head_of_dept_id: 7 }

  it('new ticket with nothing picked: both boxes take the default head', () => {
    //  LỖI ĐÃ XẢY RA: màn hình hiện TBP mặc định ở cả hai ô nhưng bản nháp giữ id 0, nên
    //  phiếu tạo ra không mang người duyệt dù người dùng thấy ô đã có người.
    const out = fillApproverDefaults({ head_of_dept: '', head_of_dept_id: 0, approver_employee_id: 0 }, shown)
    expect(out).toMatchObject({ head_of_dept: 'Trưởng phòng mặc định', head_of_dept_id: 7, approver_employee_id: 7 })
  })

  it('keeps an approver the user picked on purpose', () => {
    const out = fillApproverDefaults({ head_of_dept: '', head_of_dept_id: 0, approver_employee_id: 42 }, shown)
    expect(out.approver_employee_id).toBe(42)
    expect(out.head_of_dept_id).toBe(7)
  })

  it('keeps a head the user picked and makes it the approver when none was chosen', () => {
    const out = fillApproverDefaults(
      { head_of_dept: 'Phó phòng', head_of_dept_id: 9, approver_employee_id: 0 },
      shown,
    )
    expect(out).toMatchObject({ head_of_dept: 'Phó phòng', head_of_dept_id: 9, approver_employee_id: 9 })
  })

  it('department without a head and nothing picked stays empty so submit can block it', () => {
    const out = fillApproverDefaults(
      { head_of_dept: '', head_of_dept_id: 0, approver_employee_id: null },
      { head_of_dept: '', head_of_dept_id: 0 },
    )
    expect(out.head_of_dept_id).toBe(0)
    expect(out.approver_employee_id).toBe(0)
  })
})
