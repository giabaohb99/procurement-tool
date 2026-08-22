import { describe, expect, it } from 'vitest'

import { CHANGE_KIND, type DocumentVersion } from '../types/document-record'
import { soBanKeTiep } from './next-version-no'

function ban(major: number, minor: number): DocumentVersion {
  return { major, minor } as DocumentVersion
}

describe('soBanKeTiep', () => {
  it('sửa lớn thì lên đầu số kế tiếp và trả phần lẻ về 0', () => {
    expect(soBanKeTiep(ban(1, 0), CHANGE_KIND.major)).toBe('2.0')
    expect(soBanKeTiep(ban(2, 3), CHANGE_KIND.major)).toBe('3.0')
  })

  it('sửa nhỏ thì giữ đầu số, cộng phần lẻ', () => {
    expect(soBanKeTiep(ban(1, 0), CHANGE_KIND.minor)).toBe('1.1')
    expect(soBanKeTiep(ban(2, 3), CHANGE_KIND.minor)).toBe('2.4')
  })

  //  Lỗi thật: hộp thoại ghi cứng "lên bản 2.0 / 1.1", nên văn bản đã ở 2.1 vẫn
  //  mời người dùng "lên bản 1.1" — chọn xong ra 2.2, khác hẳn thứ vừa đọc.
  it('không còn nói bản 1.1 khi văn bản đã đi qua bản 1', () => {
    expect(soBanKeTiep(ban(2, 1), CHANGE_KIND.minor)).not.toBe('1.1')
  })

  it('chưa có bản đang dùng thì không bịa ra số', () => {
    expect(soBanKeTiep(undefined, CHANGE_KIND.major)).toBeNull()
  })
})
