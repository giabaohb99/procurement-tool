import { describe, expect, it } from 'vitest'

import { SCOPE_MODE } from '../types/document-scope'
import { onlyExcludeRows } from './scope-only-exclude'

const INCLUDES = SCOPE_MODE.include
const EXCLUDE = SCOPE_MODE.exclude

describe('chiToanDongLoaiTru', () => {
  it('chưa khai dòng nào thì không cảnh báo — đó là mặc định áp cho cả pháp nhân', () => {
    expect(onlyExcludeRows([])).toBe(false)
  })

  it('một dòng loại trừ đứng một mình là văn bản không tới ai', () => {
    expect(onlyExcludeRows([EXCLUDE])).toBe(true)
  })

  it('nhiều dòng nhưng toàn loại trừ vẫn là không tới ai', () => {
    expect(onlyExcludeRows([EXCLUDE, EXCLUDE, EXCLUDE])).toBe(true)
  })

  it('có ít nhất một dòng bao gồm thì thôi cảnh báo', () => {
    expect(onlyExcludeRows([INCLUDES, EXCLUDE])).toBe(false)
  })

  it('toàn dòng bao gồm thì đương nhiên không cảnh báo', () => {
    expect(onlyExcludeRows([INCLUDES])).toBe(false)
  })
})
