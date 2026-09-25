import { describe, expect, it } from 'vitest'

import type { WorkGroupNode, WorkList, WorkSidebar } from '../types/work'
import { flattenGroups, groupNameOf } from './work-groups'

function list(id: number, name: string, groupId: number | null): WorkList {
  return {
    id,
    name,
    description: '',
    color: '',
    group_id: groupId,
    sort_order: 0,
    is_archived: 0,
    my_role: 1,
    task_count: 0,
    task_done: 0,
    created_at: '2026-09-14',
  } as WorkList
}

function node(id: number, name: string, lists: WorkList[], children: WorkGroupNode[] = []): WorkGroupNode {
  return {
    id,
    name,
    description: '',
    parent_id: null,
    sort_order: 0,
    is_archived: 0,
    my_role: 1,
    lists,
    children,
  }
}

describe('flattenGroups — bao-CR-482', () => {
  it('duỗi cha rồi tới con, kèm độ sâu và số dự án trực tiếp', () => {
    const sidebar: WorkSidebar = {
      groups: [node(1, 'DX', [list(10, 'ERP v2', 1)], [node(5, 'Con', [list(11, 'X', 5), list(12, 'Y', 5)])])],
      lists: [list(99, 'Lẻ', null)],
    }
    expect(flattenGroups(sidebar).map((g) => [g.id, g.name, g.depth, g.listCount])).toEqual([
      [1, 'DX', 0, 1],
      [5, 'Con', 1, 2],
    ])
  })

  it('không có dữ liệu thì rỗng, không nổ', () => {
    expect(flattenGroups(undefined)).toEqual([])
  })

  it('groupNameOf: ngoài nhóm là chuỗi rỗng, nhóm không còn trong cây thì in số', () => {
    const groups = flattenGroups({ groups: [node(1, 'DX', [])], lists: [] })
    expect(groupNameOf(groups, null)).toBe('')
    expect(groupNameOf(groups, 1)).toBe('DX')
    expect(groupNameOf(groups, 42)).toBe('Nhóm #42')
  })
})
