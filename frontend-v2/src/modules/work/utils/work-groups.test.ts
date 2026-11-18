import { describe, expect, it } from 'vitest'

import type { WorkGroupNode, WorkList, WorkSidebar } from '../types/work'
import { flattenGroups, groupNameOf, matchesProjectGroup } from './work-groups'

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
    expect(groupNameOf(groups, 42)).toBe('Nhóm dự án #42')
  })
})

describe('matchesProjectGroup (duoc-CR-782)', () => {
  const inGroup = list(1, 'ERP v2', 7)
  const loose = list(2, 'Nhân sự', null)

  it('keeps every project for "all"', () => {
    expect([inGroup, loose].filter((p) => matchesProjectGroup(p, 'all'))).toHaveLength(2)
  })

  it('treats a missing group id as "not in any group", never as group 0', () => {
    expect(matchesProjectGroup(loose, 'none')).toBe(true)
    expect(matchesProjectGroup(inGroup, 'none')).toBe(false)
    expect(matchesProjectGroup({ ...loose, group_id: 0 as unknown as null }, 'none')).toBe(true)
  })

  it('matches only the exact group id', () => {
    expect(matchesProjectGroup(inGroup, 7)).toBe(true)
    expect(matchesProjectGroup(inGroup, 8)).toBe(false)
    expect(matchesProjectGroup(loose, 7)).toBe(false)
  })
})
