import { describe, expect, it } from 'vitest'

import { canAccessRoute, visibleNavItems } from '@/app/router/module-visibility'
import type { PermissionAction, PermissionEntity } from '@/core/authorization/permission-types'
import { appRoutes } from '@/shared/constants/app-routes'
import { documentModule } from './routes'

/**
 * BA MỤC MENU MỞ CHO NGƯỜI NGOÀI PHÂN HỆ.
 *
 * Cùng một cái bẫy đã vấp ba lần: gác mục menu bằng quyền vai trò trong khi
 * backend đã mở một khe riêng cho nhóm người khác. Người bị giấu mất mục menu
 * không có cách nào biết — họ chỉ thấy "chức năng không có tác dụng".
 *
 *  - «Văn bản»      → tab *Văn bản đến* mở cho mọi tài khoản đăng nhập.
 *  - «Chờ tôi duyệt» → người ký trong luồng thường không có vai trò nào ở Văn bản.
 *  - «Sổ văn bản»    → quyền xem sổ còn tới từ bảng thành viên (ô *Người xem sổ*).
 *
 * Cái thứ ba là lỗi khách báo 26/08/2026: chia sổ xong người được chia vào
 * trang của mình không thấy sổ đâu. Backend đã mở khe từ 25/08 (`nguoi_doc_so`)
 * nhưng cửa giao diện vẫn khóa `document_book.read`, nên mục menu biến mất và
 * gõ thẳng URL thì ăn trang 403 — trước cả khi bộ lọc theo từng quyển kịp chạy.
 */
const MUC_MO_CHO_NGUOI_NGOAI = [
  { label: 'Văn bản', path: appRoutes.document.documents },
  { label: 'Chờ tôi duyệt', path: appRoutes.document.pendingApproval },
  { label: 'Sổ văn bản', path: appRoutes.document.books },
]

/** Người dùng KHÔNG có một quyền nào — đúng bối cảnh của người được chia sổ. */
const khongCoQuyen = () => false

/** Chỉ có đúng một quyền được liệt kê. */
function chiCo(...allowed: `${PermissionEntity}.${PermissionAction}`[]) {
  return (entity: PermissionEntity, action: PermissionAction) =>
    allowed.includes(`${entity}.${action}` as (typeof allowed)[number])
}

describe('menu phân hệ Văn thư', () => {
  it.each(MUC_MO_CHO_NGUOI_NGOAI)(
    'mục «$label» KHÔNG gác quyền vai trò',
    ({ label }) => {
      const item = documentModule.nav.find((nav) => nav.label === label)
      expect(item, `thiếu mục «${label}»`).toBeDefined()
      //  Khai `entity` hay `entities` ở đây là khóa lại đúng nhóm người mà
      //  backend vừa mở khe cho.
      expect(item?.entity, label).toBeUndefined()
      expect(item?.entities, label).toBeUndefined()
    },
  )

  it.each(MUC_MO_CHO_NGUOI_NGOAI)(
    'người KHÔNG có quyền nào vẫn thấy mục «$label»',
    ({ label }) => {
      const labels = visibleNavItems(documentModule, khongCoQuyen).map((item) => item.label)
      expect(labels).toContain(label)
    },
  )

  it.each(MUC_MO_CHO_NGUOI_NGOAI)(
    'gõ thẳng URL của «$label» thì KHÔNG bị chặn 403',
    ({ path }) => {
      expect(canAccessRoute(documentModule, path, khongCoQuyen)).toBe(true)
    },
  )

  it('chi tiết một quyển sổ cũng mở — trang con ăn theo quyền của mục danh sách', () => {
    //  Chia sổ xong người ta bấm vào dòng sổ để xem bên trong; chặn ở đây thì
    //  danh sách hiện ra mà mở không được, còn khó hiểu hơn là không thấy gì.
    expect(
      canAccessRoute(documentModule, appRoutes.document.bookDetail(7), khongCoQuyen),
    ).toBe(true)
  })

  it('mở được phân hệ Văn thư dù không có quyền nào', () => {
    //  Cửa ngoài đóng thì khe bên trong thành mã chết — đúng lỗi DEMO_MANAGER
    //  22/08/2026 đã phải vá ở `canOpenModule`.
    expect(visibleNavItems(documentModule, khongCoQuyen).length).toBeGreaterThan(0)
  })

  // ── Cặp đối chứng: mở ba mục trên KHÔNG được biến thành mở toang ──────────
  it('mục danh mục nền VẪN gác quyền — không phải cứ đăng nhập là khai được sổ', () => {
    const labels = visibleNavItems(documentModule, khongCoQuyen).map((item) => item.label)
    const danhMuc = documentModule.nav.filter(
      (item) => item.group === 'Danh mục' || item.manage,
    )
    expect(danhMuc.length).toBeGreaterThan(0)
    for (const item of danhMuc) {
      expect(labels, item.label).not.toContain(item.label)
    }
  })

  it('có quyền quản lý danh mục thì mục danh mục hiện lại', () => {
    const co = chiCo('doc_type.create', 'doc_type.write', 'doc_type.delete')
    const labels = visibleNavItems(documentModule, co).map((item) => item.label)
    expect(labels.length).toBeGreaterThan(MUC_MO_CHO_NGUOI_NGOAI.length)
  })
})
