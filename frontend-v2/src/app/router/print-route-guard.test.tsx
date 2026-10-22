import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ENTITIES, type PermissionMap } from '@/core/authorization/permission-types'
import { appRoutes } from '@/shared/constants/app-routes'
import { withPrintGuard } from './print-route-guard'
import { PRINT_ROUTE_ACCESS } from './print-route-access'

let state: { user: { permissions?: PermissionMap } | null } = { user: null }

vi.mock('@/core/auth/auth-store', () => ({
  useAuthStore: (selector: (s: typeof state) => unknown) => selector(state),
}))

function Secret() {
  return <p>NOI DUNG BAN IN</p>
}

function renderGuarded(path: string) {
  const Guarded = withPrintGuard(path, Secret)
  return render(
    <MemoryRouter>
      <Guarded />
    </MemoryRouter>,
  )
}

/** Gom mọi đường dẫn trong `appRoutes` (gọi hàm với ':id') có đoạn `/print/`. */
function collectPrintPaths(node: unknown, out: string[] = []): string[] {
  if (typeof node === 'string') {
    if (node.startsWith('/print/')) out.push(node)
  } else if (typeof node === 'function') {
    const value = (node as (id: string) => unknown)(':id')
    collectPrintPaths(value, out)
  } else if (node && typeof node === 'object') {
    Object.values(node).forEach((child) => collectPrintPaths(child, out))
  }
  return out
}

beforeEach(() => {
  state = { user: null }
})

describe('NF-20 — mọi route /print đều khai quyền', () => {
  //  Gác điều hướng mặc định MỞ: route in thêm sau mà quên khai ở đây thì ai
  //  đăng nhập cũng mở được. Bài này đỏ ngay lúc thêm route.
  it('mỗi đường /print/ trong appRoutes có mặt trong PRINT_ROUTE_ACCESS', () => {
    const printPaths = collectPrintPaths(appRoutes)
    expect(printPaths.length).toBeGreaterThanOrEqual(12)
    const missing = printPaths.filter((path) => !(path in PRINT_ROUTE_ACCESS))
    expect(missing).toEqual([])
  })

  it('không có khai quyền thừa cho route không còn tồn tại', () => {
    const printPaths = new Set(collectPrintPaths(appRoutes))
    expect(Object.keys(PRINT_ROUTE_ACCESS).filter((path) => !printPaths.has(path))).toEqual([])
  })

  it('entity khai là entity thật; route không gác theo vai trò phải ghi lý do', () => {
    for (const access of Object.values(PRINT_ROUTE_ACCESS)) {
      if ('flow' in access) expect(access.flow.length).toBeGreaterThan(10)
      else expect(ENTITIES).toContain(access.entity)
    }
  })
})

describe('withPrintGuard', () => {
  const orderPrint = appRoutes.procurement.purchaseOrderPrint(':id')

  it('chưa đăng nhập / chưa có bản đồ quyền: chặn, không dựng trang in', () => {
    renderGuarded(orderPrint)
    expect(screen.getByText('Không có quyền mở bản in')).toBeTruthy()
    expect(screen.queryByText('NOI DUNG BAN IN')).toBeNull()
  })

  it('có read nhưng thiếu print thì vẫn bị chặn (bản in đòi đúng hành động print)', () => {
    state = { user: { permissions: { purchase_order: { read: true } } as PermissionMap } }
    renderGuarded(orderPrint)
    expect(screen.queryByText('NOI DUNG BAN IN')).toBeNull()
    expect(screen.getByText(/purchase_order:print/)).toBeTruthy()
  })

  it('đủ quyền print thì hiện trang in', () => {
    state = { user: { permissions: { purchase_order: { print: true } } as PermissionMap } }
    renderGuarded(orderPrint)
    expect(screen.getByText('NOI DUNG BAN IN')).toBeTruthy()
  })

  it('route in chưa khai quyền thì ĐÓNG, không mở toang', () => {
    state = { user: { permissions: { purchase_order: { print: true } } as PermissionMap } }
    renderGuarded('/print/chua-khai/:id')
    expect(screen.queryByText('NOI DUNG BAN IN')).toBeNull()
  })

  it('route gác theo luồng duyệt (văn bản) không bị chặn ở giao diện dù không có vai trò', () => {
    state = { user: { permissions: {} as PermissionMap } }
    renderGuarded(appRoutes.document.documentPrint(':id'))
    expect(screen.getByText('NOI DUNG BAN IN')).toBeTruthy()
  })

  it('mỗi route khai entity: chỉ đúng quyền đó mới qua', () => {
    for (const [path, access] of Object.entries(PRINT_ROUTE_ACCESS)) {
      if ('flow' in access) continue
      state = { user: { permissions: { [access.entity]: { [access.action]: true } } as PermissionMap } }
      const { unmount } = renderGuarded(path)
      expect(screen.queryByText('NOI DUNG BAN IN'), path).not.toBeNull()
      unmount()
      state = { user: { permissions: {} as PermissionMap } }
      const second = renderGuarded(path)
      expect(screen.queryByText('NOI DUNG BAN IN'), path).toBeNull()
      second.unmount()
    }
  })
})
