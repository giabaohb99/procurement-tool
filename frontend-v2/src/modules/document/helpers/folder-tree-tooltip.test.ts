import { describe, expect, it } from 'vitest'

import { buildFolderTooltip } from './folder-tree-tooltip'

function node(id: number, name: string, parent_id: number) {
  return { id, name, parent_id }
}

describe('buildFolderTooltip', () => {
  it('nối tên từ gốc tới chính node bằng " / "', () => {
    const byId = new Map([
      [1, node(1, 'CÔNG TY TNHH DEGO HOLDING', 0)],
      [2, node(2, 'Hợp đồng', 1)],
      [3, node(3, 'Mua bán', 2)],
    ])
    expect(buildFolderTooltip(node(3, 'Mua bán', 2), byId)).toBe(
      'CÔNG TY TNHH DEGO HOLDING / Hợp đồng / Mua bán',
    )
  })

  it('node gốc (parent_id = 0) chỉ trả đúng tên của chính nó', () => {
    const byId = new Map([[1, node(1, 'CÔNG TY', 0)]])
    expect(buildFolderTooltip(node(1, 'CÔNG TY', 0), byId)).toBe('CÔNG TY')
  })

  it('cha không có trong map (không thấy được) thì dừng lại, không nổ', () => {
    const byId = new Map([[2, node(2, 'Con', 1)]])
    expect(buildFolderTooltip(node(2, 'Con', 1), byId)).toBe('Con')
  })

  it('dữ liệu hỏng tự trỏ vòng (parent_id trỏ lại chính nó) không lặp vô hạn', () => {
    const byId = new Map([[1, node(1, 'Tự trỏ', 1)]])
    expect(buildFolderTooltip(node(1, 'Tự trỏ', 1), byId)).toBe('Tự trỏ')
  })

  it('vòng lặp GIỮA hai node (1↔2, dữ liệu hỏng) không lặp vô hạn', () => {
    const byId = new Map([
      [1, node(1, 'A', 2)],
      [2, node(2, 'B', 1)],
    ])
    expect(buildFolderTooltip(node(1, 'A', 2), byId)).toEqual(expect.any(String))
  })
})
