import { render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type { SettingField } from '../types/setting'

import { SettingFieldRow } from './setting-field-row'

/**
 * bao-CR-529 — ô «Phòng thu mua mặc định» CHỌN từ danh mục Phòng ban, không gõ mã.
 *
 * Đại ca: «sao chỗ này để mã PBA017, sao không cho chọn từ danh sách phòng ban».
 * Giá trị vẫn là MÃ phòng — backend lưu mã từ bao-CR-524.
 */

let canRead = true
const departmentsQuery = vi.fn()

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => canRead }),
}))

vi.mock('@/modules/hr/hooks/use-departments', () => ({
  useDepartments: (_params: unknown, options: { enabled?: boolean }) => {
    departmentsQuery(options)
    return {
      data: {
        items: [
          { id: 20, code: 'PBA017', name: 'Sản xuất -Thu mua', is_active: true },
          { id: 5, code: 'NM01', name: 'Nhà máy Dego Organic', is_active: true },
        ],
      },
    }
  },
}))

const field = (value: string): SettingField => ({
  key: 'central_purchasing_dept_code',
  group: 'workflow',
  label: 'Phòng thu mua mặc định',
  type: 'department',
  value,
  hint: 'Để trống = PBA017 «Sản xuất -Thu mua».',
})

describe('SettingFieldRow — ô chọn phòng ban (bao-CR-529)', () => {
  beforeEach(() => {
    canRead = true
    departmentsQuery.mockClear()
  })

  it('hiện TÊN phòng đang chọn thay vì mã trần', () => {
    render(<SettingFieldRow field={field('PBA017')} disabled={false} onChange={vi.fn()} />)
    expect(screen.getByText('Sản xuất -Thu mua · PBA017')).toBeInTheDocument()
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
  })

  it('mã đang lưu không có trong danh mục vẫn hiện nguyên văn, không giả làm ô trống', () => {
    render(<SettingFieldRow field={field('MACU')} disabled={false} onChange={vi.fn()} />)
    expect(screen.getByText('MACU')).toBeInTheDocument()
  })

  it('thiếu quyền đọc Phòng ban thì rơi về ô chữ và KHÔNG gọi danh mục', () => {
    canRead = false
    render(<SettingFieldRow field={field('PBA017')} disabled={false} onChange={vi.fn()} />)
    expect(screen.getByRole('textbox')).toHaveValue('PBA017')
    expect(departmentsQuery).toHaveBeenCalledWith({ enabled: false })
  })
})
