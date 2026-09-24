import { describe, expect, it } from 'vitest'

import { defaultFolderHint } from './default-folder-hint'
import type { DocFolderTreeNode } from '../types/document-folder'

function folder(overrides: Partial<DocFolderTreeNode> & { id: number }): DocFolderTreeNode {
  return {
    company_id: 1,
    parent_id: 0,
    kind: 2,
    kind_label: '',
    name: `Thư mục ${overrides.id}`,
    code: '',
    path: '',
    depth: 1,
    sort_order: 0,
    status: 1,
    status_label: '',
    document_count: 0,
    document_count_branch: 0,
    my_level: 2,
    ...overrides,
  }
}

describe('defaultFolderHint', () => {
  it('returns null when no company is selected yet (nothing to resolve)', () => {
    expect(defaultFolderHint([], 0, null)).toBeNull()
  })

  it('returns null when the folder tree has not loaded (no company root to fall back to)', () => {
    expect(defaultFolderHint([], 1, null)).toBeNull()
  })

  it('falls back to the company folder when the type has no default declared', () => {
    const companyRoot = folder({ id: 1, kind: 1, company_id: 5, name: 'CÔNG TY DEGO' })
    expect(defaultFolderHint([companyRoot], 5, null)).toBe(
      'Không chọn → văn bản sẽ vào thư mục "CÔNG TY DEGO".',
    )
  })

  it('falls back to the company folder when default_folder_id is 0 (unset sentinel)', () => {
    const companyRoot = folder({ id: 1, kind: 1, company_id: 5, name: 'CÔNG TY DEGO' })
    expect(defaultFolderHint([companyRoot], 5, 0)).toContain('CÔNG TY DEGO')
  })

  it('uses the type default folder when it belongs to the same company and is active', () => {
    const companyRoot = folder({ id: 1, kind: 1, company_id: 5, name: 'CÔNG TY DEGO' })
    const contractFolder = folder({ id: 9, company_id: 5, name: 'Hợp đồng' })
    expect(defaultFolderHint([companyRoot, contractFolder], 5, 9)).toBe(
      'Không chọn → văn bản sẽ vào thư mục "Hợp đồng".',
    )
  })

  // Lỗi âm thầm đáng ngại nhất: mặc định của loại thuộc pháp nhân KHÁC — dùng
  // nhầm nó thì câu báo chỉ một nơi trong khi văn bản thật lại rơi vào thư mục
  // pháp nhân đúng của nó (backend `resolve_default` cũng chặn y hệt).
  it('ignores the type default folder when it belongs to a different company', () => {
    const companyRootA = folder({ id: 1, kind: 1, company_id: 5, name: 'CÔNG TY A' })
    const folderInCompanyB = folder({ id: 9, company_id: 6, name: 'Hợp đồng của B' })
    expect(defaultFolderHint([companyRootA, folderInCompanyB], 5, 9)).toBe(
      'Không chọn → văn bản sẽ vào thư mục "CÔNG TY A".',
    )
  })

  it('ignores an archived type default folder and falls back to the company folder', () => {
    const companyRoot = folder({ id: 1, kind: 1, company_id: 5, name: 'CÔNG TY DEGO' })
    const archived = folder({ id: 9, company_id: 5, name: 'Đã ngừng dùng', status: 2 })
    expect(defaultFolderHint([companyRoot, archived], 5, 9)).toBe(
      'Không chọn → văn bản sẽ vào thư mục "CÔNG TY DEGO".',
    )
  })

  it('returns null when neither the declared default nor a company root can be resolved', () => {
    const unrelated = folder({ id: 9, company_id: 6, name: 'Của công ty khác' })
    expect(defaultFolderHint([unrelated], 5, 9)).toBeNull()
  })

  it('treats a negative or nonsensical default_folder_id as unset rather than throwing', () => {
    const companyRoot = folder({ id: 1, kind: 1, company_id: 5, name: 'CÔNG TY DEGO' })
    expect(defaultFolderHint([companyRoot], 5, -1)).toContain('CÔNG TY DEGO')
  })
})
