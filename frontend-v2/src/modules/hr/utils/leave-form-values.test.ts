import { describe, expect, it } from 'vitest'

import {
  emptyLeaveForm,
  formValuesOf,
  REASON_MAX,
  toLeavePayload,
  totalLeaveDays,
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

  it('chừa sẵn MỘT dòng loại nghỉ trống, không để bảng rỗng', () => {
    //  Gần như mọi tờ đơn chỉ có một loại nghỉ, nên bắt người dùng bấm «Thêm
    //  loại nghỉ» trước khi gõ được gì là thừa một nhịp. `days = 0` là dấu hiệu
    //  «chưa sửa đè, backend cứ tự tính».
    expect(emptyLeaveForm().lines).toEqual([{ leave_type_id: 0, days: 0 }])
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
  it('bê nguyên các ô của tờ đơn, không tự nắn giá trị nào', () => {
    const form = formValuesOf(request())
    expect(form).toEqual({
      employee_id: 3,
      employee_name: '',
      lines: [{ leave_type_id: 4, days: 2 }],
      from_date: '2026-01-05',
      to_date: '2026-01-07',
      from_session: LEAVE_SESSION.AFTERNOON,
      to_session: LEAVE_SESSION.MORNING,
      from_time: '',
      to_time: '',
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
    expect(formValuesOf(request({ total_days: 1.5 })).lines).toEqual([
      { leave_type_id: 4, days: 1.5 },
    ])
  })

  it('ô rỗng vẫn ra chuỗi rỗng, không ra `undefined` làm ô nhập mất kiểm soát', () => {
    const form = formValuesOf(request({ reason: '', contact_phone: '', contact_address: '' }))
    expect(form.reason).toBe('')
    expect(form.contact_phone).toBe('')
    expect(form.contact_address).toBe('')
  })
})

/**
 * NHIỀU LOẠI NGHỈ TRONG MỘT ĐƠN (07/09/2026).
 *
 * `leave_type_id` và `total_days` là hai cột DẪN XUẤT do backend đặt, nên form
 * không giữ chúng nữa. Nhóm bài dưới chốt đường đi hai chiều của bản kê.
 */
describe('lines — bản kê loại nghỉ', () => {
  it('nạp đủ các dòng của tờ đơn theo đúng thứ tự', () => {
    const form = formValuesOf(
      request({
        total_days: 4,
        lines: [
          { id: 1, leave_type_id: 4, leave_type_name: 'Phép năm', days: 3, sort_order: 0 },
          { id: 2, leave_type_id: 5, leave_type_name: 'Không lương', days: 1, sort_order: 1 },
        ],
      }),
    )
    expect(form.lines).toEqual([
      { leave_type_id: 4, days: 3 },
      { leave_type_id: 5, days: 1 },
    ])
  })

  it('đơn CŨ chưa có bản kê thì dựng lại một dòng từ hai cột đầu đơn', () => {
    //  Không có nhánh này thì mở một tờ đơn lập trước đợt nhiều loại ra sửa sẽ
    //  thấy bảng loại nghỉ TRỐNG, và lưu lại là mất loại nghỉ đã chọn.
    expect(formValuesOf(request({ lines: [] })).lines).toEqual([
      { leave_type_id: 4, days: 2 },
    ])
    expect(formValuesOf(request({ lines: undefined })).lines).toEqual([
      { leave_type_id: 4, days: 2 },
    ])
  })

  it('loại dòng CHƯA CHỌN loại nghỉ khi dựng thân yêu cầu', () => {
    //  Bảng luôn chừa sẵn một dòng trống để gõ; đẩy nó lên là ăn câu chặn
    //  «Chưa chọn loại nghỉ» cho một dòng người dùng còn chưa động tới.
    const payload = toLeavePayload({
      ...emptyLeaveForm(),
      lines: [
        { leave_type_id: 4, days: 3 },
        { leave_type_id: 0, days: 0 },
      ],
    })
    expect(payload.lines).toEqual([{ leave_type_id: 4, days: 3 }])
  })

  it('KHÔNG gửi `leave_type_id` lẫn `total_days` — backend tự tính hai ô đó', () => {
    const payload = toLeavePayload(emptyLeaveForm()) as unknown as Record<string, unknown>
    expect('leave_type_id' in payload).toBe(false)
    expect('total_days' in payload).toBe(false)
  })

  it('bảng rỗng hoàn toàn vẫn gửi được `lines` rỗng, không nổ', () => {
    //  Backend sẽ chặn với câu «Chưa chọn loại nghỉ» — đó là chỗ nói câu đó,
    //  không phải ở đây bằng một ngoại lệ JavaScript.
    expect(toLeavePayload({ ...emptyLeaveForm(), lines: [] }).lines).toEqual([])
  })
})

describe('totalLeaveDays', () => {
  it('cộng các dòng lại, KHÔNG để đuôi số thực rò ra màn hình', () => {
    //  0.13 + 0.5 trong JavaScript ra 0.6300000000000001, và ô «Tổng cộng» hiện
    //  nguyên cái đuôi đó.
    expect(totalLeaveDays([
      { leave_type_id: 1, days: 0.13 },
      { leave_type_id: 2, days: 0.5 },
    ])).toBe(0.63)
  })

  it('danh sách rỗng ra 0, không ra NaN', () => {
    expect(totalLeaveDays([])).toBe(0)
  })

  it('dòng chưa nhập số ngày tính là 0', () => {
    expect(totalLeaveDays([{ leave_type_id: 1, days: 0 }])).toBe(0)
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
