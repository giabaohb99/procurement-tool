import { describe, expect, it } from 'vitest'

import type { MyDecision } from '@/modules/approval/types/approval'
import type { LegacyDecision, LegacyPendingDocument } from '../types/legacy-pending-approval'
import { buildInboxRows, describeInboxEmpty, INBOX_SCOPE } from './approval-inbox-row'

const legacy: LegacyPendingDocument = {
  document_id: 17,
  code: '',
  title: 'Công văn tạo nhanh',
  version_label: '1.0',
  submitted_by_name: 'Dego Admin',
  submitted_at: '2026-09-25T02:22:55',
}

//  Lỗi bắt khi test UI 25/09/2026: văn bản duyệt MỘT BƯỚC không có việc trong
//  bộ máy duyệt nên không bao giờ hiện ở «Chờ tôi duyệt».
describe('buildInboxRows — single-step documents', () => {
  it('lists a single-step document as a pending row that opens the document', () => {
    const [row] = buildInboxRows([], [], [legacy])
    expect(row).toMatchObject({
      kind: 'pending',
      entityId: 17,
      title: 'Công văn tạo nhanh',
      nodeName: 'Duyệt một bước',
      startedByName: 'Dego Admin',
      isOverdue: false,
      dueAt: null,
    })
  })

  it('keeps ids unique when a document id equals a task id', () => {
    const rows = buildInboxRows([], [], [legacy, { ...legacy, document_id: 18 }])
    expect(new Set(rows.map((row) => row.id)).size).toBe(2)
    expect(rows.map((row) => row.id)).toEqual(['legacy-17', 'legacy-18'])
  })

  it('still works for callers that pass only the two old sources', () => {
    expect(buildInboxRows([], [])).toEqual([])
  })
})

//  Duyệt một bước xong thì văn bản biến khỏi màn — nhóm «Đã duyệt» phải có nó.
describe('buildInboxRows — single-step decisions', () => {
  const approved: LegacyDecision = {
    id: 4048,
    document_id: 17,
    code: '01/2026/CV-DEGO',
    title: 'Công văn tạo nhanh',
    action: 2,
    action_label: 'Duyệt',
    comment: '',
    decided_at: '2026-09-25T02:45:56',
    status_label: 'Có hiệu lực',
  }
  const engineDecision = {
    id: 9,
    entity_id: 18,
    entity_code: '02/2026/TB-DEGO',
    entity_title: 'Thông báo nghỉ lễ',
    node_seq: 1,
    node_name: 'Trưởng phòng duyệt',
    action: 2,
    action_label: 'Duyệt',
    comment: '',
    decided_at: '2026-09-25T03:00:00',
    instance_status_label: 'Hoàn tất',
    on_behalf_of_name: '',
  } as MyDecision

  it('lists my single-step approval as a done row with the current document status', () => {
    const [row] = buildInboxRows([], [], [], [approved])
    expect(row).toMatchObject({
      id: 'legacy-done-4048',
      kind: 'done',
      entityId: 17,
      nodeName: 'Duyệt một bước',
      action: 2,
      actionLabel: 'Duyệt',
      instanceStatusLabel: 'Có hiệu lực',
    })
  })

  it('interleaves both kinds of decisions by time, newest first, below every pending row', () => {
    const older = { ...approved, id: 1, decided_at: '2026-09-01T00:00:00' }
    const rows = buildInboxRows([], [engineDecision], [legacy], [older, approved])
    expect(rows.map((row) => row.id)).toEqual([
      'legacy-17',
      'done-9',
      'legacy-done-4048',
      'legacy-done-1',
    ])
  })

  it('keeps the return reason so the reader sees why it was sent back', () => {
    const [row] = buildInboxRows(
      [],
      [],
      [],
      [{ ...approved, action: 4, action_label: 'Trả lại', comment: 'Thiếu chữ ký phụ lục' }],
    )
    expect(row).toMatchObject({ actionLabel: 'Trả lại', comment: 'Thiếu chữ ký phụ lục' })
  })
})

//  25/09/2026: tab mặc định đổi sang «Cần duyệt». Tab đó trống (hết việc) mà
//  màn báo «không khớp điều kiện đang lọc» là nói sai — người dùng chưa lọc gì.
describe('describeInboxEmpty', () => {
  it('says there is nothing waiting when the default tab is empty and nothing is filtered', () => {
    expect(describeInboxEmpty(INBOX_SCOPE.pending, false)).toBe(
      'Không có văn bản nào đang chờ bạn duyệt.',
    )
  })

  it('speaks about the tab the user is on', () => {
    expect(describeInboxEmpty(INBOX_SCOPE.overdue, false)).toContain('quá hạn')
    expect(describeInboxEmpty(INBOX_SCOPE.done, false)).toContain('chưa duyệt')
  })

  it('blames the filter only when a keyword or a condition is really active', () => {
    for (const scope of Object.values(INBOX_SCOPE)) {
      expect(describeInboxEmpty(scope, true)).toBe('Không có văn bản nào khớp điều kiện đang lọc.')
    }
  })
})
