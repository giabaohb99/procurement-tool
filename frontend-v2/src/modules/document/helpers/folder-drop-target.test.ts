import { describe, expect, it } from 'vitest'

import { FOLDER_ACCESS_LEVEL } from '../types/document-folder'
import {
  deepestDescendantDepth,
  isValidFolderDropTarget,
  isValidFolderReorderTarget,
  MAX_FOLDER_DEPTH,
  reorderSiblingIds,
  type FolderDragSource,
} from './folder-drop-target'

const LEAF: FolderDragSource = { id: 5, path: '/1/5/', depth: 2 }

describe('isValidFolderDropTarget', () => {
  it('chặn thả vào CHÍNH NÓ', () => {
    expect(
      isValidFolderDropTarget(LEAF, {
        id: 5,
        path: '/1/5/',
        depth: 2,
        myLevel: FOLDER_ACCESS_LEVEL.manage,
      }),
    ).toBe(false)
  })

  it('chặn thả vào CON CHÁU của chính nó (path bắt đầu bằng path nguồn)', () => {
    expect(
      isValidFolderDropTarget(LEAF, {
        id: 9,
        path: '/1/5/9/',
        depth: 3,
        myLevel: FOLDER_ACCESS_LEVEL.manage,
      }),
    ).toBe(false)
  })

  //  Luật «chặn khác pháp nhân» BỎ 24/09/2026 (chuyển đâu tùy người dùng) —
  //  thả sang nhánh của một pháp nhân khác nay HỢP LỆ.
  it('allows dropping into a branch of ANOTHER company (company rule removed)', () => {
    expect(
      isValidFolderDropTarget(LEAF, {
        id: 7,
        path: '/2/7/',
        depth: 2,
        myLevel: FOLDER_ACCESS_LEVEL.manage,
      }),
    ).toBe(true)
  })

  it('cho phép thả vào một thư mục khác nhánh, mức Đóng góp trở lên', () => {
    expect(
      isValidFolderDropTarget(LEAF, {
        id: 7,
        path: '/1/7/',
        depth: 2,
        myLevel: FOLDER_ACCESS_LEVEL.contribute,
      }),
    ).toBe(true)
  })

  it('chặn khi mức quyền trên đích DƯỚI Đóng góp (Xem hoặc Riêng tư)', () => {
    const target = { id: 7, path: '/1/7/', depth: 2 }
    expect(isValidFolderDropTarget(LEAF, { ...target, myLevel: FOLDER_ACCESS_LEVEL.view })).toBe(
      false,
    )
    expect(isValidFolderDropTarget(LEAF, { ...target, myLevel: FOLDER_ACCESS_LEVEL.private })).toBe(
      false,
    )
  })

  it(`đúng ranh giới ${MAX_FOLDER_DEPTH} cấp: cấp SAU khi chuyển = ${MAX_FOLDER_DEPTH} thì được, vượt lên thì chặn`, () => {
    const target = {
      id: 7,
      path: '/1/7/',
      depth: MAX_FOLDER_DEPTH - 1,
      myLevel: FOLDER_ACCESS_LEVEL.manage,
    }
    expect(isValidFolderDropTarget(LEAF, target)).toBe(true)
    expect(isValidFolderDropTarget(LEAF, { ...target, depth: MAX_FOLDER_DEPTH })).toBe(false)
  })

  it('nhánh kéo có con cháu SÂU HƠN — chặn dựa trên cấp SÂU NHẤT sau khi chuyển, không chỉ cấp của chính node kéo', () => {
    //  LEAF ở cấp 2, nhưng nhánh nó có một cháu ở cấp 4 (sâu hơn 2 cấp). Thả
    //  vào đích cấp d thì cháu đó rơi xuống cấp d+1+2 — tính từ trần
    //  `MAX_FOLDER_DEPTH`.
    const source: FolderDragSource = { ...LEAF, deepestDescendantDepth: 4 }
    const lastOkDepth = MAX_FOLDER_DEPTH - 3
    const target = { id: 7, path: '/1/7/', depth: lastOkDepth, myLevel: FOLDER_ACCESS_LEVEL.manage }
    expect(isValidFolderDropTarget(source, target)).toBe(true)
    expect(isValidFolderDropTarget(source, { ...target, depth: lastOkDepth + 1 })).toBe(false)
  })

  it('không truyền deepestDescendantDepth thì coi nhánh kéo chỉ có một cấp (node lá)', () => {
    expect(
      isValidFolderDropTarget(LEAF, {
        id: 7,
        path: '/1/7/',
        depth: MAX_FOLDER_DEPTH - 1,
        myLevel: FOLDER_ACCESS_LEVEL.manage,
      }),
    ).toBe(true)
  })
})

describe('deepestDescendantDepth', () => {
  it('không có con cháu nào thì trả về đúng cấp của chính nó', () => {
    expect(deepestDescendantDepth([{ id: 5, path: '/1/5/', depth: 2 }], LEAF)).toBe(2)
  })

  it('lấy CẤP SÂU NHẤT trong số các cháu, không phải cháu đầu tiên tìm thấy', () => {
    const rows = [
      { id: 5, path: '/1/5/', depth: 2 },
      { id: 9, path: '/1/5/9/', depth: 3 },
      { id: 11, path: '/1/5/9/11/', depth: 4 },
      { id: 12, path: '/1/5/12/', depth: 3 },
    ]
    expect(deepestDescendantDepth(rows, LEAF)).toBe(4)
  })

  it('bỏ qua node CÙNG PATH PREFIX nhưng thuộc NHÁNH KHÁC (không phải con cháu thật)', () => {
    //  `/1/50/` bắt đầu bằng `/1/5` dưới dạng CHUỖI THÔ nhưng không phải con
    //  cháu — path thật của node 5 tự đóng bằng dấu `/` (`/1/5/`) nên phép so
    //  `startsWith` trên `path` (đã có dấu `/` ở cuối) không mắc bẫy này.
    const rows = [
      { id: 5, path: '/1/5/', depth: 2 },
      { id: 50, path: '/1/50/', depth: 2 },
    ]
    expect(deepestDescendantDepth(rows, LEAF)).toBe(2)
  })

  it('danh sách chỉ có chính node đó (chưa nạp cháu) thì không nổ, trả về cấp của nó', () => {
    expect(deepestDescendantDepth([], LEAF)).toBe(2)
  })
})

describe('isValidFolderReorderTarget', () => {
  const source = { id: 5, parentId: 1 }

  it('chặn thả vào CHÍNH NÓ', () => {
    expect(
      isValidFolderReorderTarget(source, {
        id: 5,
        parentId: 1,
        parentMyLevel: FOLDER_ACCESS_LEVEL.manage,
      }),
    ).toBe(false)
  })

  it('chặn khi KHÁC CHA — đổi thứ tự chỉ áp dụng cho anh em cùng cha, đổi cha phải đi đường khác', () => {
    expect(
      isValidFolderReorderTarget(source, {
        id: 9,
        parentId: 2,
        parentMyLevel: FOLDER_ACCESS_LEVEL.manage,
      }),
    ).toBe(false)
  })

  it('chặn khi mức quyền trên CHA CHUNG dưới QUẢN LÝ — kể cả Đóng góp (đủ cho đổi cha nhưng không đủ đổi thứ tự)', () => {
    expect(
      isValidFolderReorderTarget(source, {
        id: 9,
        parentId: 1,
        parentMyLevel: FOLDER_ACCESS_LEVEL.contribute,
      }),
    ).toBe(false)
  })

  it('cho phép: cùng cha, mức QUẢN LÝ trên cha chung', () => {
    expect(
      isValidFolderReorderTarget(source, {
        id: 9,
        parentId: 1,
        parentMyLevel: FOLDER_ACCESS_LEVEL.manage,
      }),
    ).toBe(true)
  })
})

describe('reorderSiblingIds', () => {
  it('kéo dòng ĐẦU xuống thả SAU dòng CUỐI — đúng thứ tự vòng ra sau cùng', () => {
    expect(reorderSiblingIds([1, 2, 3], 1, 3, 'after')).toEqual([2, 3, 1])
  })

  it('kéo dòng CUỐI lên thả TRƯỚC dòng ĐẦU — đúng thứ tự lên đầu', () => {
    expect(reorderSiblingIds([1, 2, 3], 3, 1, 'before')).toEqual([3, 1, 2])
  })

  it('thả TRƯỚC ngay dòng liền kề phía sau — không đổi gì (đã đúng vị trí đó)', () => {
    expect(reorderSiblingIds([1, 2, 3], 1, 2, 'before')).toEqual([1, 2, 3])
  })

  it('thả SAU ngay dòng liền kề phía trước — không đổi gì (đã đúng vị trí đó)', () => {
    expect(reorderSiblingIds([1, 2, 3], 2, 1, 'after')).toEqual([1, 2, 3])
  })

  it('kéo vào CHÍNH NÓ — trả nguyên mảng gốc, không nổ', () => {
    expect(reorderSiblingIds([1, 2, 3], 2, 2, 'after')).toEqual([1, 2, 3])
  })

  it('thiếu sourceId hoặc targetId trong mảng (dữ liệu vừa đổi giữa chừng) — trả nguyên mảng gốc', () => {
    expect(reorderSiblingIds([1, 2, 3], 99, 2, 'before')).toEqual([1, 2, 3])
    expect(reorderSiblingIds([1, 2, 3], 1, 99, 'before')).toEqual([1, 2, 3])
  })

  it('mảng RỖNG hoặc MỘT phần tử — không nổ, trả nguyên mảng gốc', () => {
    expect(reorderSiblingIds([], 1, 2, 'before')).toEqual([])
    expect(reorderSiblingIds([1], 1, 1, 'after')).toEqual([1])
  })

  it('không sửa mảng ĐẦU VÀO (thuần, không side-effect)', () => {
    const input = [1, 2, 3]
    reorderSiblingIds(input, 1, 3, 'after')
    expect(input).toEqual([1, 2, 3])
  })

  it('trần cấp khớp backend: 100 cấp tính cả gốc (folder_constants.MAX_DEPTH)', () => {
    //  Từng là 7 — đại ca mở lên 100 ngày 26/09/2026. Hai bên lệch nhau thì
    //  giao diện cho thả mà backend trả 400, hoặc ngược lại bôi xám oan.
    expect(MAX_FOLDER_DEPTH).toBe(100)
  })
})
