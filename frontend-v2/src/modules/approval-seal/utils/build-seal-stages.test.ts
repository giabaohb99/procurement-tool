import { describe, expect, it } from 'vitest'

import { SEAL_STATUS, type SealRequest } from '../types/seal-request'
import { buildSealStages } from './build-seal-stages'

/** Phiếu tối thiểu — mỗi bài kiểm ghi đè đúng ô nó quan tâm. */
function makeRequest(patch: Partial<SealRequest> = {}): SealRequest {
  return {
    id: 1,
    code: 'DD014',
    status: SEAL_STATUS.draft,
    status_label: 'Nháp',
    purpose: 'Đóng dấu công văn',
    company_ids: [],
    companies: [],
    department_id: 0,
    first_approver_id: 7,
    approver_name: 'Trần Trưởng Phòng',
    approved_at: '',
    completed_by_name: '',
    completed_at: '',
    requester: 'Phạm Khánh Ngân',
    requester_id: 9,
    requester_email: '',
    requester_phone: '',
    requester_role: '',
    note: '',
    created_at: '2026-09-17T11:42:00',
    approval_running: false,
    ...patch,
  }
}

describe('buildSealStages', () => {
  it('opens with the person who CREATED the ticket — the link the old four-row card forgot', () => {
    const [first] = buildSealStages(makeRequest())

    expect(first.title).toBe('Lập phiếu (nháp)')
    expect(first.actor).toBe('Phạm Khánh Ngân')
    expect(first.state).toBe('done')
    expect(first.time).toContain('17/09/2026')
  })

  it('draft ticket: three stages, the last two still waiting', () => {
    const stages = buildSealStages(makeRequest())

    expect(stages.map((s) => s.key)).toEqual(['created', 'approve', 'stamp'])
    expect(stages[1]).toMatchObject({ title: 'Chờ Trưởng bộ phận duyệt', state: 'pending' })
    expect(stages[2]).toMatchObject({ title: 'Chờ Văn thư đóng dấu', state: 'pending' })
  })

  it('hides the future approver while EDITING — the real value lives in the form select', () => {
    expect(buildSealStages(makeRequest(), { editing: true })[1].actor).toBe('')
    //  …nhưng chỉ giấu khi CHƯA duyệt: đã duyệt rồi thì đó là dấu vết, không phải dự định.
    const approved = makeRequest({ status: SEAL_STATUS.approved, approved_at: '2026-09-18T09:00:00' })
    expect(buildSealStages(approved, { editing: true })[1].actor).toBe('Trần Trưởng Phòng')
  })

  it('counts a multi-step approval as APPROVED even without the single-step timestamp', () => {
    //  Lỗi cũ của bản đặt xe: lấy `approved_at` làm điều kiện nên phiếu duyệt xong
    //  vẫn hiện "Chờ duyệt" vì bộ máy nhiều bước không ghi mốc đó.
    const stages = buildSealStages(makeRequest({ status: SEAL_STATUS.approved, approved_at: '' }))

    expect(stages[1]).toMatchObject({ title: 'Trưởng bộ phận đã duyệt', state: 'done' })
  })

  it('completed: all three stages done, clerk named', () => {
    const stages = buildSealStages(
      makeRequest({
        status: SEAL_STATUS.completed,
        approved_at: '2026-09-18T09:00:00',
        completed_by_name: 'Lê Văn Thư',
        completed_at: '2026-09-18T15:30:00',
      }),
    )

    expect(stages.every((s) => s.state === 'done')).toBe(true)
    expect(stages[2]).toMatchObject({ title: 'Văn thư đã đóng dấu', actor: 'Lê Văn Thư' })
  })

  it.each([
    [SEAL_STATUS.rejected, 'Bị từ chối'],
    [SEAL_STATUS.returned, 'Trả về yêu cầu chỉnh sửa'],
  ])('a dead end (%i) CUTS the stamping stage — no promising work that will never happen', (status, title) => {
    const stages = buildSealStages(makeRequest({ status, approved_at: '2026-09-18T09:00:00' }))

    expect(stages).toHaveLength(2)
    expect(stages[1]).toMatchObject({ title, state: 'stopped' })
    expect(stages.some((s) => s.key === 'stamp')).toBe(false)
  })

  it('cancelled: drops stages that will never come, keeps the trail already there', () => {
    const stages = buildSealStages(
      makeRequest({ status: SEAL_STATUS.cancelled, approved_at: '2026-09-18T09:00:00' }),
    )

    expect(stages.map((s) => s.key)).toEqual(['created', 'approve', 'cancel'])
    expect(stages.at(-1)).toMatchObject({ title: 'Đã hủy phiếu', state: 'stopped' })
    expect(stages.some((s) => s.state === 'pending')).toBe(false)
  })

  it('still builds every stage on a ticket with no timestamps and no names', () => {
    const stages = buildSealStages(
      makeRequest({ created_at: null, requester: '', approver_name: '', completed_by_name: '' }),
    )

    expect(stages).toHaveLength(3)
    expect(stages[0]).toMatchObject({ actor: '', time: '' })
  })

  it('carries the stop reason onto the blocked stage only', () => {
    const stages = buildSealStages(
      makeRequest({ status: SEAL_STATUS.rejected, approved_at: '2026-09-18T09:00:00' }),
      { stopReason: 'Chưa đính kèm thư mời chính thức' },
    )

    expect(stages[1].reason).toBe('Chưa đính kèm thư mời chính thức')
    //  Chặng đã xong không được mang lý do — nó kể chuyện đã làm, không kể chuyện bị chặn.
    expect(stages[0].reason).toBe('')
  })

  it('leaves the reason empty on a healthy ticket even if one is passed in', () => {
    //  Nhật ký có thể còn lý do của lần trả về TRƯỚC; phiếu đã gửi lại rồi thì
    //  không chặng nào đang bị chặn, bày lý do cũ ra là nói sai tình trạng.
    const stages = buildSealStages(makeRequest({ status: SEAL_STATUS.pending }), {
      stopReason: 'Lý do của lần trả về trước',
    })

    expect(stages.every((stage) => stage.reason === '')).toBe(true)
  })
})
