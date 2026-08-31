import { describe, expect, it } from 'vitest'

import {
  allModules,
  customModuleRoutes,
  moduleRegistry,
  moduleRoutes,
} from './module-registry'

/**
 * Hợp đồng "thêm module = thêm một dòng" chỉ đứng vững nếu bảng đăng ký luôn
 * sạch. Những khẳng định dưới đây bắt các lỗi mà `tsc` không thấy: trùng id,
 * trùng đường dẫn, module bật nhưng chưa có route nào.
 */
describe('module-registry', () => {
  it('id của phân hệ là duy nhất', () => {
    const ids = allModules.map((m) => m.id)
    expect(new Set(ids).size).toBe(ids.length)
  })

  it('đường dẫn gốc của phân hệ là duy nhất', () => {
    const paths = allModules.filter((m) => m.path).map((m) => m.path)
    expect(new Set(paths).size).toBe(paths.length)
  })

  it('mỗi phân hệ đều có tên, mô tả và cặp màu để hiện ở màn chọn phân hệ', () => {
    for (const module of allModules) {
      expect(module.title, module.id).toBeTruthy()
      expect(module.description, module.id).toBeTruthy()
      expect(module.accent, module.id).toBeTruthy()
    }
  })

  it('phân hệ tắt không được vào router (vào thẳng URL phải ra 404)', () => {
    const disabled = allModules.filter((m) => !m.enabled)
    for (const module of disabled) {
      expect(moduleRegistry, module.id).not.toContain(module)
    }
  })

  it('phân hệ link ra app khác bị loại khỏi router', () => {
    // `path` rỗng của nó sẽ khớp bừa mọi URL nếu lọt vào bảng dò module theo URL.
    const external = allModules.filter((m) => m.externalUrl)
    expect(external.length).toBeGreaterThan(0) // Trung tâm HDSD
    for (const module of external) {
      expect(module.path, module.id).toBe('')
      expect(moduleRegistry, module.id).not.toContain(module)
    }
  })

  it('phân hệ đã đăng ký thì phải có đường dẫn tuyệt đối và ít nhất một route', () => {
    expect(moduleRegistry.length).toBeGreaterThan(0)
    for (const module of moduleRegistry) {
      expect(module.path, module.id).toMatch(/^\/[a-z0-9-]+$/)
      expect(module.routes.length, module.id).toBeGreaterThan(0)
    }
  })

  it('mục menu trái nào cũng nằm trong đường dẫn của chính phân hệ đó', () => {
    for (const module of moduleRegistry) {
      for (const item of module.nav) {
        if (item.crossModule) continue // lối tắt sang phân hệ khác — xét riêng bên dưới
        expect(item.path, `${module.id} - ${item.label}`).toMatch(
          new RegExp(`^${module.path}(/|$)`),
        )
      }
    }
  })

  it('đường dẫn phụ sang phân hệ khác phải trỏ vào một phân hệ CÓ THẬT và đang bật', () => {
    //  `crossModule` là khe duy nhất được phép ra khỏi đường dẫn của phân hệ mình
    //  (Thu mua mượn Công nợ / YCTT của Tài chính). Không canh thì gõ nhầm một
    //  chữ trong path là mục menu dẫn thẳng vào trang 404 mà chẳng ai hay.
    const shortcuts = moduleRegistry.flatMap((m) =>
      m.nav.filter((i) => i.crossModule).map((i) => ({ module: m, item: i })),
    )
    expect(shortcuts.length).toBeGreaterThan(0) // Thu mua -> Tài chính
    for (const { module, item } of shortcuts) {
      const target = moduleRegistry.find(
        (m) => m.path && (item.path === m.path || item.path.startsWith(`${m.path}/`)),
      )
      expect(target, `${module.id} - ${item.label}`).toBeDefined()
      // Trỏ về chính mình thì đừng khai `crossModule` — cờ đó tắt luôn phần kiểm
      // đường dẫn ở khẳng định trên, dùng bừa là mất chốt canh.
      expect(target?.id, `${module.id} - ${item.label}`).not.toBe(module.id)
    }
  })

  it('moduleRoutes + customModuleRoutes gom đủ route của các phân hệ đang bật, không lẫn nhau', () => {
    const inLayout = moduleRegistry
      .filter((m) => !m.customLayout)
      .reduce((sum, m) => sum + m.routes.length, 0)
    const custom = moduleRegistry
      .filter((m) => m.customLayout)
      .reduce((sum, m) => sum + m.routes.length, 0)
    expect(moduleRoutes).toHaveLength(inLayout)
    expect(customModuleRoutes).toHaveLength(custom)
    // Một route lọt cả hai danh sách là được mount hai lần — router sẽ khớp bừa.
    for (const route of customModuleRoutes) {
      expect(moduleRoutes).not.toContain(route)
    }
  })
  it('phân hệ nghiệp vụ không có mục menu bỏ trống khóa quyền — kẻo thẻ mở cho cả người ngoài', () => {
    //  LỖI ĐÃ XẢY RA (27/08/2026): mục «Tổng quan» của Thu mua / Sản xuất / Kho /
    //  Tài chính / Nhân sự không khai `entity`, mà thẻ phân hệ mở khi CÒN MỘT mục
    //  hiện được — nên tài khoản văn thư (không có quyền nào bên đó) vẫn thấy thẻ
    //  mở, vào trong gặp Tổng quan toàn số 0. Mục mới của phân hệ nghiệp vụ phải
    //  khai `entity`/`entities`; muốn mở công khai thật thì thêm id phân hệ vào
    //  danh sách chủ ý dưới đây kèm lý do.
    const openByDesign = new Set([
      'document', // «Chờ tôi duyệt» dành cho người duyệt NGOÀI phân hệ (xem module-visibility.ts)
      'forum', // bảng tin toàn công ty — mọi người đều vào
      'appearance', // tùy chọn hiển thị của chính người đăng nhập
    ])
    const missing: string[] = []
    for (const module of moduleRegistry) {
      if (openByDesign.has(module.id)) continue
      for (const item of module.nav) {
        if (!item.entity && !item.entities?.length) {
          missing.push(`${module.id} - ${item.label}`)
        }
      }
    }
    expect(missing).toEqual([])
  })

  it('màu icon phân hệ chạy được ở CẢ hai chế độ nền', () => {
    //  LỖI ĐÃ XẢY RA (27/08/2026): cả 20 phân hệ tô nền ô icon bằng bậc nhạt đặc
    //  (`bg-rose-50`, `bg-slate-100`). Bậc đó có độ sáng 96–98% nên nó trắng ở
    //  MỌI chế độ nền — bật nền tối là 20 mảng trắng chóe trên trang tối. Nền
    //  phải là màu đậm pha alpha để lộ nền phía sau, và chữ phải có biến thể
    //  `dark:` vì bậc 600 quá tối trên nền tối.
    const sai: string[] = []
    for (const module of moduleRegistry) {
      const khop = module.accent.match(
        /^bg-([a-z]+)-500\/10 text-\1-600 dark:text-\1-400$/,
      )
      if (!khop) sai.push(`${module.id}: ${module.accent}`)
    }
    expect(sai).toEqual([])
  })
})
