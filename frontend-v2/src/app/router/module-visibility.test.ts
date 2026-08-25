import { describe, expect, it } from 'vitest'

import { FileText } from 'lucide-react'

import type { PermissionEntity } from '@/core/authorization/permission-types'
import type { ErpModule } from './module-definition'
import { canOpenModule, visibleNavItems } from './module-visibility'

function phanHe(nav: ErpModule['nav'], entity?: string): ErpModule {
  return { id: 'x', title: 'X', path: '/x', enabled: true, entity, nav } as ErpModule
}

/** `can` giả lập: chỉ mấy entity trong danh sách là đọc được. */
function choPhep(...duoc: string[]) {
  return (entity: PermissionEntity) => duoc.includes(entity)
}

describe('canOpenModule', () => {
  //  LỖI THẬT (22/08/2026): màn chọn phân hệ chỉ xét `module.entity`, nên
  //  DEMO_MANAGER — người ký ở ba trong bốn chặng luồng ban hành văn bản — thấy
  //  ô «Văn bản» đeo ổ khóa. Chuông báo 6 việc chờ mà không vào nổi chỗ để duyệt.
  it('người duyệt không có quyền trên phân hệ vẫn mở được nếu có mục không gác quyền', () => {
    const vanBan = phanHe(
      [
        { label: 'Văn bản', path: '/d/list', entity: 'document', icon: FileText },
        //  «Chờ tôi duyệt» cố ý không khai `entity`.
        { label: 'Chờ tôi duyệt', path: '/d/pending', icon: FileText },
      ],
      'document',
    )

    expect(canOpenModule(vanBan, choPhep())).toBe(true)
  })

  it('không thấy mục nào thì mới khóa', () => {
    const vanBan = phanHe([{ label: 'Văn bản', path: '/d/list', entity: 'document', icon: FileText }], 'document')

    expect(canOpenModule(vanBan, choPhep())).toBe(false)
    expect(canOpenModule(vanBan, choPhep('document'))).toBe(true)
  })

  it('có quyền một mục bất kỳ là mở được, không cần đúng entity của phân hệ', () => {
    const vanBan = phanHe(
      [
        { label: 'Văn bản', path: '/d/list', entity: 'document', icon: FileText },
        { label: 'Sổ văn bản', path: '/d/books', entity: 'document_book', icon: FileText },
      ],
      'document',
    )

    expect(canOpenModule(vanBan, choPhep('document_book'))).toBe(true)
  })

  it('phân hệ không có mục nào thì khóa, không sập', () => {
    expect(canOpenModule(phanHe([]), choPhep())).toBe(false)
  })
})

describe('visibleNavItems', () => {
  it('giữ lại mục không gác quyền và mục đã có quyền, bỏ phần còn lại', () => {
    const nav = [
      { label: 'Tổng quan', path: '/d', icon: FileText },
      { label: 'Văn bản', path: '/d/list', entity: 'document', icon: FileText },
      { label: 'Sổ', path: '/d/books', entity: 'document_book', icon: FileText },
    ] as ErpModule['nav']

    expect(visibleNavItems(phanHe(nav), choPhep('document_book')).map((i) => i.label)).toEqual([
      'Tổng quan',
      'Sổ',
    ])
  })
})

describe('mục gom nhiều màn con (`entities`)', () => {
  //  «Thiết lập văn bản» là MỘT mục menu chứa bốn tab chạy trên bốn khóa khác
  //  nhau. Trước CR-157 nó gác bằng đúng `doc_type`, nên người chỉ giữ *Đơn vị
  //  gửi nhận* không vào nổi trang chứa đúng tab của mình.
  const thietLap = [
    {
      label: 'Thiết lập văn bản',
      path: '/d/settings',
      icon: FileText,
      entities: ['doc_type', 'doc_template', 'security_level', 'external_party'],
    },
  ] as ErpModule['nav']

  it('có quyền trên BẤT KỲ khóa nào là hiện mục', () => {
    expect(visibleNavItems(phanHe(thietLap), choPhep('external_party'))).toHaveLength(1)
    expect(visibleNavItems(phanHe(thietLap), choPhep('doc_type'))).toHaveLength(1)
  })

  it('không có khóa nào thì ẩn — đừng biến nó thành mục ai cũng thấy', () => {
    expect(visibleNavItems(phanHe(thietLap), choPhep('document'))).toHaveLength(0)
  })

  it('mảng rỗng thì coi như không gác, giống mục bỏ trống `entity`', () => {
    const nav = [
      { label: 'Chờ tôi duyệt', path: '/d/pending', icon: FileText, entities: [] },
    ] as ErpModule['nav']
    expect(visibleNavItems(phanHe(nav), choPhep())).toHaveLength(1)
  })
})

describe('phân hệ LINK RA NGOÀI', () => {
  /** Đúng hình dạng `helpCenterModule`: không màn hình nào trong app này. */
  function linkRaNgoai(): ErpModule {
    return {
      id: 'help-center',
      title: 'Hướng dẫn sử dụng',
      path: '',
      externalUrl: () => 'http://localhost:8082',
      enabled: true,
      nav: [],
      routes: [],
    } as unknown as ErpModule
  }

  //  LỖI KHÁCH BÁO 25/08/2026: ô «Hướng dẫn sử dụng» đeo ổ khóa, không ai bấm
  //  vào được — kể cả admin. `canOpenModule` đo bằng "còn mục menu nào hiện
  //  không", mà phân hệ link ra ngoài có `nav: []` theo đúng bản chất nên luôn
  //  ra 0. Tài liệu dùng hệ thống mà không ai mở được là hỏng đúng chỗ đáng giá.
  it('luôn mở, kể cả tài khoản không có quyền nào', () => {
    expect(canOpenModule(linkRaNgoai(), choPhep())).toBe(true)
  })

  it('không phụ thuộc quyền của người dùng', () => {
    expect(canOpenModule(linkRaNgoai(), choPhep('help_article'))).toBe(true)
  })

  //  Chốt chiều ngược: đừng nới thành "phân hệ nào không có mục menu cũng mở".
  it('phân hệ THƯỜNG mà không thấy mục nào thì vẫn khóa', () => {
    expect(canOpenModule(phanHe([]), choPhep())).toBe(false)
  })
})
