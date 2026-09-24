import { describe, expect, it } from 'vitest'

import { resolveShownDeptHead } from './dept-head-display'

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
