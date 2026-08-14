import { describe, expect, it } from 'vitest'

import { allModules, moduleRegistry, moduleRoutes } from './module-registry'

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

  it('moduleRoutes gom đủ route của các phân hệ đang bật', () => {
    const total = moduleRegistry.reduce((sum, m) => sum + m.routes.length, 0)
    expect(moduleRoutes).toHaveLength(total)
  })
})
