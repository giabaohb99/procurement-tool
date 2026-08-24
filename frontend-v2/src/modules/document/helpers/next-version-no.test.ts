import { describe, expect, it } from 'vitest'

import { CHANGE_KIND, VERSION_STATUS, type DocumentVersion } from '../types/document-record'
import { soBanKeTiep } from './next-version-no'

function ban(major: number, minor: number, status: number = VERSION_STATUS.approved): DocumentVersion {
  return { major, minor, status } as DocumentVersion
}

describe('soBanKeTiep', () => {
  it('sửa lớn thì lên đầu số kế tiếp và trả phần lẻ về 0', () => {
    expect(soBanKeTiep([ban(1, 0)], CHANGE_KIND.major)).toBe('2.0')
    expect(soBanKeTiep([ban(2, 3)], CHANGE_KIND.major)).toBe('3.0')
  })

  it('sửa nhỏ thì giữ đầu số, cộng phần lẻ', () => {
    expect(soBanKeTiep([ban(1, 0)], CHANGE_KIND.minor)).toBe('1.1')
    expect(soBanKeTiep([ban(2, 3)], CHANGE_KIND.minor)).toBe('2.4')
  })

  //  Lỗi thật: hộp thoại ghi cứng "lên bản 2.0 / 1.1", nên văn bản đã ở 2.1 vẫn
  //  mời người dùng "lên bản 1.1" — chọn xong ra 2.2, khác hẳn thứ vừa đọc.
  it('không còn nói bản 1.1 khi văn bản đã đi qua bản 1', () => {
    expect(soBanKeTiep([ban(2, 1)], CHANGE_KIND.minor)).not.toBe('1.1')
  })

  it('đếm từ số CAO NHẤT, không phải bản cuối danh sách', () => {
    expect(soBanKeTiep([ban(2, 0), ban(1, 0), ban(1, 1)], CHANGE_KIND.major)).toBe('3.0')
    //  10.0 phải lớn hơn 2.0 — đúng lý do `major`/`minor` là hai số nguyên chứ
    //  không phải chuỗi "2.0".
    expect(soBanKeTiep([ban(2, 0), ban(10, 0)], CHANGE_KIND.minor)).toBe('10.1')
  })

  //  Lỗi thật (24/08/2026): bản 2.0 bị TỪ CHỐI nằm lại trong bảng, bản đang dùng
  //  vẫn là 1.0. Helper cũ đếm từ bản đang dùng nên mời "lên bản 2.0", còn backend
  //  đếm từ số cao nhất và sinh 3.0 — người dùng bấm theo lời mời rồi nhận số khác.
  it('số của bản bị từ chối vẫn CHÁY, không mời dùng lại', () => {
    const versions = [ban(1, 0), ban(2, 0, VERSION_STATUS.rejected)]
    expect(soBanKeTiep(versions, CHANGE_KIND.major)).toBe('3.0')
  })

  it('chưa có phiên bản nào thì không bịa ra số', () => {
    expect(soBanKeTiep([], CHANGE_KIND.major)).toBeNull()
  })
})
