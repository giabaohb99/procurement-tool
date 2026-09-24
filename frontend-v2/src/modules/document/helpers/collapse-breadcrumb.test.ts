import { describe, expect, it } from 'vitest'

import { collapseBreadcrumb } from './collapse-breadcrumb'

function crumb(id: number) {
  return { id, name: `Thư mục ${id}` }
}

describe('collapseBreadcrumb', () => {
  it('rỗng thì không hiện gì, không nổ', () => {
    expect(collapseBreadcrumb([])).toEqual({ head: [], collapsed: [], tail: [] })
  })

  it('chỉ MỘT đoạn (thư mục gốc pháp nhân) → hiện nguyên, không gập', () => {
    const crumbs = [crumb(1)]
    expect(collapseBreadcrumb(crumbs)).toEqual({ head: [], collapsed: [], tail: crumbs })
  })

  it('đúng ngưỡng 4 đoạn → vẫn hiện đủ, chưa gập', () => {
    const crumbs = [crumb(1), crumb(2), crumb(3), crumb(4)]
    expect(collapseBreadcrumb(crumbs)).toEqual({ head: [], collapsed: [], tail: crumbs })
  })

  it('vượt ngưỡng (5 đoạn) → gập đúng giữa: đầu 1, cuối 2, giữa gập vào «…»', () => {
    const crumbs = [crumb(1), crumb(2), crumb(3), crumb(4), crumb(5)]
    expect(collapseBreadcrumb(crumbs)).toEqual({
      head: [crumb(1)],
      collapsed: [crumb(2), crumb(3)],
      tail: [crumb(4), crumb(5)],
    })
  })

  it('đường RẤT dài (10 đoạn) → phần gập chứa đúng số đoạn còn lại, không rơi đoạn nào', () => {
    const crumbs = Array.from({ length: 10 }, (_, i) => crumb(i + 1))
    const result = collapseBreadcrumb(crumbs)
    expect(result.head).toHaveLength(1)
    expect(result.collapsed).toHaveLength(7)
    expect(result.tail).toHaveLength(2)
    //  Ghép lại đúng thứ tự gốc — không mất, không lặp, không đảo đoạn nào.
    expect([...result.head, ...result.collapsed, ...result.tail]).toEqual(crumbs)
  })
})
