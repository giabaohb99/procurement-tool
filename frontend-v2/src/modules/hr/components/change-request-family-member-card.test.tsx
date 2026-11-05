import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { ChangeRequestFamilyRow } from '../types/employee-change-request'
import { ChangeRequestFamilyMemberCard } from './change-request-family-member-card'

function member(overrides: Partial<ChangeRequestFamilyRow> = {}): ChangeRequestFamilyRow {
  return {
    full_name: 'Trần Thị Mẹ',
    relation: 3,
    gender: 2,
    date_of_birth: '1965-04-02',
    phone: '',
    id_number: '046165000001',
    ...overrides,
  }
}

/** Giá trị đứng ngay sau nhãn trong khối `<dl>` của thẻ. */
function valueOf(label: string): string {
  return screen.getByText(label).nextElementSibling?.textContent ?? ''
}

describe('ChangeRequestFamilyMemberCard', () => {
  it('bày STT, họ tên và đủ bốn trường còn lại của bảng, đã dịch mã ra chữ', () => {
    render(<ChangeRequestFamilyMemberCard member={member()} index={1} />)

    expect(screen.getByText('2.')).toBeInTheDocument()
    expect(screen.getByText('Trần Thị Mẹ')).toBeInTheDocument()
    expect(valueOf('Quan hệ với chủ hộ')).toBe('Mẹ')
    expect(valueOf('Giới tính')).toBe('Nữ')
    expect(valueOf('Ngày sinh')).toBe('02/04/1965')
    expect(valueOf('Số CCCD')).toBe('046165000001')
  })

  //  Ở màn so sánh, "khối cũ trống CCCD, khối mới có" chính là thay đổi — bỏ dòng thì người duyệt
  //  không thấy khác ở đâu. Mã 0 (chưa khai) và null cũng phải ra gạch, không ra "0" hay "null".
  it('ô chưa khai vẫn giữ dòng, in "—" thay vì bỏ trống hay in mã thô', () => {
    render(
      <ChangeRequestFamilyMemberCard
        member={member({ relation: 0, gender: 0, date_of_birth: null, id_number: '' })}
        index={0}
      />,
    )
    expect(valueOf('Quan hệ với chủ hộ')).toBe('—')
    expect(valueOf('Giới tính')).toBe('—')
    expect(valueOf('Ngày sinh')).toBe('—')
    expect(valueOf('Số CCCD')).toBe('—')
  })

  it('chưa khai họ tên thì nói rõ, không để dòng đầu trống', () => {
    render(<ChangeRequestFamilyMemberCard member={member({ full_name: '' })} index={0} />)
    expect(screen.getByText('(chưa khai tên)')).toBeInTheDocument()
  })
})
