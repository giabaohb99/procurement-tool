import { describe, expect, it } from 'vitest'

import {
  emptyLeaveForm,
  formValuesOf,
  REASON_MAX,
  toLeavePayload,
} from './leave-form-values'
import {
  EDITABLE_LEAVE_STATUSES,
  LEAVE_SESSION,
  LEAVE_SESSION_LABELS,
  LEAVE_STATUS,
  LEAVE_STATUS_LABELS,
  LEAVE_UNIT,
  LEAVE_UNIT_LABELS,
  type LeaveRequest,
} from '../types/leave'

/**
 * Hai nhóm bài:
 *  1. dựng giá trị form — chỗ dễ trôi ngày vì múi giờ;
 *  2. ràng buộc hằng số phải khớp `backend/app/modules/leave/constants.py`.
 *     Bộ mã số KHÔNG do `gen_status_ts.py` sinh (kịch bản đó chỉ lo bộ mã
 *     chuỗi), nên hai đầu gõ tay và hai đầu có thể lệch. Bài dưới là cái chốt.
 */

function request(overrides: Partial<LeaveRequest> = {}): LeaveRequest {
  return {
    id: 1,
    code: 'NP001',
    company_id: 1,
    department_id: 2,
    employee_id: 3,
    leave_type_id: 4,
    from_date: '2026-01-05',
    to_date: '2026-01-07',
    from_session: LEAVE_SESSION.AFTERNOON,
    to_session: LEAVE_SESSION.MORNING,
    unit: LEAVE_UNIT.DAY,
    total_days: 2,
    reason: 'Về quê',
    contact_phone: '0900000000',
    contact_address: 'Cà Mau',
    status: LEAVE_STATUS.DRAFT,
    approval_instance_id: 0,
    document_id: 0,
    decision_note: '',
    ...overrides,
  }
}

describe('emptyLeaveForm', () => {
  it('đặt hai đầu ngày là HÔM NAY theo giờ địa phương, không lệch một ngày vì UTC', () => {
    //  `toISOString()` quy về UTC còn Việt Nam lệch +7, nên mở form lúc 0h-7h
    //  sáng thì ô «Từ ngày» từng hiện ngày HÔM QUA. Múi giờ khi chạy test cố
    //  định `Asia/Ho_Chi_Minh` (vitest.config.ts) nên bài này bắt được.
    const now = new Date()
    const expected = [
      now.getFullYear(),
      `${now.getMonth() + 1}`.padStart(2, '0'),
      `${now.getDate()}`.padStart(2, '0'),
    ].join('-')

    const form = emptyLeaveForm()
    expect(form.from_date).toBe(expected)
    expect(form.to_date).toBe(expected)
  })

  it('để `total_days` bằng 0 — dấu hiệu «chưa sửa đè, backend cứ tự tính»', () => {
    expect(emptyLeaveForm().total_days).toBe(0)
  })

  it('mặc định nghỉ CẢ NGÀY ở cả hai đầu', () => {
    const form = emptyLeaveForm()
    expect(form.from_session).toBe(LEAVE_SESSION.FULL)
    expect(form.to_session).toBe(LEAVE_SESSION.FULL)
  })

  it('trả về đối tượng MỚI mỗi lần gọi, không dùng chung một tham chiếu', () => {
    //  Dùng chung thì mở tab thứ hai là gõ đè lên form của tab thứ nhất.
    const a = emptyLeaveForm()
    a.reason = 'đã gõ'
    expect(emptyLeaveForm().reason).toBe('')
  })
})

describe('formValuesOf', () => {
  it('bê nguyên chín ô của tờ đơn, không tự nắn giá trị nào', () => {
    const form = formValuesOf(request())
    expect(form).toEqual({
      leave_type_id: 4,
      from_date: '2026-01-05',
      to_date: '2026-01-07',
      from_session: LEAVE_SESSION.AFTERNOON,
      to_session: LEAVE_SESSION.MORNING,
      total_days: 2,
      reason: 'Về quê',
      contact_phone: '0900000000',
      contact_address: 'Cà Mau',
      handovers: [],
    })
  })

  it('KHÔNG mang theo `status`, `code` hay `id` — form không được sửa mấy ô đó', () => {
    //  Qua `unknown` vì `LeaveFormValues` là `interface` nên không có chỉ mục
    //  ngầm — đọc khóa lạ trên nó là lỗi biên dịch, mà đó chính là thứ bài này
    //  muốn kiểm ở thời điểm CHẠY.
    const form = formValuesOf(request()) as unknown as Record<string, unknown>
    expect(form.status).toBeUndefined()
    expect(form.code).toBeUndefined()
    expect(form.id).toBeUndefined()
  })

  it('giữ nguyên số ngày người dùng đã sửa đè, kể cả nửa ngày', () => {
    expect(formValuesOf(request({ total_days: 1.5 })).total_days).toBe(1.5)
  })

  it('ô rỗng vẫn ra chuỗi rỗng, không ra `undefined` làm ô nhập mất kiểm soát', () => {
    const form = formValuesOf(request({ reason: '', contact_phone: '', contact_address: '' }))
    expect(form.reason).toBe('')
    expect(form.contact_phone).toBe('')
    expect(form.contact_address).toBe('')
  })
})

describe('bộ mã phải khớp backend', () => {
  it('mọi trạng thái đều có nhãn tiếng Việt', () => {
    for (const value of Object.values(LEAVE_STATUS)) {
      expect(LEAVE_STATUS_LABELS[value]).toBeTruthy()
    }
  })

  it('mọi buổi và mọi đơn vị đều có nhãn', () => {
    for (const value of Object.values(LEAVE_SESSION)) {
      expect(LEAVE_SESSION_LABELS[value]).toBeTruthy()
    }
    for (const value of Object.values(LEAVE_UNIT)) {
      expect(LEAVE_UNIT_LABELS[value]).toBeTruthy()
    }
  })

  it('chỉ Nháp và Trả về là sửa được — khớp `EDITABLE_STATUSES` của backend', () => {
    //  Nới thêm trạng thái vào đây là mở đường sửa một tờ đơn ĐANG chạy trong
    //  luồng duyệt: người duyệt đọc một đằng, dữ liệu lưu một nẻo. Backend chặn
    //  ở `check_editable`, nhưng người dùng sẽ gõ xong rồi mới ăn lỗi.
    expect(EDITABLE_LEAVE_STATUSES).toEqual([LEAVE_STATUS.DRAFT, LEAVE_STATUS.RETURNED])
  })

  it('giá trị trạng thái là số nguyên dương liền mạch 1..6 (R2/QĐ-11)', () => {
    expect(Object.values(LEAVE_STATUS).sort((a, b) => a - b)).toEqual([1, 2, 3, 4, 5, 6])
  })

  it('trần lý do nghỉ khớp `String(1000)` của cột `reason`', () => {
    expect(REASON_MAX).toBe(1000)
  })
})

/**
 * BÀN GIAO CÔNG VIỆC — bảng con `tab_leave_handover`.
 *
 * Backend nhận danh sách này từ đầu và bản chỉ xem đã hiện nó, nhưng form thì
 * chưa từng gửi lên: mọi đơn lập từ giao diện v2 đều có phần bàn giao RỖNG dù
 * người dùng có nhập hay không. Nhóm bài dưới chốt đường đi hai chiều.
 */
describe('handovers', () => {
  it('nạp danh sách bàn giao của tờ đơn vào form, kèm tên để hiện lại được', () => {
    const form = formValuesOf(
      request({
        handovers: [
          { id: 9, employee_id: 7, employee_name: 'Nhân viên (Demo)', content: 'Đơn hàng', sort_order: 0 },
        ],
      }),
    )
    expect(form.handovers).toEqual([
      { employee_id: 7, employee_name: 'Nhân viên (Demo)', content: 'Đơn hàng' },
    ])
  })

  it('đơn KHÔNG có khóa `handovers` thì cho mảng rỗng, không phải undefined', () => {
    //  `undefined` thì `value.handovers.map(...)` trong ô nhập nổ ngay lúc mở.
    expect(formValuesOf(request()).handovers).toEqual([])
  })

  it('dòng thiếu tên hoặc thiếu nội dung vẫn nạp được, chỉ là chuỗi rỗng', () => {
    const form = formValuesOf(
      request({
        handovers: [
          { id: 9, employee_id: 7, content: '', sort_order: 0 },
        ],
      }),
    )
    expect(form.handovers).toEqual([{ employee_id: 7, employee_name: '', content: '' }])
  })

  it('LUÔN gửi khóa `handovers` lên API, kể cả khi rỗng', () => {
    //  Backend coi VẮNG MẶT khóa này là "giữ nguyên danh sách cũ"
    //  (`has_handovers` trong `request_service.update`). Bỏ khóa khi rỗng thì
    //  người dùng xóa hết người bàn giao rồi bấm lưu sẽ thấy danh sách cũ hiện
    //  lại y nguyên.
    const payload = toLeavePayload({ ...emptyLeaveForm(), handovers: [] })
    expect(payload.handovers).toEqual([])
    expect('handovers' in payload).toBe(true)
  })

  it('loại dòng chưa chọn người, và KHÔNG đẩy `employee_name` lên server', () => {
    const payload = toLeavePayload({
      ...emptyLeaveForm(),
      handovers: [
        { employee_id: 0, employee_name: '', content: 'chưa chọn ai' },
        { employee_id: 7, employee_name: 'Nhân viên (Demo)', content: '  Đơn hàng  ' },
      ],
    })
    //  Tên chỉ để hiện trên màn — cột `tab_leave_handover` không có ô đó.
    expect(payload.handovers).toEqual([{ employee_id: 7, content: 'Đơn hàng' }])
  })

  it('người bàn giao KHÔNG ghi nội dung vẫn được gửi — cử người là đủ', () => {
    const payload = toLeavePayload({
      ...emptyLeaveForm(),
      handovers: [{ employee_id: 7, employee_name: 'A', content: '   ' }],
    })
    expect(payload.handovers).toEqual([{ employee_id: 7, content: '' }])
  })
})
