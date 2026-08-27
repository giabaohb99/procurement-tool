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
        expect(item.path, `${module.id} - ${item.label}`).toMatch(
          new RegExp(`^${module.path}(/|$)`),
        )
      }
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
