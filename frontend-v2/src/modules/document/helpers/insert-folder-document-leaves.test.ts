import { describe, expect, it } from 'vitest'

import type { TreeNode } from '@/shared/tree/tree-types'
import { insertFolderDocumentLeaves } from './insert-folder-document-leaves'
import { makeDocumentLeafId, makeEmptyLeafId, makeLoadingLeafId, makeMoreLeafId } from './folder-tree-document-leaf-id'
import type { FolderDocumentLeavesState } from '../hooks/use-folder-tree-document-leaves'
import type { DocFolderTreeNode } from '../types/document-folder'
import type { DocumentRecord } from '../types/document-record'

function folderNode(id: number, label: string, children?: TreeNode<DocFolderTreeNode>[]): TreeNode<DocFolderTreeNode> {
  return { id, label, children, expandable: true }
}

function doc(id: number, title: string): DocumentRecord {
  return { id, title } as DocumentRecord // chỉ hai trường hàm này đọc tới
}

function state(overrides: Partial<FolderDocumentLeavesState> = {}): FolderDocumentLeavesState {
  return { documents: [], total: 0, isLoading: false, ...overrides }
}

describe('insertFolderDocumentLeaves', () => {
  it('thư mục KHÔNG mở thì không đụng gì tới cây, không tốn tra cứu leaves', () => {
    const tree = [folderNode(1, 'A')]
    const { tree: out, leaves } = insertFolderDocumentLeaves(tree, new Set(), new Map())
    expect(out).toEqual(tree)
    expect(leaves.size).toBe(0)
  })

  it('thư mục mở, có văn bản trực tiếp: chèn SAU thư mục con thật, giữ đúng thứ tự', () => {
    const tree = [folderNode(1, 'A', [folderNode(2, 'Con')])]
    const leavesByFolder = new Map([[1, state({ documents: [doc(10, 'Văn bản X')], total: 1 })]])
    const { tree: out, leaves } = insertFolderDocumentLeaves(tree, new Set([1]), leavesByFolder)

    const children = out[0].children ?? []
    expect(children.map((c) => c.id)).toEqual([2, makeDocumentLeafId(1, 10)])
    expect(leaves.get(makeDocumentLeafId(1, 10))).toEqual({
      type: 'document',
      document: doc(10, 'Văn bản X'),
      folderId: 1,
    })
  })

  it('thư mục mở, KHÔNG có thư mục con lẫn văn bản: hiện đúng MỘT dòng «(trống)»', () => {
    const tree = [folderNode(1, 'A')]
    const { tree: out, leaves } = insertFolderDocumentLeaves(tree, new Set([1]), new Map([[1, state()]]))
    const children = out[0].children ?? []
    expect(children).toHaveLength(1)
    expect(children[0].id).toBe(makeEmptyLeafId(1))
    expect(leaves.get(makeEmptyLeafId(1))).toEqual({ type: 'empty' })
  })

  it('có thư mục con thật nhưng KHÔNG có văn bản trực tiếp: KHÔNG hiện dòng «(trống)» (thư mục không thật sự rỗng)', () => {
    const tree = [folderNode(1, 'A', [folderNode(2, 'Con')])]
    const { tree: out } = insertFolderDocumentLeaves(tree, new Set([1]), new Map([[1, state()]]))
    const children = out[0].children ?? []
    expect(children.map((c) => c.id)).toEqual([2])
  })

  it('đang tải và CHƯA có thư mục con thật: hiện dòng «Đang tải…», không phải «(trống)»', () => {
    const tree = [folderNode(1, 'A')]
    const { tree: out, leaves } = insertFolderDocumentLeaves(
      tree,
      new Set([1]),
      new Map([[1, state({ isLoading: true })]]),
    )
    const children = out[0].children ?? []
    expect(children[0].id).toBe(makeLoadingLeafId(1))
    expect(leaves.get(makeLoadingLeafId(1))).toEqual({ type: 'loading' })
  })

  it('đang tải nhưng ĐÃ có thư mục con thật: không thêm dòng "đang tải" (đỡ rối mắt)', () => {
    const tree = [folderNode(1, 'A', [folderNode(2, 'Con')])]
    const { tree: out } = insertFolderDocumentLeaves(
      tree,
      new Set([1]),
      new Map([[1, state({ isLoading: true })]]),
    )
    const children = out[0].children ?? []
    expect(children.map((c) => c.id)).toEqual([2])
  })

  it('vượt trần trang: thêm dòng «Xem thêm n văn bản…» với số CÒN LẠI đúng', () => {
    const tree = [folderNode(1, 'A')]
    const leavesByFolder = new Map([[1, state({ documents: [doc(10, 'X')], total: 101 })]])
    const { tree: out, leaves } = insertFolderDocumentLeaves(tree, new Set([1]), leavesByFolder)
    const children = out[0].children ?? []
    const moreId = makeMoreLeafId(1)
    expect(children.map((c) => c.id)).toEqual([makeDocumentLeafId(1, 10), moreId])
    expect(leaves.get(moreId)).toEqual({ type: 'more', folderId: 1, remaining: 100 })
  })

  it('cây LỒNG NHIỀU cấp, chỉ CẤP CON đang mở: chèn đúng cấp, không đụng cấp khác', () => {
    const tree = [folderNode(1, 'A', [folderNode(2, 'B')])]
    const { tree: out } = insertFolderDocumentLeaves(
      tree,
      new Set([2]),
      new Map([[2, state({ documents: [doc(5, 'Y')], total: 1 })]]),
    )
    expect(out[0].children?.[0].children?.map((c) => c.id)).toEqual([makeDocumentLeafId(2, 5)])
    expect(out[0].children?.[0].id).toBe(2)
  })

  it('không nổ khi leavesByFolderId trống dù id nằm trong expandedIds (chưa kịp nạp)', () => {
    expect(() =>
      insertFolderDocumentLeaves([folderNode(1, 'A')], new Set([1]), new Map()),
    ).not.toThrow()
  })
})
