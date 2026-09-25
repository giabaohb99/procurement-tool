import { describe, expect, it } from 'vitest'

import { countSubfoldersByParent, formatFolderContentCount } from './folder-content-count'
import type { DocFolderTreeNode } from '../types/document-folder'

function node(id: number, parentId: number): DocFolderTreeNode {
  return {
    id,
    company_id: 1,
    parent_id: parentId,
    kind: 2,
    kind_label: '',
    name: `F${id}`,
    code: '',
    path: '',
    depth: 0,
    sort_order: 0,
    status: 1,
    status_label: '',
    document_count: 0,
    document_count_branch: 0,
    my_level: 3,
  }
}

describe('countSubfoldersByParent', () => {
  it('counts only DIRECT children, not grandchildren', () => {
    const counts = countSubfoldersByParent([node(1, 0), node(2, 1), node(3, 1), node(4, 2)])
    expect(counts.get(1)).toBe(2)
    expect(counts.get(2)).toBe(1)
    expect(counts.get(4)).toBeUndefined()
  })

  it('ignores roots (parent_id 0) so id 0 never collects a bogus count', () => {
    expect(countSubfoldersByParent([node(1, 0), node(2, 0)]).has(0)).toBe(false)
  })

  it('tolerates undefined / empty data while the tree is still loading', () => {
    expect(countSubfoldersByParent(undefined).size).toBe(0)
    expect(countSubfoldersByParent([]).size).toBe(0)
  })
})

describe('formatFolderContentCount', () => {
  it('shows both parts joined by a dot', () => {
    expect(formatFolderContentCount(2, 5)).toBe('2 thư mục · 5 văn bản')
  })

  it('drops the zero part instead of printing "0 thư mục"', () => {
    expect(formatFolderContentCount(0, 5)).toBe('5 văn bản')
    expect(formatFolderContentCount(3, 0)).toBe('3 thư mục')
  })

  it('says "Trống" when there is nothing at all', () => {
    expect(formatFolderContentCount(0, 0)).toBe('Trống')
  })
})
