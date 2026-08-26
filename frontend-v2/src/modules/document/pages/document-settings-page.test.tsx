import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { PermissionEntity } from '@/core/authorization/permission-types'
import { DocumentSettingsPage } from './document-settings-page'

//  Khóa mà tài khoản đang thử được ĐỌC.
let canRead: PermissionEntity[] = []

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: (entity: PermissionEntity) => canRead.includes(entity),
    canAny: () => true,
  }),
}))

//  Bốn danh mục con tự gọi API riêng — không phải thứ màn này chịu trách nhiệm.
vi.mock('../components/document-type-catalog', () => ({
  DocumentTypeCatalog: () => <div>bảng loại văn bản</div>,
}))
vi.mock('../components/document-template-catalog', () => ({
  DocumentTemplateCatalog: () => <div>bảng thư viện mẫu</div>,
}))
vi.mock('../components/security-level-catalog', () => ({
  SecurityLevelCatalog: () => <div>bảng mức mật</div>,
}))
vi.mock('../components/document-partner-catalog', () => ({
  DocumentPartnerCatalog: () => <div>bảng đơn vị gửi nhận</div>,
}))

function build() {
  render(
    <MemoryRouter>
      <DocumentSettingsPage />
    </MemoryRouter>,
  )
}

beforeEach(() => {
  canRead = []
})

describe('DocumentSettingsPage', () => {
  //  CR-157: bốn tab chạy trên BỐN khóa khác nhau, còn mục menu chỉ hỏi «có bất
  //  kỳ khóa nào không». Trước đó cả trang gác bằng đúng `doc_type`: người chỉ
  //  giữ *Đơn vị gửi nhận* không vào nổi trang chứa đúng tab của mình, còn người
  //  có `doc_type` mà thiếu `security_level` thì vào được rồi bấm tab ăn 403.
  it('chỉ hiện tab mà tài khoản đọc được', () => {
    canRead = ['doc_type', 'external_party']
    build()

    expect(screen.getByRole('tab', { name: /Loại văn bản/ })).toBeInTheDocument()
    expect(screen.getByRole('tab', { name: /Đơn vị gửi nhận/ })).toBeInTheDocument()
    expect(screen.queryByRole('tab', { name: /Mức mật/ })).not.toBeInTheDocument()
    expect(screen.queryByRole('tab', { name: /Thư viện văn bản mẫu/ })).not.toBeInTheDocument()
  })

  it('chỉ có khóa của tab CUỐI thì vẫn mở đúng tab đó, không rơi vào tab trống', () => {
    //  `?tab=` mặc định trỏ vào «Loại văn bản» — tab người này không được xem.
    canRead = ['external_party']
    build()

    expect(screen.getByText('bảng đơn vị gửi nhận')).toBeInTheDocument()
    expect(screen.queryByText('bảng loại văn bản')).not.toBeInTheDocument()
  })

  it('không có khóa nào thì nói thẳng, đừng hiện khung rỗng', () => {
    build()

    expect(screen.getByText(/không có quyền xem danh mục nền nào/i)).toBeInTheDocument()
    expect(screen.queryByRole('tab')).not.toBeInTheDocument()
  })
})
