import { describe, expect, it } from 'vitest'

import { SCOPE_MODE } from '../types/document-scope'
import { chiToanDongLoaiTru } from './scope-only-exclude'

const BAO_GOM = SCOPE_MODE.include
const LOAI_TRU = SCOPE_MODE.exclude

describe('chiToanDongLoaiTru', () => {
  it('chưa khai dòng nào thì không cảnh báo — đó là mặc định áp cho cả pháp nhân', () => {
    expect(chiToanDongLoaiTru([])).toBe(false)
  })

  it('một dòng loại trừ đứng một mình là văn bản không tới ai', () => {
    expect(chiToanDongLoaiTru([LOAI_TRU])).toBe(true)
  })

  it('nhiều dòng nhưng toàn loại trừ vẫn là không tới ai', () => {
    expect(chiToanDongLoaiTru([LOAI_TRU, LOAI_TRU, LOAI_TRU])).toBe(true)
  })

  it('có ít nhất một dòng bao gồm thì thôi cảnh báo', () => {
    expect(chiToanDongLoaiTru([BAO_GOM, LOAI_TRU])).toBe(false)
  })

  it('toàn dòng bao gồm thì đương nhiên không cảnh báo', () => {
    expect(chiToanDongLoaiTru([BAO_GOM])).toBe(false)
  })
})
