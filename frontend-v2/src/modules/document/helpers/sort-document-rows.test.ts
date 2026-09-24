import { describe, expect, it } from 'vitest'

import { DOCUMENT_STATUS, type DocumentRecord } from '../types/document-record'
import { DOCUMENT_SORT_FIELD, sortDocumentRows } from './sort-document-rows'

function doc(overrides: Partial<DocumentRecord> & { id: number }): DocumentRecord {
  return {
    origin: 1, doc_code: null, issue_number: '', display_code: '', seq_no: null, issue_year: null,
    allow_manual_number: false, legacy_code: '', storage_location: '', metadata: null, doc_type_id: 1,
    doc_type_name: 'Loại A', doc_type_code: '', company_id: 1, company_name: '', department_id: null,
    department_name: '', owner_employee_id: 0, owner_name: '', drafter_employee_id: null, drafter_name: '',
    signer_employee_id: null, signer_name: '', title: 'X', summary: '', keywords: '', secrecy_level: 1,
    urgency: 1, status: DOCUMENT_STATUS.draft, status_label: '', effective_date: null, expire_date: null,
    attachment_view_until: null, attachment_view_window_enabled: false, has_content: false, book_id: null,
    book_name: '', book_seq_no: null, book_year: null, book_number_display: '', current_version_id: null,
    version_no: '1.0', version_count: 1, attachment_count: 0, needs_review: false, needs_review_note: '',
    apply_mode: 1, created_at: '2026-01-01T00:00:00',
    content_mode: 1,
    ...overrides,
  }
}

describe('sortDocumentRows', () => {
  const rows = [
    doc({ id: 1, title: 'Bò', doc_type_name: 'Z', created_at: '2026-03-01' }),
    doc({ id: 2, title: 'Áo', doc_type_name: 'A', created_at: '2026-01-01' }),
    doc({ id: 3, title: 'Cá', doc_type_name: 'M', created_at: '2026-02-01' }),
  ]

  it('sắp theo TÊN tăng dần, đúng thứ tự chữ Việt (Á trước B trước C)', () => {
    const sorted = sortDocumentRows(rows, DOCUMENT_SORT_FIELD.name, 'asc')
    expect(sorted.map((r) => r.id)).toEqual([2, 1, 3])
  })

  it('sắp theo TÊN giảm dần — đảo ngược', () => {
    const sorted = sortDocumentRows(rows, DOCUMENT_SORT_FIELD.name, 'desc')
    expect(sorted.map((r) => r.id)).toEqual([3, 1, 2])
  })

  it('sắp theo NGÀY TẠO tăng dần', () => {
    const sorted = sortDocumentRows(rows, DOCUMENT_SORT_FIELD.createdAt, 'asc')
    expect(sorted.map((r) => r.id)).toEqual([2, 3, 1])
  })

  it('sắp theo LOẠI tăng dần', () => {
    const sorted = sortDocumentRows(rows, DOCUMENT_SORT_FIELD.type, 'asc')
    expect(sorted.map((r) => r.id)).toEqual([2, 3, 1])
  })

  it('KHÔNG sửa mảng đầu vào (thuần, không side-effect)', () => {
    const input = [...rows]
    sortDocumentRows(input, DOCUMENT_SORT_FIELD.name, 'asc')
    expect(input.map((r) => r.id)).toEqual([1, 2, 3])
  })

  it('mảng RỖNG — không nổ, trả rỗng', () => {
    expect(sortDocumentRows([], DOCUMENT_SORT_FIELD.name, 'asc')).toEqual([])
  })

  it('mảng MỘT phần tử — trả nguyên', () => {
    const one = [doc({ id: 9 })]
    expect(sortDocumentRows(one, DOCUMENT_SORT_FIELD.name, 'asc').map((r) => r.id)).toEqual([9])
  })
})
