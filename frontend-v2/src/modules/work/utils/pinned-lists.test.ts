import { describe, expect, it } from 'vitest'

import {
  MAX_PINNED_LISTS,
  parsePinnedLists,
  serializePinnedLists,
  togglePinned,
} from './pinned-lists'

describe('pinned-lists', () => {
  it('đọc chuỗi lưu, bỏ rác và trùng, giữ thứ tự', () => {
    expect(parsePinnedLists('3, 1,abc,3,0,-2,2.5,7')).toEqual([3, 1, 7])
    expect(parsePinnedLists('')).toEqual([])
    expect(parsePinnedLists(undefined)).toEqual([])
  })

  it('khứ hồi giữ nguyên', () => {
    expect(parsePinnedLists(serializePinnedLists([5, 2, 9]))).toEqual([5, 2, 9])
  })

  it('bật ghim đứng cuối, tắt ghim gỡ ra', () => {
    expect(togglePinned([1, 2], 3)).toEqual([1, 2, 3])
    expect(togglePinned([1, 2, 3], 2)).toEqual([1, 3])
  })

  it('đủ trần thì không ghim thêm nhưng vẫn gỡ được', () => {
    const full = Array.from({ length: MAX_PINNED_LISTS }, (_, i) => i + 1)
    expect(togglePinned(full, 999)).toEqual(full)
    expect(togglePinned(full, 1)).toHaveLength(MAX_PINNED_LISTS - 1)
  })

  it('đọc không vượt trần dù chuỗi lưu dài hơn', () => {
    const raw = Array.from({ length: MAX_PINNED_LISTS + 5 }, (_, i) => i + 1).join(',')
    expect(parsePinnedLists(raw)).toHaveLength(MAX_PINNED_LISTS)
  })
})

describe('collectSidebarLists', () => {
  it('gom dự án đứng lẻ, trong nhóm và trong nhóm con', async () => {
    const { collectSidebarLists } = await import('./pinned-lists')
    const tree = [
      { lists: [{ id: 1 }], children: [{ lists: [{ id: 2 }], children: [] }] },
      { lists: [{ id: 3 }], children: [] },
    ]
    expect(
      collectSidebarLists(tree, [{ id: 9 }])
        .map((l) => l.id)
        .sort(),
    ).toEqual([1, 2, 3, 9])
  })
})
