import { describe, expect, it } from 'vitest'

import { appRoutes } from '@/shared/constants/app-routes'
import { dossierModule } from './routes'

/**
 * Chốt BẢO MẬT của phân hệ Hồ sơ, không phải bài kiểm hình thức.
 *
 * Luật vá ngày 16/09/2026: **mọi route của phân hệ này phải nằm sau một mục menu
 * CÓ khóa quyền.** Lý do nằm ở hai nhánh "mở mặc định" của khung điều hướng:
 *
 * - `itemAllowed` coi mục **không khai `entity` là luôn hiện**;
 * - `canAccessRoute` trả `true` khi **không mục nào khớp đường dẫn**
 *   (`module-visibility.ts:141`).
 *
 * Nghĩa là một route không có mục menu gác thì mở cho **mọi người đăng nhập**, ở
 * cả hai lối vào, mà không dòng nào đỏ lên. Màn *Danh sách hồ sơ* đã dựng xong
 * khuôn nhưng chạy trên dữ liệu mẫu và khóa `dossier` chưa có ở backend — nối
 * `fetchDossiers` vào API thật trong tình trạng đó là lộ hồ sơ pháp lý của công
 * ty cho toàn bộ nhân viên. Xem ghi chú đầu `routes.tsx`.
 */
describe('phân hệ Hồ sơ — chốt phân quyền đường dẫn', () => {
  /** Mục menu thật sự gác được: có `entity` hoặc `entities` không rỗng. */
  const gatedPaths = dossierModule.nav
    .filter((item) => item.entity || item.entities?.length)
    .map((item) => item.path)

  it('mọi mục menu đều khai khóa quyền', () => {
    //  Bỏ `entity` của một mục là mục đó hiện với cả công ty. `module-registry`
    //  cũng canh luật này, nhưng nó canh qua danh sách miễn trừ dùng chung — chốt
    //  tại chỗ thì người sửa tệp này thấy ngay, khỏi phải lần sang tệp khác.
    const ungated = dossierModule.nav
      .filter((item) => !item.entity && !item.entities?.length)
      .map((item) => item.label)
    expect(ungated).toEqual([])
  })

  it('mọi route đều nằm sau một mục menu có khóa quyền', () => {
    //  Ngoại lệ DUY NHẤT là gốc phân hệ, vốn chỉ chuyển hướng (xem bài kế tiếp).
    const unguarded = dossierModule.routes
      .map((route) => route.path)
      .filter((path): path is string => typeof path === 'string')
      .filter((path) => path !== appRoutes.dossier.root)
      .filter((path) => !gatedPaths.some((g) => path === g || path.startsWith(`${g}/`)))

    expect(
      unguarded,
      'route không mục menu nào gác = mở cho mọi người đăng nhập (canAccessRoute trả true khi không khớp mục nào)',
    ).toEqual([])
  })

  it('gốc /dossier chỉ được CHUYỂN HƯỚNG, không được gắn màn nào', () => {
    //  Bài trên miễn trừ đường gốc, nên nếu không chốt thêm ở đây thì đổi phần
    //  `element` của nó từ `<Navigate>` sang màn danh sách hồ sơ là lách qua được
    //  cả hai bài mà vẫn mở màn đó cho toàn công ty.
    const root = dossierModule.routes.find((route) => route.path === appRoutes.dossier.root)

    expect(root, 'thiếu route gốc /dossier').toBeDefined()
    expect(
      root && 'lazy' in root ? root.lazy : undefined,
      'gốc /dossier nạp một màn — màn đó không có mục menu nào gác',
    ).toBeUndefined()
  })

  it('màn Danh sách hồ sơ (dữ liệu mẫu) CHƯA được đăng ký route', () => {
    //  Khuôn màn còn nguyên trên đĩa (`pages/dossier-list-page.tsx`) nhưng không
    //  chỗ nào gọi tới. Bật lại phải làm đủ bốn việc ở ghi chú đầu `routes.tsx` —
    //  việc thứ ba là khai khóa `dossier` kèm CỘT THẬT ở `SCOPE_FIELDS`, đừng khai
    //  `PUBLIC` cho xong vì `PUBLIC` nghĩa là `apply_scope` không lọc gì cả.
    const paths = dossierModule.routes.map((route) => route.path)
    expect(paths).toEqual([
      appRoutes.dossier.root,
      appRoutes.dossier.types,
      appRoutes.dossier.typeNew,
      appRoutes.dossier.typeDetail(':id'),
    ])
  })
})
