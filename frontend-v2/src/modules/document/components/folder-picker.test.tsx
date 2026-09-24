import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { PermissionAction, PermissionEntity } from '@/core/authorization/permission-types'
import { FolderPicker } from './folder-picker'
import {
  useCreateDocFolder,
  useDocFolderSearch,
  useDocFolderTree,
} from '../hooks/use-document-folders'
import type { DocFolderSearchResult, DocFolderTreeNode } from '../types/document-folder'

/**
 * Mọi hook cần dữ liệu thật đều mock TRỌN VẸN (cùng lối `book-documents-tab.test.tsx`)
 * — component dưới test chỉ chịu trách nhiệm LỌC (mức ≥ Đóng góp, đúng pháp
 * nhân) và ĐIỀU KHIỂN lựa chọn, không chịu trách nhiệm gọi mạng, nên không cần
 * `QueryClientProvider` thật.
 */
vi.mock('../hooks/use-document-folders', () => ({
  useDocFolderTree: vi.fn(),
  useDocFolderSearch: vi.fn(),
  useCreateDocFolder: vi.fn(),
}))

let canCreateFolder = true
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: (entity: PermissionEntity, action: PermissionAction) =>
      entity === 'doc_folder' && action === 'create' ? canCreateFolder : true,
  }),
}))

const COMPANY_A = 10
const COMPANY_B = 20

function node(overrides: Partial<DocFolderTreeNode> & { id: number }): DocFolderTreeNode {
  return {
    company_id: COMPANY_A,
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

const ROOT_A = node({ id: 1, kind: 1, company_id: COMPANY_A, parent_id: 0, name: 'CÔNG TY A' })
const CONTRACTS_A = node({ id: 2, company_id: COMPANY_A, parent_id: 1, name: 'Hợp đồng' })
//  Mức chỉ XEM (1) — dưới ngưỡng Đóng góp (2), KHÔNG được liệt kê để chọn.
const VIEW_ONLY_A = node({
  id: 3,
  company_id: COMPANY_A,
  parent_id: 1,
  name: 'Chỉ xem được',
  my_level: 1,
})
//  Cùng tên dễ nhầm nhưng khác PHÁP NHÂN — không được lẫn vào cây của công ty A.
const FOLDER_B = node({ id: 4, company_id: COMPANY_B, parent_id: 0, kind: 1, name: 'CÔNG TY B' })

function mockTree(nodes: DocFolderTreeNode[]) {
  vi.mocked(useDocFolderTree).mockReturnValue({ data: nodes } as unknown as ReturnType<
    typeof useDocFolderTree
  >)
}

function mockSearch(results: DocFolderSearchResult[]) {
  vi.mocked(useDocFolderSearch).mockReturnValue({ data: results } as unknown as ReturnType<
    typeof useDocFolderSearch
  >)
}

beforeEach(() => {
  canCreateFolder = true
  mockTree([ROOT_A, CONTRACTS_A, VIEW_ONLY_A, FOLDER_B])
  mockSearch([])
  vi.mocked(useCreateDocFolder).mockReturnValue({
    mutateAsync: vi.fn(),
    isPending: false,
  } as unknown as ReturnType<typeof useCreateDocFolder>)
})

describe('FolderPicker — cây chỉ liệt kê thư mục đủ điều kiện', () => {
  //  Luật «ẩn pháp nhân khác» BỎ 24/09/2026 — văn bản gắn vào thư mục nào cũng
  //  được; chỉ còn lọc theo MỨC Đóng góp.
  it('shows folders of EVERY company at Contribute level and up, hides View-only ones', async () => {
    const user = userEvent.setup()
    render(
      <FolderPicker
        companyId={COMPANY_A}
        folderIds={[]}
        primaryFolderId={null}
        onChange={vi.fn()}
      />,
    )

    await user.click(screen.getByRole('combobox'))

    expect(screen.getByText('CÔNG TY A')).toBeVisible()
    expect(screen.getByText('Hợp đồng')).toBeVisible()
    expect(screen.queryByText('Chỉ xem được')).not.toBeInTheDocument()
    expect(screen.getByText('CÔNG TY B')).toBeVisible()
  })

  it('companyId = 0 (Thiết lập loại văn bản) thì thấy thư mục của MỌI pháp nhân', async () => {
    const user = userEvent.setup()
    render(
      <FolderPicker folderIds={[]} primaryFolderId={null} onChange={vi.fn()} multiple={false} />,
    )

    await user.click(screen.getByRole('combobox'))

    expect(screen.getByText('CÔNG TY A')).toBeVisible()
    expect(screen.getByText('CÔNG TY B')).toBeVisible()
  })
})

describe('FolderPicker — chọn NHIỀU (màn tạo văn bản)', () => {
  it('bấm một thư mục thì thêm vào lựa chọn và đặt luôn làm thư mục CHÍNH', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(
      <FolderPicker
        companyId={COMPANY_A}
        folderIds={[]}
        primaryFolderId={null}
        onChange={onChange}
      />,
    )

    await user.click(screen.getByRole('combobox'))
    await user.click(screen.getByText('Hợp đồng'))

    expect(onChange).toHaveBeenCalledWith([2], 2)
  })

  it('bấm lại thư mục ĐÃ chọn thì gỡ nó ra, thư mục còn lại lên làm chính', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(
      <FolderPicker
        companyId={COMPANY_A}
        folderIds={[1, 2]}
        primaryFolderId={1}
        onChange={onChange}
      />,
    )

    // Chip của thư mục 1 (CÔNG TY A) và nút gỡ nằm trong hàng chip, không phải
    // trong cây — mở popover rồi bấm đúng dòng cây của thư mục 1.
    await user.click(screen.getByRole('combobox'))
    await user.click(screen.getByRole('treeitem', { name: /CÔNG TY A/ }))

    expect(onChange).toHaveBeenCalledWith([2], 2)
  })

  it('nhiều thư mục đã chọn hiện đủ chip, bấm ngôi sao đổi thư mục CHÍNH', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(
      <FolderPicker
        companyId={COMPANY_A}
        folderIds={[1, 2]}
        primaryFolderId={1}
        onChange={onChange}
      />,
    )

    expect(screen.getByText('CÔNG TY A')).toBeVisible()
    expect(screen.getByText('Hợp đồng')).toBeVisible()

    await user.click(screen.getByRole('button', { name: 'Đặt "Hợp đồng" làm thư mục chính' }))
    expect(onChange).toHaveBeenCalledWith([1, 2], 2)
  })

  it('chỉ một chip thì KHÔNG hiện ngôi sao — không có gì để chọn "chính"', () => {
    render(
      <FolderPicker companyId={COMPANY_A} folderIds={[2]} primaryFolderId={2} onChange={vi.fn()} />,
    )
    expect(screen.queryByTitle('Thư mục chính')).not.toBeInTheDocument()
    expect(screen.queryByTitle(/Đặt làm thư mục chính/)).not.toBeInTheDocument()
  })
})

describe('FolderPicker — chọn MỘT (Thư mục mặc định của loại văn bản)', () => {
  it('bấm thư mục khác thì THAY THẾ lựa chọn cũ, không cộng dồn', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    render(
      <FolderPicker folderIds={[1]} primaryFolderId={1} onChange={onChange} multiple={false} />,
    )

    await user.click(screen.getByRole('combobox'))
    await user.click(screen.getByText('Hợp đồng'))

    expect(onChange).toHaveBeenCalledWith([2], 2)
    expect(onChange).not.toHaveBeenCalledWith([1, 2], expect.anything())
  })
})

describe('FolderPicker — ô tìm (gõ ra danh sách phẳng kèm đường dẫn)', () => {
  it('search results filter by Contribute level only, other companies included', async () => {
    mockSearch([
      {
        id: 2,
        name: 'Hợp đồng',
        company_id: COMPANY_A,
        path_display: 'CÔNG TY A / Hợp đồng',
        my_level: 2,
        breadcrumb: [],
      },
      {
        id: 3,
        name: 'Chỉ xem được',
        company_id: COMPANY_A,
        path_display: 'CÔNG TY A / Chỉ xem được',
        my_level: 1,
        breadcrumb: [],
      },
      {
        id: 4,
        name: 'CÔNG TY B',
        company_id: COMPANY_B,
        path_display: 'CÔNG TY B',
        my_level: 3,
        breadcrumb: [],
      },
    ])
    const user = userEvent.setup()
    render(
      <FolderPicker
        companyId={COMPANY_A}
        folderIds={[]}
        primaryFolderId={null}
        onChange={vi.fn()}
      />,
    )

    await user.click(screen.getByRole('combobox'))
    await user.type(screen.getByPlaceholderText('Gõ tên thư mục…'), 'hop dong')

    expect(screen.getByText('CÔNG TY A / Hợp đồng')).toBeVisible()
    expect(screen.queryByText('Chỉ xem được')).not.toBeInTheDocument()
    //  Tên + đường dẫn cùng là «CÔNG TY B» nên khớp hơn một phần tử.
    expect(screen.getAllByText(/CÔNG TY B$/).length).toBeGreaterThan(0)
  })
})

describe('FolderPicker — câu gợi ý khi để trống', () => {
  it('rỗng + showEmptyHint thì nói rõ văn bản sẽ vào thư mục nào', () => {
    render(
      <FolderPicker
        companyId={COMPANY_A}
        folderIds={[]}
        primaryFolderId={null}
        onChange={vi.fn()}
        showEmptyHint
      />,
    )
    expect(screen.getByText('Không chọn → văn bản sẽ vào thư mục "CÔNG TY A".')).toBeVisible()
  })

  it('đã chọn ít nhất một thư mục thì KHÔNG hiện câu gợi ý nữa', () => {
    render(
      <FolderPicker
        companyId={COMPANY_A}
        folderIds={[2]}
        primaryFolderId={2}
        onChange={vi.fn()}
        showEmptyHint
      />,
    )
    expect(screen.queryByText(/văn bản sẽ vào thư mục/)).not.toBeInTheDocument()
  })
})

describe('FolderPicker — nút «Tạo thư mục mới»', () => {
  it('không có quyền doc_folder.create thì ẩn nút', async () => {
    canCreateFolder = false
    const user = userEvent.setup()
    render(
      <FolderPicker
        companyId={COMPANY_A}
        folderIds={[]}
        primaryFolderId={null}
        onChange={vi.fn()}
      />,
    )
    await user.click(screen.getByRole('combobox'))
    expect(screen.queryByText('Tạo thư mục mới')).not.toBeInTheDocument()
  })

  it('companyId = 0 (Thiết lập loại) thì ẩn nút — không có pháp nhân nào làm cha rõ ràng', async () => {
    const user = userEvent.setup()
    render(
      <FolderPicker folderIds={[]} primaryFolderId={null} onChange={vi.fn()} multiple={false} />,
    )
    await user.click(screen.getByRole('combobox'))
    expect(screen.queryByText('Tạo thư mục mới')).not.toBeInTheDocument()
  })

  it('có quyền và có pháp nhân thì tạo xong tự thêm vào lựa chọn', async () => {
    const user = userEvent.setup()
    const onChange = vi.fn()
    const created = node({ id: 99, company_id: COMPANY_A, parent_id: 1, name: 'Vừa tạo' })
    const mutateAsync = vi.fn().mockResolvedValue(created)
    vi.mocked(useCreateDocFolder).mockReturnValue({
      mutateAsync,
      isPending: false,
    } as unknown as ReturnType<typeof useCreateDocFolder>)

    render(
      <FolderPicker
        companyId={COMPANY_A}
        folderIds={[]}
        primaryFolderId={null}
        onChange={onChange}
      />,
    )
    await user.click(screen.getByRole('combobox'))
    await user.click(screen.getByText('Tạo thư mục mới'))
    await user.type(screen.getByPlaceholderText('Tên thư mục mới…'), 'Vừa tạo')
    await user.click(screen.getByRole('button', { name: 'Tạo' }))

    expect(mutateAsync).toHaveBeenCalledWith({ parent_id: 1, name: 'Vừa tạo' })
    expect(onChange).toHaveBeenCalledWith([99], 99)
  })
})
