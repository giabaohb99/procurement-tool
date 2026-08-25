import { describe, expect, it } from 'vitest'

import { FileText } from 'lucide-react'

import type { PermissionAction, PermissionEntity } from '@/core/authorization/permission-types'
import type { ErpModule } from './module-definition'
import { canAccessRoute, canOpenModule, visibleNavItems } from './module-visibility'

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

/** `can` giả lập theo (entity, action): map entity -> tập action được phép. */
function choPhepDay(map: Record<string, PermissionAction[]>) {
  return (entity: PermissionEntity, action: PermissionAction) =>
    (map[entity] ?? []).includes(action)
}

describe('canAccessRoute', () => {
  const navEmp = [
    { label: 'Nhân sự', path: '/x/emp', entity: 'employee', icon: FileText },
  ] as ErpModule['nav']

  it('trang chi tiết ăn theo quyền của mục danh sách khớp path dài nhất', () => {
    // /x/emp/5 không có mục riêng -> lấy quyền của /x/emp (entity=employee, read).
    expect(canAccessRoute(phanHe(navEmp), '/x/emp/5', choPhep())).toBe(false)
    expect(canAccessRoute(phanHe(navEmp), '/x/emp/5', choPhep('employee'))).toBe(true)
  })

  it('mục cụ thể hơn mà cố ý KHÔNG gác quyền thì cho xem, dù không có quyền entity cha', () => {
    // Mục con công khai (không entity) phải thắng mục cha có entity nhờ path dài hơn —
    // nếu ưu tiên nhầm mục cha, màn công khai sẽ bị khóa oan.
    const nav = [
      { label: 'Nhân sự', path: '/x/emp', entity: 'employee', icon: FileText },
      { label: 'Danh bạ công khai', path: '/x/emp/dir', icon: FileText },
    ] as ErpModule['nav']

    expect(canAccessRoute(phanHe(nav), '/x/emp/dir/9', choPhep())).toBe(true)
  })

  it('không mục nào khớp thì cho xem (backend vẫn gác)', () => {
    expect(canAccessRoute(phanHe(navEmp), '/x/khac', choPhep())).toBe(true)
  })

  it('mục khai action riêng thì hỏi đúng action đó, không phải read', () => {
    const nav = [
      { label: 'Chờ duyệt', path: '/x/duyet', entity: 'document', action: 'approve', icon: FileText },
    ] as ErpModule['nav']

    expect(canAccessRoute(phanHe(nav), '/x/duyet', choPhepDay({ document: ['read'] }))).toBe(false)
    expect(canAccessRoute(phanHe(nav), '/x/duyet', choPhepDay({ document: ['approve'] }))).toBe(true)
  })

  it('mục quản lý (manage) đòi quyền tạo/sửa/xóa, read thuần không đủ', () => {
    const nav = [
      { label: 'Danh mục', path: '/x/dm', entity: 'unit', manage: true, icon: FileText },
    ] as ErpModule['nav']

    expect(canAccessRoute(phanHe(nav), '/x/dm', choPhepDay({ unit: ['read'] }))).toBe(false)
    expect(canAccessRoute(phanHe(nav), '/x/dm', choPhepDay({ unit: ['write'] }))).toBe(true)
  })
})
