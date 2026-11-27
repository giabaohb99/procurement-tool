import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import {
  PACKAGING_BOM_IMPORT,
  PACKAGING_MISA_IMPORT,
  PACKAGING_QUOTE_IMPORT,
} from '../config/packaging-excel-imports'
import { PackagingExcelImportButton } from './packaging-excel-import-button'

let granted: string[] = []
const downloadFile = vi.fn()

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: (entity: string, action: string) => granted.includes(`${entity}:${action}`) }),
}))
vi.mock('@/core/api/download-file', () => ({
  downloadFile: (...args: unknown[]) => downloadFile(...args),
}))
vi.mock('@/modules/system/hooks/use-imports', () => ({
  useUploadImport: () => ({ mutateAsync: vi.fn(), isPending: false }),
}))

const IMPORT_RIGHTS = ['import:create', 'import:read']

function renderButton(kind = PACKAGING_QUOTE_IMPORT) {
  return render(
    <MemoryRouter>
      <PackagingExcelImportButton kind={kind} />
    </MemoryRouter>,
  )
}

describe('PackagingExcelImportButton', () => {
  beforeEach(() => {
    granted = []
    downloadFile.mockReset()
    downloadFile.mockResolvedValue(undefined)
  })

  it('stays hidden without import rights even when the packaging right is there', () => {
    granted = ['packaging_price_list:create', 'packaging_price_list:write']
    renderButton()
    expect(screen.queryByRole('button', { name: 'Nhập báo giá' })).not.toBeInTheDocument()
  })

  it('needs packaging_history.write for the Misa book — create alone is not enough (it rewrites prices)', () => {
    granted = [...IMPORT_RIGHTS, 'packaging_history:create']
    const { unmount } = renderButton(PACKAGING_MISA_IMPORT)
    expect(screen.queryByRole('button', { name: 'Nạp sổ Misa' })).not.toBeInTheDocument()
    unmount()
    granted = [...IMPORT_RIGHTS, 'packaging_history:write']
    renderButton(PACKAGING_MISA_IMPORT)
    expect(screen.getByRole('button', { name: 'Nạp sổ Misa' })).toBeInTheDocument()
  })

  //  bao-CR-792 — mỗi loại nhập gác bằng khóa của MÀN chứa nút; quyền ở màn khác của cụm không mở được nút.
  it.each([
    { kind: PACKAGING_BOM_IMPORT, own: 'packaging_bom:create', label: 'Nhập từ Excel' },
    { kind: PACKAGING_QUOTE_IMPORT, own: 'packaging_price_list:create', label: 'Nhập báo giá' },
    { kind: PACKAGING_MISA_IMPORT, own: 'packaging_history:write', label: 'Nạp sổ Misa' },
  ])('shows "$label" only with $own, never with the rights of another screen', ({ kind, own, label }) => {
    const everyRight = [
      'packaging_bom:create',
      'packaging_bom:write',
      'packaging_price_list:create',
      'packaging_price_list:write',
      'packaging_history:create',
      'packaging_history:write',
      'packaging_impact:read',
      //  Khóa chung cũ đã nghỉ: còn sót trong vai trò cũng không mở được nút nào.
      'packaging_cost:create',
      'packaging_cost:write',
    ]
    const ownEntity = own.split(':')[0]
    granted = [...IMPORT_RIGHTS, ...everyRight.filter((right) => !right.startsWith(`${ownEntity}:`))]
    const { unmount } = renderButton(kind)
    expect(screen.queryByRole('button', { name: label })).not.toBeInTheDocument()
    unmount()
    granted = [...IMPORT_RIGHTS, own]
    renderButton(kind)
    expect(screen.getByRole('button', { name: label })).toBeInTheDocument()
  })

  it('downloads the template of its own kind from the dialog, and Chạy thử waits for a file', () => {
    granted = [...IMPORT_RIGHTS, 'packaging_price_list:create']
    renderButton()
    fireEvent.click(screen.getByRole('button', { name: 'Nhập báo giá' }))
    expect(screen.getByRole('heading', { name: 'Nhập báo giá VTBB từ Excel' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Chạy thử' })).toBeDisabled()
    fireEvent.click(screen.getByRole('button', { name: 'Tải tệp mẫu' }))
    expect(downloadFile).toHaveBeenCalledWith('/api/imports/template', 'mau-nhap-bao-gia-vtbb.xlsx', {
      module: 5,
    })
  })
})
