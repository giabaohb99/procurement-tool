import { describe, expect, it } from 'vitest'

import { validateAttachment } from './attachment-rules'

/** Dựng File giả đúng kích thước mà không cấp phát thật từng byte. */
function fakeFile(name: string, type: string, size: number): File {
  const f = new File([''], name, { type })
  Object.defineProperty(f, 'size', { value: size })
  return f
}

const MB = 1024 * 1024

describe('validateAttachment', () => {
  it('nhận ảnh JPG/PNG/WebP trong trần 5MB', () => {
    expect(validateAttachment(fakeFile('a.jpg', 'image/jpeg', 5 * MB))).toBeNull()
    expect(validateAttachment(fakeFile('a.png', 'image/png', 1 * MB))).toBeNull()
    expect(validateAttachment(fakeFile('a.webp', 'image/webp', 100))).toBeNull()
  })

  it('nhận PDF trong trần 10MB nhưng chặn PDF quá trần', () => {
    expect(validateAttachment(fakeFile('hd.pdf', 'application/pdf', 10 * MB))).toBeNull()
    expect(validateAttachment(fakeFile('hd.pdf', 'application/pdf', 10 * MB + 1)))
      .toContain('PDF tối đa 10MB')
  })

  it('chặn ảnh quá 5MB — trần ảnh KHÔNG ăn theo trần PDF', () => {
    expect(validateAttachment(fakeFile('to.png', 'image/png', 6 * MB)))
      .toContain('Ảnh tối đa 5MB')
  })

  it('chặn loại tệp ngoài danh sách (Excel/Word/exe...)', () => {
    const xlsx = fakeFile(
      'bang.xlsx',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      100,
    )
    expect(validateAttachment(xlsx)).toContain('Chỉ nhận ảnh JPG/PNG/WebP hoặc PDF')
    expect(validateAttachment(fakeFile('x.gif', 'image/gif', 100))).not.toBeNull()
  })
})
