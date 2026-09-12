import { describe, expect, it } from 'vitest'

import { LEAVE_SESSION } from '../types/leave'
import { applyAssistantLeaveDraft, parseAssistantLeaveDraft } from './assistant-leave-draft'
import { emptyLeaveForm, REASON_MAX } from './leave-form-values'

/**
 * Đầu vào của `parseAssistantLeaveDraft` là kết quả tool do MODEL điền rồi đi qua
 * `location.state` — tức dữ liệu KHÔNG kiểm soát được kiểu. Bộ test này cố tình
 * đập vào đó chứ không đi đường hạnh phúc: sai kiểu, thiếu khóa, số âm, chuỗi dài.
 */

/** Bản nháp đủ khóa, đúng hình dạng backend trả về — gốc để từng test bẻ một chỗ. */
function draftOf(patch: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    kind: 'leave_request',
    lines: [{ leave_type_id: 7, leave_type: 'Phép năm', days: 3 }],
    from_date: '2026-09-01',
    to_date: '2026-09-03',
    from_session: LEAVE_SESSION.FULL,
    to_session: LEAVE_SESSION.FULL,
    from_time: '',
    to_time: '',
    reason: 'Về quê có việc gia đình',
    contact_phone: '0900000001',
    ...patch,
  }
}

describe('parseAssistantLeaveDraft', () => {
  it('reads a well-formed draft into form values', () => {
    expect(parseAssistantLeaveDraft(draftOf())).toEqual({
      leave_type_id: 7,
      days: 3,
      from_date: '2026-09-01',
      to_date: '2026-09-03',
      from_session: LEAVE_SESSION.FULL,
      to_session: LEAVE_SESSION.FULL,
      from_time: '',
      to_time: '',
      reason: 'Về quê có việc gia đình',
      contact_phone: '0900000001',
    })
  })

  it('rejects anything that is not a leave draft', () => {
    //  Cùng một ô `location.state.assistantDraft` còn chở bản nháp YCBG/YCMH —
    //  nhận nhầm là form nghỉ phép điền rác từ phiếu của phân hệ khác.
    expect(parseAssistantLeaveDraft(draftOf({ kind: 'survey_request' }))).toBeNull()
    expect(parseAssistantLeaveDraft({ ...draftOf(), kind: undefined })).toBeNull()
    expect(parseAssistantLeaveDraft(null)).toBeNull()
    expect(parseAssistantLeaveDraft(undefined)).toBeNull()
    expect(parseAssistantLeaveDraft('leave_request')).toBeNull()
    expect(parseAssistantLeaveDraft(42)).toBeNull()
    expect(parseAssistantLeaveDraft([draftOf()])).toBeNull()
  })

  it('rejects a draft missing any of the core fields', () => {
    expect(parseAssistantLeaveDraft(draftOf({ from_date: '' }))).toBeNull()
    expect(parseAssistantLeaveDraft(draftOf({ to_date: '01/09/2026' }))).toBeNull()
    expect(parseAssistantLeaveDraft(draftOf({ reason: '   ' }))).toBeNull()
    expect(parseAssistantLeaveDraft(draftOf({ lines: [] }))).toBeNull()
    expect(parseAssistantLeaveDraft(draftOf({ lines: 'Phép năm' }))).toBeNull()
    expect(parseAssistantLeaveDraft(draftOf({ lines: [null] }))).toBeNull()
    //  id loại nghỉ <= 0 là "không biết loại nào" — điền vào ô chọn thì nó câm.
    expect(parseAssistantLeaveDraft(draftOf({ lines: [{ leave_type_id: 0, days: 3 }] }))).toBeNull()
    expect(parseAssistantLeaveDraft(draftOf({ lines: [{ leave_type_id: -7, days: 3 }] }))).toBeNull()
    expect(
      parseAssistantLeaveDraft(draftOf({ lines: [{ leave_type_id: '7', days: 3 }] })),
    ).toBeNull()
  })

  it('drops malformed dates instead of feeding them to the date input', () => {
    //  Chuỗi khác `YYYY-MM-DD` vào ô ngày là ô đó hỏng IM LẶNG — thà trả null.
    //  `2026-09-011` và `...T00:00:00` canh riêng một lỗi: bản đầu cắt 10 ký tự
    //  RỒI mới kiểm regex, nên ngày gõ thừa số lọt qua thành một ngày khác.
    for (const bad of [
      '2026-9-1',
      '2026/09/01',
      'mai',
      '20260901',
      '2026-09-011',
      '2026-09-01T00:00:00',
      20260901,
    ]) {
      expect(parseAssistantLeaveDraft(draftOf({ from_date: bad }))).toBeNull()
    }
  })

  it('falls back to a full day for any session outside the code set', () => {
    for (const bad of [0, 5, -1, 1.5, 'morning', null, undefined, {}]) {
      const draft = parseAssistantLeaveDraft(draftOf({ from_session: bad, to_session: bad }))
      expect(draft?.from_session).toBe(LEAVE_SESSION.FULL)
      expect(draft?.to_session).toBe(LEAVE_SESSION.FULL)
    }
  })

  it('keeps times only for an hourly leave', () => {
    const theoGio = parseAssistantLeaveDraft(
      draftOf({
        from_session: LEAVE_SESSION.HOURLY,
        to_session: LEAVE_SESSION.HOURLY,
        from_time: '08:00',
        to_time: '10:30',
      }),
    )
    expect(theoGio?.from_time).toBe('08:00')
    expect(theoGio?.to_time).toBe('10:30')

    //  Buổi không phải «Theo giờ» mà vẫn kèm giờ thì form gửi lên hai ô thừa.
    const caNgay = parseAssistantLeaveDraft(draftOf({ from_time: '08:00', to_time: '10:30' }))
    expect(caNgay?.from_time).toBe('')
    expect(caNgay?.to_time).toBe('')

    //  Giờ sai dạng thì bỏ ô đó, đừng bỏ cả bản nháp — người dùng gõ lại được.
    const sai = parseAssistantLeaveDraft(
      draftOf({
        from_session: LEAVE_SESSION.HOURLY,
        to_session: LEAVE_SESSION.HOURLY,
        from_time: '8:00',
        to_time: 830,
      }),
    )
    expect(sai?.from_time).toBe('')
    expect(sai?.to_time).toBe('')
  })

  it('zeroes a non-positive or non-numeric day count', () => {
    //  `days = 0` nghĩa là CHƯA có con số: đơn một dòng thì backend tự tính lại.
    expect(parseAssistantLeaveDraft(draftOf({ lines: [{ leave_type_id: 7, days: 0 }] }))?.days).toBe(
      0,
    )
    expect(
      parseAssistantLeaveDraft(draftOf({ lines: [{ leave_type_id: 7, days: -3 }] }))?.days,
    ).toBe(0)
    expect(
      parseAssistantLeaveDraft(draftOf({ lines: [{ leave_type_id: 7, days: '3' }] }))?.days,
    ).toBe(0)
    expect(parseAssistantLeaveDraft(draftOf({ lines: [{ leave_type_id: 7 }] }))?.days).toBe(0)
  })

  it('clips over-long text to the field limits', () => {
    const draft = parseAssistantLeaveDraft(
      draftOf({ reason: 'x'.repeat(REASON_MAX + 500), contact_phone: '0'.repeat(80) }),
    )
    expect(draft?.reason).toHaveLength(REASON_MAX)
    expect(draft?.contact_phone).toHaveLength(30)
  })
})

describe('applyAssistantLeaveDraft', () => {
  it('overwrites only the fields the draft speaks about', () => {
    const base = emptyLeaveForm()
    const draft = parseAssistantLeaveDraft(draftOf())
    expect(draft).not.toBeNull()
    const form = applyAssistantLeaveDraft(base, draft!)

    expect(form.from_date).toBe('2026-09-01')
    expect(form.to_date).toBe('2026-09-03')
    expect(form.reason).toBe('Về quê có việc gia đình')
    expect(form.contact_phone).toBe('0900000001')
    expect(form.lines).toEqual([{ leave_type_id: 7, days: 3 }])
    //  Ô bản nháp KHÔNG nói tới phải giữ nguyên của form rỗng — nhất là
    //  `employee_id = 0` (người nghỉ là chính người lập đơn): trợ lý không được
    //  đặt người khác vào ô đó.
    expect(form.employee_id).toBe(base.employee_id)
    expect(form.employee_name).toBe(base.employee_name)
    expect(form.handovers).toEqual(base.handovers)
    expect(form.contact_address).toBe(base.contact_address)
  })

  it('keeps the form phone when the draft has none', () => {
    const base = { ...emptyLeaveForm(), contact_phone: '0911111111' }
    const draft = parseAssistantLeaveDraft(draftOf({ contact_phone: '' }))
    expect(applyAssistantLeaveDraft(base, draft!).contact_phone).toBe('0911111111')
  })

  it('does not mutate the form it was given', () => {
    const base = emptyLeaveForm()
    const snapshot = structuredClone(base)
    applyAssistantLeaveDraft(base, parseAssistantLeaveDraft(draftOf())!)
    expect(base).toEqual(snapshot)
  })
})
