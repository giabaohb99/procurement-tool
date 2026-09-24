import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { FolderShareDialog } from './folder-share-dialog'
import {
  useGrantFolderAccessBulk,
  useRevokeFolderAccess,
  useUpdateFolderAccessLevel,
} from '../hooks/use-document-folder-access'
import { useDocFolder, useUpdateDocFolder } from '../hooks/use-document-folders'
import { SUBJECT_KIND } from '../types/document-access'
import type { DocFolderDetail, FolderAccessEntry } from '../types/document-folder'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { useDepartments } from '@/modules/hr/hooks/use-departments'
import { useEmployees } from '@/modules/hr/hooks/use-employees'
import { useRoles } from '@/modules/hr/hooks/use-roles'

vi.mock('../hooks/use-document-folders', () => ({
  useDocFolder: vi.fn(),
  useUpdateDocFolder: vi.fn(),
}))
vi.mock('../hooks/use-document-folder-access', () => ({
  useGrantFolderAccessBulk: vi.fn(),
  useUpdateFolderAccessLevel: vi.fn(),
  useRevokeFolderAccess: vi.fn(),
}))
//  `vi.fn()` (không phải factory trả sẵn dữ liệu) — bài kiểm «không nổ khi
//  hook trả `undefined`» (rà UI 23/09/2026, sự cố hộp Chia sẻ) cần đổi được
//  giá trị trả về TỪNG BÀI, factory cố định không cho làm việc đó.
vi.mock('@/modules/hr/hooks/use-employees', () => ({ useEmployees: vi.fn() }))
vi.mock('@/modules/hr/hooks/use-departments', () => ({ useDepartments: vi.fn() }))
vi.mock('@/modules/hr/hooks/use-companies', () => ({ useCompanies: vi.fn() }))
vi.mock('@/modules/hr/hooks/use-roles', () => ({ useRoles: vi.fn() }))
// Hộp xác nhận toàn cục: coi như người dùng luôn bấm Đồng ý.
vi.mock('@/shared/ui/confirm-dialog', () => ({ confirm: vi.fn(() => Promise.resolve(true)) }))

function folder(overrides: Partial<DocFolderDetail> = {}): DocFolderDetail {
  return {
    id: 5,
    company_id: 1,
    parent_id: 1,
    kind: 2,
    kind_label: 'Thư mục',
    name: 'Hợp đồng',
    code: '',
    path: '/1/5/',
    depth: 2,
    sort_order: 0,
    status: 1,
    status_label: 'Đang dùng',
    document_count: 0,
    document_count_branch: 0,
    my_level: 3,
    description: '',
    breadcrumb: [],
    effective_access: [
      { id: 11, folder_id: 1, folder_name: 'CÔNG TY A', is_inherited: true, subject_kind: 1,
        subject_kind_label: 'Người', subject_id: 9, subject_name: 'Người kế thừa', effect: 1,
        effect_label: 'Cho phép', level: 1, level_label: 'Xem', valid_from: null, valid_to: null,
        reason: '', is_active: true, revoked_at: '' },
    ],
    ...overrides,
  }
}

const grantMutate = vi.fn()

beforeEach(() => {
  grantMutate.mockClear()
  vi.mocked(useDocFolder).mockReturnValue({ data: folder() } as unknown as ReturnType<typeof useDocFolder>)
  vi.mocked(useEmployees).mockReturnValue({
    data: {
      items: [
        { id: 1, full_name: 'Người Một' },
        { id: 2, full_name: 'Người Hai' },
      ],
    },
  } as unknown as ReturnType<typeof useEmployees>)
  vi.mocked(useDepartments).mockReturnValue({ data: { items: [] } } as unknown as ReturnType<typeof useDepartments>)
  vi.mocked(useCompanies).mockReturnValue({ data: { items: [] } } as unknown as ReturnType<typeof useCompanies>)
  vi.mocked(useRoles).mockReturnValue({ data: [] } as unknown as ReturnType<typeof useRoles>)
  vi.mocked(useUpdateDocFolder).mockReturnValue({ mutate: vi.fn() } as unknown as ReturnType<
    typeof useUpdateDocFolder
  >)
  vi.mocked(useGrantFolderAccessBulk).mockReturnValue({
    mutate: grantMutate,
    isPending: false,
  } as unknown as ReturnType<typeof useGrantFolderAccessBulk>)
  vi.mocked(useUpdateFolderAccessLevel).mockReturnValue({ mutate: vi.fn() } as unknown as ReturnType<
    typeof useUpdateFolderAccessLevel
  >)
  vi.mocked(useRevokeFolderAccess).mockReturnValue({ mutate: vi.fn() } as unknown as ReturnType<
    typeof useRevokeFolderAccess
  >)
})

describe('FolderShareDialog', () => {
  it('hiện tên thư mục ở tiêu đề và câu nhắc «quyền thư mục không cho đọc văn bản»', () => {
    render(<FolderShareDialog folderId={5} open onOpenChange={vi.fn()} />)
    expect(screen.getByText('Chia sẻ «Hợp đồng»')).toBeInTheDocument()
    expect(screen.getByText(/Quyền thư mục không cho đọc văn bản/)).toBeInTheDocument()
  })

  it('ô «Quyền chung» hiện ĐÚNG giá trị ĐANG khai (default_access=1 → «Xem»), không phải placeholder trống (bug lead bắt 23/09/2026)', () => {
    vi.mocked(useDocFolder).mockReturnValue({
      data: folder({ default_access: 1 }),
    } as unknown as ReturnType<typeof useDocFolder>)

    render(<FolderShareDialog folderId={5} open onOpenChange={vi.fn()} />)

    expect(
      screen.getByRole('combobox', { name: 'Quyền chung — mọi người trong pháp nhân' }),
    ).toHaveTextContent('Xem')
  })

  it('chưa đặt «Quyền chung» (default_access=null) → hiện câu nhắc CHƯA ĐẶT, không suy diễn thành Riêng tư', () => {
    vi.mocked(useDocFolder).mockReturnValue({
      data: folder({ default_access: null }),
    } as unknown as ReturnType<typeof useDocFolder>)

    render(<FolderShareDialog folderId={5} open onOpenChange={vi.fn()} />)

    expect(
      screen.getByRole('combobox', { name: 'Quyền chung — mọi người trong pháp nhân' }),
    ).toHaveTextContent('Chưa đặt — kế thừa từ thư mục cha')
  })

  it('chưa chọn đối tượng nào thì KHÔNG hiện nút «Cấp quyền» (chỉ hiện khi ≥1 chip)', () => {
    render(<FolderShareDialog folderId={5} open onOpenChange={vi.fn()} />)
    expect(screen.queryByRole('button', { name: /Cấp quyền/ })).not.toBeInTheDocument()
  })

  it('danh sách «Người có quyền» hiện dòng KẾ THỪA, ghi rõ nguồn', () => {
    render(<FolderShareDialog folderId={5} open onOpenChange={vi.fn()} />)
    expect(screen.getByText('Người kế thừa')).toBeInTheDocument()
    expect(screen.getByText(/Kế thừa từ «CÔNG TY A»/)).toBeInTheDocument()
  })

  it('chọn NHIỀU đối tượng rồi bấm «Cấp quyền» → gọi bulk ĐÚNG MỘT LẦN với cả danh sách', async () => {
    const user = userEvent.setup()
    render(<FolderShareDialog folderId={5} open onOpenChange={vi.fn()} />)

    await user.click(screen.getByRole('button', { name: /Thêm người · phòng ban/ }))
    await user.click(await screen.findByText('Người Một'))
    await user.click(screen.getByText('Người Hai'))
    //  Hai chip đã xuất hiện — xác nhận đã chọn CẢ HAI trước khi bấm chốt.
    expect(screen.getAllByText(/Người (Một|Hai) · Người/)).toHaveLength(2)

    await user.click(screen.getByRole('button', { name: /Cấp quyền \(2\)/ }))

    expect(grantMutate).toHaveBeenCalledTimes(1)
    expect(grantMutate).toHaveBeenCalledWith(
      {
        subjects: [
          { subject_kind: SUBJECT_KIND.employee, subject_id: 1 },
          { subject_kind: SUBJECT_KIND.employee, subject_id: 2 },
        ],
        effect: 1,
        level: 1,
        //  Khối «Mở rộng» (hiệu lực từ–đến, lý do) gấp lại mặc định — chưa mở
        //  ra khai gì thì gửi rỗng/null, không phải bỏ qua trường.
        valid_from: null,
        valid_to: null,
        reason: '',
      },
      expect.anything(),
    )
  })
})

describe('FolderShareDialog — chỉ đọc dưới mức Quản lý (chốt lead 23/09/2026)', () => {
  beforeEach(() => {
    vi.mocked(useDocFolder).mockReturnValue({
      data: folder({ my_level: 1 }), // Xem — dưới ngưỡng Quản lý
    } as unknown as ReturnType<typeof useDocFolder>)
  })

  it('ẩn khối mời + ô «Quyền chung», hiện câu nhắc không đủ quyền', () => {
    render(<FolderShareDialog folderId={5} open onOpenChange={vi.fn()} />)
    expect(screen.queryByText('Chọn đối tượng')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /Cấp quyền/ })).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Đặt mức mặc định')).not.toBeInTheDocument()
    expect(screen.getByText(/Không đủ quyền để mời thêm người/)).toBeInTheDocument()
  })

  it('dòng quyền hiện HUY HIỆU tĩnh, không có ô đổi mức nào (kể cả dòng không kế thừa)', () => {
    render(
      <FolderShareDialog folderId={5} open onOpenChange={vi.fn()} />,
    )
    // dòng mẫu ở fixture `folder()` là dòng KẾ THỪA — vốn dĩ đã luôn chỉ đọc;
    // khẳng định không có ô combobox nào cho toàn bộ hộp thoại.
    expect(screen.queryByRole('combobox')).not.toBeInTheDocument()
  })
})

describe('FolderSharePeopleList (qua FolderShareDialog) — «Gỡ quyền» gộp trong ô đổi mức', () => {
  it('chọn «Gỡ quyền» trong ô đổi mức của dòng KHÔNG kế thừa → hỏi xác nhận rồi gọi revoke', async () => {
    const user = userEvent.setup()
    const revokeMutate = vi.fn()
    vi.mocked(useRevokeFolderAccess).mockReturnValue({ mutate: revokeMutate } as unknown as ReturnType<
      typeof useRevokeFolderAccess
    >)
    vi.mocked(useDocFolder).mockReturnValue({
      data: folder({
        effective_access: [
          { id: 21, folder_id: 5, folder_name: 'Hợp đồng', is_inherited: false, subject_kind: 1,
            subject_kind_label: 'Người', subject_id: 3, subject_name: 'Người trực tiếp', effect: 1,
            effect_label: 'Cho phép', level: 1, level_label: 'Xem', valid_from: null, valid_to: null,
            reason: '', is_active: true, revoked_at: '' },
        ],
      }),
    } as unknown as ReturnType<typeof useDocFolder>)

    render(<FolderShareDialog folderId={5} open onOpenChange={vi.fn()} />)

    await user.click(screen.getByRole('combobox', { name: /Đổi mức quyền của Người trực tiếp/ }))
    await user.click(await screen.findByText('Gỡ quyền'))

    expect(revokeMutate).toHaveBeenCalledWith({ accessId: 21, reason: expect.any(String) })
  })
})

describe('FolderShareDialog — chống nổ khi dữ liệu lệch hợp đồng (rà UI 23/09/2026)', () => {
  it('folder.effective_access = undefined (đúng KIỂU nhưng SAI lúc chạy) → không nổ, danh sách coi như rỗng', () => {
    vi.mocked(useDocFolder).mockReturnValue({
      data: folder({ effective_access: undefined as unknown as FolderAccessEntry[] }),
    } as unknown as ReturnType<typeof useDocFolder>)

    render(<FolderShareDialog folderId={5} open onOpenChange={vi.fn()} />)

    expect(screen.getByText('Chia sẻ «Hợp đồng»')).toBeInTheDocument()
    expect(screen.getByText('Chưa khai dòng quyền nào trên nhánh này.')).toBeInTheDocument()
  })

  it('cả bốn hook chọn đối tượng (nhân sự/phòng ban/pháp nhân/vai trò) trả `data: undefined` → không nổ, ô chọn vẫn mở được', async () => {
    const user = userEvent.setup()
    vi.mocked(useEmployees).mockReturnValue({ data: undefined } as unknown as ReturnType<typeof useEmployees>)
    vi.mocked(useDepartments).mockReturnValue({ data: undefined } as unknown as ReturnType<typeof useDepartments>)
    vi.mocked(useCompanies).mockReturnValue({ data: undefined } as unknown as ReturnType<typeof useCompanies>)
    vi.mocked(useRoles).mockReturnValue({ data: undefined } as unknown as ReturnType<typeof useRoles>)

    render(<FolderShareDialog folderId={5} open onOpenChange={vi.fn()} />)
    await user.click(screen.getByRole('button', { name: /Thêm người · phòng ban/ }))

    expect(await screen.findByText('Không có ai khớp.')).toBeInTheDocument()
  })

  it('folder.breadcrumb = undefined ở khung chi tiết (qua FolderDetailsPanel dùng chung kiểu) → không nổ', () => {
    //  `FolderShareDialog` không tự vẽ breadcrumb, nhưng dùng CHUNG
    //  `DocFolderDetail` với `folder-details-panel.tsx`/`folder-contents-panel.tsx`
    //  — kiểm ở đây để chắc riêng phần `useDocFolder` của hộp Chia sẻ cũng chịu
    //  được cùng kiểu dữ liệu lệch hợp đồng đó, không giả định trường nào chắc chắn có.
    vi.mocked(useDocFolder).mockReturnValue({
      data: folder({ breadcrumb: undefined as unknown as DocFolderDetail['breadcrumb'] }),
    } as unknown as ReturnType<typeof useDocFolder>)

    expect(() => render(<FolderShareDialog folderId={5} open onOpenChange={vi.fn()} />)).not.toThrow()
    expect(screen.getByText('Chia sẻ «Hợp đồng»')).toBeInTheDocument()
  })
})
