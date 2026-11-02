import { describe, expect, it } from 'vitest'

import type { AuditLogEntry } from './audit-api'
import { collapseSameRequest, describeAuditEntry } from './describe-audit-entry'

const LABELS = { department_id: 'Phòng ban', company_id: 'Công ty', work_location: 'Nơi làm việc' }

function entry(overrides: Partial<AuditLogEntry>): AuditLogEntry {
  return {
    id: 1,
    action: 'update',
    action_label: 'Cập nhật',
    entity_id: 304,
    by: 'Dego Admin',
    at: '2026-10-29T04:09:32',
    request_id: '',
    changed_fields: '',
    ...overrides,
  }
}

describe('describeAuditEntry', () => {
  it('describes creation with the given noun', () => {
    expect(describeAuditEntry(entry({ action: 'create' }), LABELS, 'hồ sơ này')).toEqual({
      verb: 'đã tạo hồ sơ này',
      fields: [],
    })
  })

  it('translates changed columns, drops unknown technical ones and duplicates', () => {
    const result = describeAuditEntry(
      entry({ changed_fields: 'department_id, updated_at,company_id,department_id' }),
      LABELS,
    )
    expect(result).toEqual({ verb: 'đã cập nhật', fields: ['Phòng ban', 'Công ty'] })
  })

  it('falls back to «đã chỉnh sửa» when no change is known or every column is technical', () => {
    expect(describeAuditEntry(entry({ changed_fields: '' }), LABELS).verb).toBe('đã chỉnh sửa')
    expect(describeAuditEntry(entry({ changed_fields: undefined }), LABELS).verb).toBe(
      'đã chỉnh sửa',
    )
    expect(describeAuditEntry(entry({ changed_fields: 'updated_at' }), LABELS).verb).toBe(
      'đã chỉnh sửa',
    )
  })

  it('keeps the backend label for other actions', () => {
    expect(
      describeAuditEntry(entry({ action: 'lock', action_label: 'Khóa tài khoản' }), LABELS),
    ).toEqual({ verb: '— Khóa tài khoản', fields: [] })
  })
})

describe('collapseSameRequest', () => {
  it('merges rows from the same save into the newest one and unions their fields', () => {
    //  Ảnh 02/11/2026: một lần Lưu ra ba dòng «Cập nhật · 29/10 11:09» giống hệt nhau.
    const rows = [
      entry({ id: 3, request_id: 'r1', changed_fields: 'department_id' }),
      entry({ id: 2, request_id: 'r1', changed_fields: 'department_id, company_id' }),
      entry({ id: 1, request_id: 'r1', changed_fields: '' }),
    ]
    expect(collapseSameRequest(rows)).toEqual([
      entry({ id: 3, request_id: 'r1', changed_fields: 'department_id, company_id' }),
    ])
  })

  it('never merges rows without a request id (written before request logging existed)', () => {
    const rows = [entry({ id: 2 }), entry({ id: 1 })]
    expect(collapseSameRequest(rows)).toHaveLength(2)
  })

  it('keeps different people or actions in the same request apart', () => {
    const rows = [
      entry({ id: 3, request_id: 'r1' }),
      entry({ id: 2, request_id: 'r1', by: 'Người khác' }),
      entry({ id: 1, request_id: 'r1', action: 'create' }),
    ]
    expect(collapseSameRequest(rows).map((r) => r.id)).toEqual([3, 2, 1])
  })

  it('returns an empty list unchanged', () => {
    expect(collapseSameRequest([])).toEqual([])
  })
})
