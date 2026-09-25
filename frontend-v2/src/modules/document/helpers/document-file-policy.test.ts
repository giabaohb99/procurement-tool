import { describe, expect, it } from 'vitest'

import {
  DOCUMENT_FILE_ACCEPT,
  DOCUMENT_FILE_EXTENSIONS,
  describeDocumentFilePolicy,
} from './document-file-policy'

describe('document file policy', () => {
  //  Chép tay từ `_DOC` của backend (`core/file_registry.py`). Đổi bên đó thì
  //  sửa cả bộ này — bài này đỏ lên là để nhắc đúng việc đó.
  it('mirrors the backend whitelist for document_version exactly', () => {
    expect([...DOCUMENT_FILE_EXTENSIONS].sort()).toEqual([
      'cdr',
      'csv',
      'doc',
      'docx',
      'eml',
      'jpeg',
      'jpg',
      'msg',
      'pdf',
      'png',
      'txt',
      'webp',
      'xls',
      'xlsx',
      'xml',
    ])
  })

  it('builds an accept attribute with a leading dot per extension and no blanks', () => {
    const parts = DOCUMENT_FILE_ACCEPT.split(',')
    expect(parts).toHaveLength(DOCUMENT_FILE_EXTENSIONS.length)
    expect(parts.every((part) => /^\.[a-z]+$/.test(part))).toBe(true)
  })

  it('tells the user every format and the size cap in one line', () => {
    const text = describeDocumentFilePolicy()
    expect(text).toContain('PDF, DOC, DOCX')
    expect(text).toContain('CDR')
    expect(text).toContain('tối đa 50 MB mỗi tệp')
  })
})
