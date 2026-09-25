import { describe, expect, it } from 'vitest'

import { groupFilesByVersion, type GroupableFile } from './group-files-by-version'

interface F extends GroupableFile {
  id: number
  filename: string
}

function file(overrides: Partial<F> & Pick<F, 'id' | 'filename' | 'version_id'>): F {
  return {
    version_no: '1.0',
    is_current_version: true,
    ...overrides,
  }
}

describe('groupFilesByVersion — cây phẳng khi chỉ một phiên bản', () => {
  it('0 tệp → phẳng, mảng rỗng', () => {
    const result = groupFilesByVersion([])
    expect(result.flat).toBe(true)
    if (result.flat) expect(result.files).toEqual([])
  })

  it('nhiều tệp CÙNG một phiên bản → phẳng, không bọc nút cha thừa', () => {
    const files = [
      file({ id: 1, filename: 'a.pdf', version_id: 10 }),
      file({ id: 2, filename: 'b.pdf', version_id: 10 }),
    ]
    const result = groupFilesByVersion(files)
    expect(result.flat).toBe(true)
    if (result.flat) expect(result.files).toBe(files) // giữ nguyên tham chiếu, không sắp lại
  })
})

describe('groupFilesByVersion — nhóm theo phiên bản khi có từ hai phiên bản trở lên', () => {
  it('hai phiên bản ra hai nhóm, bản ĐANG DÙNG lên đầu dù id nhỏ hơn', () => {
    const files = [
      file({ id: 1, filename: 'cu.pdf', version_id: 1, version_no: '1.0', is_current_version: false }),
      file({ id: 2, filename: 'moi.pdf', version_id: 2, version_no: '2.0', is_current_version: true }),
    ]
    const result = groupFilesByVersion(files)
    expect(result.flat).toBe(false)
    if (result.flat) return
    expect(result.groups.map((g) => g.versionId)).toEqual([2, 1])
    expect(result.groups[0]?.versionLabel).toBe('Bản 2.0 · đang dùng')
    expect(result.groups[1]?.versionLabel).toBe('Bản 1.0')
  })

  it('không phiên bản nào đang dùng (dữ liệu hỏng) vẫn sắp theo id giảm dần, không nổ', () => {
    const files = [
      file({ id: 1, filename: 'a.pdf', version_id: 1, version_no: '1.0', is_current_version: false }),
      file({ id: 2, filename: 'b.pdf', version_id: 3, version_no: '3.0', is_current_version: false }),
      file({ id: 3, filename: 'c.pdf', version_id: 2, version_no: '2.0', is_current_version: false }),
    ]
    const result = groupFilesByVersion(files)
    expect(result.flat).toBe(false)
    if (result.flat) return
    expect(result.groups.map((g) => g.versionId)).toEqual([3, 2, 1])
  })

  it('gom đúng tệp vào nhóm của nó, giữ nguyên thứ tự trong nhóm', () => {
    const files = [
      file({ id: 1, filename: 'a1.pdf', version_id: 1, version_no: '1.0', is_current_version: false }),
      file({ id: 2, filename: 'b1.pdf', version_id: 2, version_no: '2.0', is_current_version: true }),
      file({ id: 3, filename: 'a2.pdf', version_id: 1, version_no: '1.0', is_current_version: false }),
    ]
    const result = groupFilesByVersion(files)
    expect(result.flat).toBe(false)
    if (result.flat) return
    const oldGroup = result.groups.find((g) => g.versionId === 1)
    expect(oldGroup?.files.map((f) => f.filename)).toEqual(['a1.pdf', 'a2.pdf'])
  })

  it('tệp TRÙNG TÊN ở hai phiên bản khác nhau vẫn giữ cả hai, không gộp lại', () => {
    const files = [
      file({ id: 1, filename: 'hop-dong.pdf', version_id: 1, version_no: '1.0', is_current_version: false }),
      file({ id: 2, filename: 'hop-dong.pdf', version_id: 2, version_no: '2.0', is_current_version: true }),
    ]
    const result = groupFilesByVersion(files)
    expect(result.flat).toBe(false)
    if (result.flat) return
    expect(result.groups.flatMap((g) => g.files).map((f) => f.id)).toEqual(
      expect.arrayContaining([1, 2]),
    )
  })

  it('tệp TRÙNG TÊN trong CÙNG một phiên bản (đường phẳng) vẫn giữ cả hai dòng riêng', () => {
    const files = [
      file({ id: 1, filename: 'scan.pdf', version_id: 1 }),
      file({ id: 2, filename: 'scan.pdf', version_id: 1 }),
    ]
    const result = groupFilesByVersion(files)
    expect(result.flat).toBe(true)
    if (!result.flat) return
    expect(result.files).toHaveLength(2)
  })
})
