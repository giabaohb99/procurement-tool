import { describe, expect, it } from 'vitest'

import { ENTITIES } from '@/core/authorization/permission-types'
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
 * cả hai lối vào, mà không dòng nào đỏ lên. Màn *Danh sách hồ sơ* đã từng nằm
 * đúng trong tình trạng đó và phải gỡ khỏi routing; nay nó quay lại vì khóa
 * `dossier` đã có thật ở backend, khai **cột thật** trong `SCOPE_FIELDS`.
 *
 * ⚠️ Đây là chốt của GIAO DIỆN, và giao diện không bao giờ là bảo mật. Chốt thật
 * nằm ở `require()` + `apply_scope()` của backend — kiểm ở
 * `test/backend/test_ho_so_pham_vi.py`.
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

  it('khóa quyền của mọi mục menu đều CÓ THẬT ở backend', () => {
    //  Gõ sai tên khóa (`dossiers`, `dossier_list`…) thì `can()` trả false với
    //  MỌI người và mục menu biến mất im lặng — đọc ra như "chưa ai được cấp
    //  quyền", nên người đi sửa sẽ vào màn Phân quyền tìm một ô tick không tồn tại.
    const entities: string[] = ENTITIES as unknown as string[]
    for (const item of dossierModule.nav) {
      for (const key of [item.entity, ...(item.entities ?? [])].filter(Boolean)) {
        expect(entities, `mục «${item.label}» khai khóa lạ: ${key}`).toContain(key)
      }
    }
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
    //  `element` của nó từ `<Navigate>` sang một màn bất kỳ là lách qua được cả
    //  hai bài mà vẫn mở màn đó cho toàn công ty.
    const root = dossierModule.routes.find((route) => route.path === appRoutes.dossier.root)

    expect(root, 'thiếu route gốc /dossier').toBeDefined()
    expect(
      root && 'lazy' in root ? root.lazy : undefined,
      'gốc /dossier nạp một màn — màn đó không có mục menu nào gác',
    ).toBeUndefined()
  })

  it('hai màn nằm sau HAI khóa khác nhau, không dùng chung một khóa', () => {
    //  Luật «một khóa = một màn hình» (CR-157) ở đây không phải chuyện gọn gàng:
    //  loại hồ sơ là KHUÔN BIỂU MẪU của hồ sơ (`field_schema`), nên gộp chung
    //  một khóa là ai lập được một tờ giấy phép cũng xóa được ô «Số giấy phép»
    //  khỏi mọi hồ sơ cùng loại.
    const byPath = new Map(dossierModule.nav.map((item) => [item.path, item.entity]))
    expect(byPath.get(appRoutes.dossier.list)).toBe('dossier')
    expect(byPath.get(appRoutes.dossier.types)).toBe('dossier_type')
  })

  it('route đăng ký đúng bộ đường dẫn mong đợi, và `/new` đứng TRƯỚC `/:id`', () => {
    const paths = dossierModule.routes.map((route) => route.path)
    expect(paths).toEqual([
      appRoutes.dossier.root,
      appRoutes.dossier.list,
      appRoutes.dossier.newDossier,
      appRoutes.dossier.detail(':id'),
      appRoutes.dossier.types,
      appRoutes.dossier.typeNew,
      appRoutes.dossier.typeDetail(':id'),
    ])

    //  ⚠️ Thứ tự là luật, không phải thẩm mỹ: react-router khớp theo thứ tự đăng
    //  ký, nên `/:id` đứng trước thì «new» bị nuốt thành một id — khung CRUD gọi
    //  API chi tiết với `id = "new"` và người dùng chỉ thấy màn báo lỗi tải.
    for (const [staticPath, dynamicPath] of [
      [appRoutes.dossier.newDossier, appRoutes.dossier.detail(':id')],
      [appRoutes.dossier.typeNew, appRoutes.dossier.typeDetail(':id')],
    ]) {
      expect(
        paths.indexOf(staticPath),
        `${staticPath} phải đăng ký trước ${dynamicPath}`,
      ).toBeLessThan(paths.indexOf(dynamicPath))
    }
  })
})
