import { describe, expect, it } from 'vitest'

import type { Employee } from '../types/employee'
import type { EmployeeConcurrent } from '../types/employee-concurrent'
import type { EmployeeWorkHistory } from '../types/employee-work-history'
import {
  planApplyPrompt,
  workHistoryRowToApplyValues,
  type ApplyPromptValues,
} from './employee-work-history-apply'

const TODAY = '2026-10-03'

const employee: Employee = {
  id: 1,
  code: 'NSU001',
  full_name: 'Trần Minh',
  email: '',
  phone: '',
  company_id: 10,
  company_name: 'Công ty cũ',
  department_id: 20,
  department_name: 'Phòng cũ',
  position: 'Nhân viên',
  position_id: 30,
  role_name: '',
  status: 'official',
  status_label: 'Đang làm',
  is_active: true,
  gender: 0,
  avatar: '',
  signature: '',
}

function values(overrides: Partial<ApplyPromptValues>): ApplyPromptValues {
  return {
    event_type: 1,
    from_date: TODAY,
    to_date: '',
    company_id: 0,
    department_id: 0,
    position_id: 0,
    ...overrides,
  }
}

/** Dòng tối thiểu cho `existingRows` — chỉ cần ba trường `hasLaterMainRow` đọc tới. */
function existingRow(overrides: Partial<EmployeeWorkHistory>): EmployeeWorkHistory {
  return {
    id: 2,
    employee_id: 1,
    event_type: 3,
    from_date: '2026-11-01',
    to_date: null,
    company_id: 10,
    company_name: 'Công ty cũ',
    department_id: 20,
    department_name: 'Phòng cũ',
    position_id: 30,
    position_label: 'Nhân viên',
    decision_no: '',
    decision_date: null,
    note: '',
    applied_at: null,
    file_count: 0,
    is_current: true,
    can_apply: true,
    ...overrides,
  }
}

describe('planApplyPrompt — nhóm chính (Tuyển dụng/Điều chuyển/Bổ nhiệm/Miễn nhiệm)', () => {
  it('ngày hiệu lực trong TƯƠNG LAI → không hỏi', () => {
    expect(
      planApplyPrompt(values({ department_id: 99, from_date: '2026-10-04' }), employee, [], TODAY),
    ).toBeNull()
  })

  it('đúng HÔM NAY và khác hồ sơ → hỏi, nêu giá trị CŨ → MỚI', () => {
    expect(
      planApplyPrompt(
        values({ department_id: 99, department_label: 'Phòng mới' }),
        employee,
        [],
        TODAY,
      ),
    ).toEqual({
      kind: 'profile',
      changes: ['Phòng ban: Phòng cũ → Phòng mới'],
    })
  })

  it('khác hồ sơ nhưng KHÔNG có nhãn mới (chưa tra được danh mục) → nói "(chưa gán)"', () => {
    expect(planApplyPrompt(values({ department_id: 99 }), employee, [], TODAY)).toEqual({
      kind: 'profile',
      changes: ['Phòng ban: Phòng cũ → (chưa gán)'],
    })
  })

  it('đổi CẢ pháp nhân, phòng ban, chức vụ → liệt kê đủ ba dòng cũ → mới', () => {
    expect(
      planApplyPrompt(
        values({
          company_id: 11,
          company_label: 'Công ty mới',
          department_id: 99,
          department_label: 'Phòng mới',
          position_id: 31,
          position_label: 'Trưởng phòng',
        }),
        employee,
        [],
        TODAY,
      ),
    ).toEqual({
      kind: 'profile',
      changes: [
        'Pháp nhân: Công ty cũ → Công ty mới',
        'Phòng ban: Phòng cũ → Phòng mới',
        'Chức vụ: Nhân viên → Trưởng phòng',
      ],
    })
  })

  it('dòng ĐÃ KẾT THÚC (to_date < hôm nay) → không hỏi dù có khác hồ sơ', () => {
    expect(
      planApplyPrompt(
        values({ department_id: 99, to_date: '2026-10-01' }),
        employee,
        [],
        TODAY,
      ),
    ).toBeNull()
  })

  it('KHỚP hồ sơ hiện tại (không ô nào khác) → không hỏi', () => {
    expect(
      planApplyPrompt(
        values({ company_id: 10, department_id: 20, position_id: 30 }),
        employee,
        [],
        TODAY,
      ),
    ).toBeNull()
  })

  it('loại "Khác" (9) không nằm trong APPLICABLE → không hỏi dù khác hồ sơ', () => {
    expect(
      planApplyPrompt(values({ event_type: 9, department_id: 99 }), employee, [], TODAY),
    ).toBeNull()
  })

  it('id 0 ở ô company/department/position → KHÔNG coi là thay đổi', () => {
    expect(
      planApplyPrompt(
        values({ company_id: 0, department_id: 0, position_id: 0 }),
        employee,
        [],
        TODAY,
      ),
    ).toBeNull()
  })

  it('ngày rỗng → không hỏi', () => {
    expect(
      planApplyPrompt(values({ department_id: 99, from_date: '' }), employee, [], TODAY),
    ).toBeNull()
  })

  it('ngày không hợp lệ → không hỏi', () => {
    expect(
      planApplyPrompt(values({ department_id: 99, from_date: 'không phải ngày' }), employee, [], TODAY),
    ).toBeNull()
  })

  it('M6 — có dòng CHÍNH khác hiệu lực MUỘN HƠN (nhập bù lịch sử cũ) → không hỏi', () => {
    const rows = [existingRow({ id: 2, event_type: 3, from_date: '2026-12-01' })]
    expect(
      planApplyPrompt(values({ department_id: 99 }), employee, [], TODAY, rows, 0),
    ).toBeNull()
  })

  it('M6 — dòng chính khác hiệu lực SỚM HƠN (không phải nhập bù) → vẫn hỏi', () => {
    const rows = [existingRow({ id: 2, event_type: 3, from_date: '2026-01-01' })]
    expect(
      planApplyPrompt(values({ department_id: 99 }), employee, [], TODAY, rows, 0),
    ).toEqual({ kind: 'profile', changes: ['Phòng ban: Phòng cũ → (chưa gán)'] })
  })

  it('M6 — dòng muộn hơn trong existingRows CHÍNH LÀ dòng đang sửa (editingId) → vẫn hỏi', () => {
    //  Dòng đang sửa còn giữ `from_date` CŨ (muộn hơn giá trị MỚI đang gửi) —
    //  phải tự loại khỏi existingRows, không thì tưởng có dòng chính khác.
    const rows = [existingRow({ id: 5, event_type: 3, from_date: '2026-12-01' })]
    expect(
      planApplyPrompt(values({ department_id: 99 }), employee, [], TODAY, rows, 5),
    ).toEqual({ kind: 'profile', changes: ['Phòng ban: Phòng cũ → (chưa gán)'] })
  })
})

/** Dòng kiêm nhiệm tối thiểu — `planApplyPrompt` tìm dòng đích theo `work_history_id`. */
function concurrentRow(overrides: Partial<EmployeeConcurrent>): EmployeeConcurrent {
  return {
    id: 70,
    employee_id: 1,
    kind: 1,
    kind_label: 'Phòng ban',
    company_id: 10,
    company_name: 'Công ty cũ',
    department_id: 50,
    department_name: 'Phòng Kế toán',
    position_id: 0,
    position_label: '',
    from_date: TODAY,
    to_date: null,
    decision_no: '',
    decision_date: null,
    note: '',
    counts_scope: true,
    work_history_id: 9,
    status: 2,
    status_label: 'Đang hiệu lực',
    file_count: 0,
    ...overrides,
  }
}

describe('planApplyPrompt — Kiêm nhiệm (loại 4, duoc-CR-755; hai loại ở duoc-CR-756)', () => {
  it('công ty KHÁC công ty chính → hỏi THÊM dòng loại Công ty: nêu công ty, KHÔNG nêu phòng của dòng QTCT', () => {
    expect(
      planApplyPrompt(
        values({
          event_type: 4,
          department_id: 50,
          department_label: 'Kế toán',
          company_id: 11,
          company_label: 'DEGO B',
          to_date: '2026-12-31',
        }),
        employee,
        [],
        TODAY,
      ),
    ).toEqual({
      kind: 'profile',
      changes: ['Thêm dòng kiêm nhiệm: công ty "DEGO B", từ 03/10/2026 đến 31/12/2026'],
    })
  })

  it('công ty trống = công ty chính → loại Phòng ban, câu chỉ nêu phòng; chưa có ngày kết thúc thì nói rõ', () => {
    expect(
      planApplyPrompt(values({ event_type: 4, department_id: 50 }), employee, [], TODAY),
    ).toEqual({
      kind: 'profile',
      changes: ['Thêm dòng kiêm nhiệm: phòng này, từ 03/10/2026 chưa kết thúc'],
    })
  })

  it('trùng đúng phòng + công ty CHÍNH → không hỏi (backend không tạo dòng)', () => {
    expect(planApplyPrompt(values({ event_type: 4, department_id: 20 }), employee, [], TODAY)).toBeNull()
  })

  it('công ty KHÁC mà phòng trùng phòng chính → vẫn hỏi THÊM (loại Công ty bỏ phòng, không có gì trùng)', () => {
    const prompt = planApplyPrompt(values({ event_type: 4, department_id: 20, company_id: 11 }), employee, [], TODAY)
    expect(prompt?.kind).toBe('profile')
  })

  it('so theo work_history_id, KHÔNG theo phòng: dòng kiêm nhiệm cùng phòng nhưng của dòng khác → vẫn hỏi THÊM', () => {
    const other = concurrentRow({ work_history_id: 3 })
    const prompt = planApplyPrompt(values({ event_type: 4, department_id: 50 }), employee, [other], TODAY, [], 9)
    expect(prompt).toEqual({ kind: 'profile', changes: [expect.stringMatching(/^Thêm dòng kiêm nhiệm/)] })
  })

  it('dòng tạo MỚI (editingId = 0) không bao giờ khớp dòng chép từ dữ liệu cũ (work_history_id = 0)', () => {
    const legacy = concurrentRow({ work_history_id: 0 })
    const prompt = planApplyPrompt(values({ event_type: 4, department_id: 50 }), employee, [legacy], TODAY, [], 0)
    expect(prompt).toEqual({ kind: 'profile', changes: [expect.stringMatching(/^Thêm dòng kiêm nhiệm/)] })
  })

  it('đã có dòng nối và giá trị KHÔNG đổi → không hỏi', () => {
    const linked = concurrentRow({})
    expect(
      planApplyPrompt(values({ event_type: 4, department_id: 50 }), employee, [linked], TODAY, [], 9),
    ).toBeNull()
  })

  it('đã có dòng nối mà ngày kết thúc đổi → hỏi CẬP NHẬT', () => {
    const linked = concurrentRow({})
    expect(
      planApplyPrompt(
        values({ event_type: 4, department_id: 50, department_label: 'Kế toán', to_date: '2026-11-30' }),
        employee,
        [linked],
        TODAY,
        [],
        9,
      ),
    ).toEqual({
      kind: 'profile',
      changes: ['Cập nhật dòng kiêm nhiệm: phòng "Kế toán", từ 03/10/2026 đến 30/11/2026'],
    })
  })

  it('dòng đã kết thúc + có dòng nối còn mở → hỏi KẾT THÚC (thành Đã hết, không gỡ)', () => {
    const linked = concurrentRow({ from_date: '2026-09-01' })
    const prompt = planApplyPrompt(
      values({ event_type: 4, department_id: 50, from_date: '2026-09-01', to_date: '2026-10-01' }),
      employee,
      [linked],
      TODAY,
      [],
      9,
    )
    expect(prompt).toEqual({ kind: 'profile', changes: [expect.stringMatching(/^Kết thúc dòng kiêm nhiệm/)] })
  })

  it('dòng đã kết thúc mà CHƯA có dòng nối → không hỏi (backend không tạo dòng đã chết)', () => {
    expect(
      planApplyPrompt(values({ event_type: 4, department_id: 50, to_date: '2026-10-01' }), employee, [], TODAY, [], 9),
    ).toBeNull()
  })

  it('loại Công ty KHÔNG cần phòng: dòng QTCT không chọn phòng vẫn hỏi THÊM', () => {
    const prompt = planApplyPrompt(
      values({ event_type: 4, company_id: 11, company_label: 'DEGO B' }),
      employee,
      [],
      TODAY,
    )
    expect(prompt).toEqual({ kind: 'profile', changes: [expect.stringMatching(/^Thêm dòng kiêm nhiệm: công ty "DEGO B"/)] })
  })

  it('cùng công ty chính mà KHÔNG chọn phòng → không hỏi (loại Phòng ban cần phòng)', () => {
    expect(planApplyPrompt(values({ event_type: 4, company_id: 10 }), employee, [], TODAY)).toBeNull()
  })

  it('hồ sơ chưa gắn pháp nhân chính → không hỏi (backend chặn 400 cả hai loại)', () => {
    const noCompany = { ...employee, company_id: 0, company_name: '' }
    expect(
      planApplyPrompt(values({ event_type: 4, company_id: 11, department_id: 50 }), noCompany, [], TODAY),
    ).toBeNull()
  })

  it('Áp lại sang công ty khác: dòng nối đang loại Phòng ban → hỏi CẬP NHẬT (đổi loại tại chỗ, cùng id)', () => {
    const linked = concurrentRow({})
    const prompt = planApplyPrompt(
      values({ event_type: 4, department_id: 50, company_id: 11, company_label: 'DEGO B' }),
      employee,
      [linked],
      TODAY,
      [],
      9,
    )
    expect(prompt).toEqual({ kind: 'profile', changes: ['Cập nhật dòng kiêm nhiệm: công ty "DEGO B", từ 03/10/2026 chưa kết thúc'] })
  })

  it('dòng nối loại Công ty giữ nguyên công ty + ngày → không hỏi, dù phòng trên dòng QTCT khác (loại Công ty không có phòng)', () => {
    const linked = concurrentRow({ kind: 2, kind_label: 'Công ty', company_id: 11, department_id: 0, department_name: '' })
    expect(
      planApplyPrompt(values({ event_type: 4, department_id: 50, company_id: 11 }), employee, [linked], TODAY, [], 9),
    ).toBeNull()
  })

  it('M6 — kiêm nhiệm nhập bù lịch sử cũ (có dòng chính muộn hơn) → không hỏi', () => {
    const rows = [existingRow({ id: 2, event_type: 1, from_date: '2026-12-01' })]
    expect(
      planApplyPrompt(values({ event_type: 4, department_id: 50 }), employee, [], TODAY, rows, 0),
    ).toBeNull()
  })
})

describe('planApplyPrompt — Thôi việc (loại 6)', () => {
  it('hôm nay → kind resign với resignDate = ngày của DÒNG', () => {
    expect(planApplyPrompt(values({ event_type: 6 }), employee, [], TODAY)).toEqual({
      kind: 'resign',
      resignDate: TODAY,
    })
  })

  it('quá khứ → kind resign với resignDate = ngày của DÒNG (nhập bù)', () => {
    expect(
      planApplyPrompt(values({ event_type: 6, from_date: '2026-09-01' }), employee, [], TODAY),
    ).toEqual({ kind: 'resign', resignDate: '2026-09-01' })
  })

  it('tương lai → không hỏi (A8 — quay lại bấm Áp khi tới ngày)', () => {
    expect(
      planApplyPrompt(values({ event_type: 6, from_date: '2026-12-25' }), employee, [], TODAY),
    ).toBeNull()
  })

  it('hồ sơ ĐÃ nghỉ việc CÙNG ngày → không hỏi (no-op)', () => {
    const resigned: Employee = { ...employee, status: 'resigned', resign_date: TODAY }
    expect(planApplyPrompt(values({ event_type: 6 }), resigned, [], TODAY)).toBeNull()
  })

  it('hồ sơ ĐÃ nghỉ việc nhưng KHÁC ngày → hỏi', () => {
    const resigned: Employee = { ...employee, status: 'resigned', resign_date: '2026-01-01' }
    expect(planApplyPrompt(values({ event_type: 6 }), resigned, [], TODAY)).toEqual({
      kind: 'resign',
      resignDate: TODAY,
    })
  })

  it('M6 CỐ Ý KHÔNG áp cho Thôi việc: có dòng chính muộn hơn vẫn hỏi (nhập bù resign quá khứ)', () => {
    //  Khác nhóm chính/kiêm nhiệm — hệ quả khóa tài khoản nặng hơn nên không tự
    //  suy luận bỏ qua câu hỏi chỉ vì có một dòng chính muộn hơn.
    const rows = [existingRow({ id: 2, event_type: 1, from_date: '2026-12-01' })]
    expect(
      planApplyPrompt(
        values({ event_type: 6, from_date: '2026-09-01' }),
        employee,
        [],
        TODAY,
        rows,
        0,
      ),
    ).toEqual({ kind: 'resign', resignDate: '2026-09-01' })
  })
})

describe('workHistoryRowToApplyValues', () => {
  it('chuyển đúng các trường, kèm NHÃN đã có sẵn trên dòng (không cần tra danh mục)', () => {
    const row = existingRow({
      event_type: 3,
      from_date: '2026-05-01',
      to_date: '2026-06-01',
      company_id: 10,
      company_name: 'Công ty A',
      department_id: 20,
      department_name: 'Phòng B',
      position_id: 30,
      position_label: 'Trưởng phòng',
    })

    expect(workHistoryRowToApplyValues(row)).toEqual({
      event_type: 3,
      from_date: '2026-05-01',
      to_date: '2026-06-01',
      company_id: 10,
      company_label: 'Công ty A',
      department_id: 20,
      department_label: 'Phòng B',
      position_id: 30,
      position_label: 'Trưởng phòng',
    })
  })

  it('to_date null (đang hiệu lực) → chuyển về chuỗi rỗng, không phải "null"', () => {
    const row = existingRow({ to_date: null })
    expect(workHistoryRowToApplyValues(row).to_date).toBe('')
  })
})
