import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { EmployeeImportButton } from './employee-import-button'

type Grants = Partial<Record<string, Partial<Record<string, boolean>>>>
let grants: Grants = {}

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: (entity: string, action: string) => !!grants[entity]?.[action],
    canAccess: () => true,
  }),
}))

//  Hộp thoại thật cần TanStack Query + API tải tệp; ở đây chỉ kiểm cách NÚT dùng nó.
vi.mock('@/modules/system/components/import-upload-dialog', () => ({
  ImportUploadDialog: (props: {
    open: boolean
    lockedModule?: number
    onCreated?: (id: number) => void
  }) =>
    props.open ? (
      <div data-testid="dialog" data-locked={props.lockedModule}>
        <button onClick={() => props.onCreated?.(42)}>tao-lo</button>
      </div>
    ) : null,
}))

function build() {
  return render(
    <MemoryRouter initialEntries={['/hr/employees']}>
      <Routes>
        <Route path="/hr/employees" element={<EmployeeImportButton />} />
        <Route path="/system/imports/:id" element={<div>chi-tiet-lo</div>} />
      </Routes>
    </MemoryRouter>,
  )
}

const full: Grants = {
  import: { create: true, read: true },
  employee: { create: true, write: true },
}

beforeEach(() => {
  grants = {}
})

describe('EmployeeImportButton', () => {
  it('đủ quyền → hiện nút', () => {
    grants = full
    build()
    expect(screen.getByRole('button', { name: /Nhập Excel/ })).toBeTruthy()
  })

  it('thiếu import.create → ẩn', () => {
    grants = { ...full, import: { read: true } }
    build()
    expect(screen.queryByRole('button', { name: /Nhập Excel/ })).toBeNull()
  })

  it('thiếu import.read → ẩn (trang chi tiết lô sẽ 403)', () => {
    grants = { ...full, import: { create: true } }
    build()
    expect(screen.queryByRole('button', { name: /Nhập Excel/ })).toBeNull()
  })

  it('chỉ employee.write (không create) → vẫn hiện', () => {
    grants = { ...full, employee: { write: true } }
    build()
    expect(screen.getByRole('button', { name: /Nhập Excel/ })).toBeTruthy()
  })

  it('thiếu cả employee.create và employee.write → ẩn', () => {
    grants = { ...full, employee: { read: true } }
    build()
    expect(screen.queryByRole('button', { name: /Nhập Excel/ })).toBeNull()
  })

  it('bấm → mở hộp thoại khóa đối tượng Nhân sự (12); tạo lô → sang /system/imports/42', () => {
    grants = full
    build()
    expect(screen.queryByTestId('dialog')).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: /Nhập Excel/ }))
    expect(screen.getByTestId('dialog').getAttribute('data-locked')).toBe('12')
    fireEvent.click(screen.getByText('tao-lo'))
    expect(screen.getByText('chi-tiet-lo')).toBeTruthy()
  })
})
