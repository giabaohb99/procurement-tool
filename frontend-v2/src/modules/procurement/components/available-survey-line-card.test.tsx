import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import {
  AvailableSurveyLineCard,
  type AvailableSurveyLineCardData,
} from './available-survey-line-card'

function line(overrides: Partial<AvailableSurveyLineCardData> = {}): AvailableSurveyLineCardData {
  return {
    supplier_code: 'NCC-A',
    supplier_name: 'CÔNG TY A',
    product_name: 'Chai PET 500ml',
    spec: 'Cổ 28mm',
    price_by_volume: 3_450.5,
    moq: 5_000,
    quote_unit: 'Chai',
    survey_item_group: 'Chai lọ',
    result_date: '2026-10-02',
    survey_code: 'KS-0042',
    ...overrides,
  }
}

describe('AvailableSurveyLineCard', () => {
  it('shows supplier, survey code, survey date, product and unit price', () => {
    render(
      <AvailableSurveyLineCard
        row={line()}
        lineItemGroup="Chai lọ"
        documentLabel="YCMH"
        attaching={false}
        onAttach={() => {}}
      />,
    )

    expect(screen.getByText('CÔNG TY A')).toBeInTheDocument()
    expect(screen.getByText('KS-0042')).toBeInTheDocument()
    expect(screen.getByText(/02\/10\/2026/)).toBeInTheDocument()
    expect(screen.getByText('Chai PET 500ml')).toBeInTheDocument()
    //  Đơn giá giữ số lẻ — làm tròn ở đây là so giá NCC sai đúng ở phần lẻ.
    expect(screen.getByText(/^3\.450,5 đ\/Chai$/)).toBeInTheDocument()
    expect(screen.queryByText('≠ phân loại')).toBeNull()
  })

  it('flags a survey whose item group differs from the line being processed', () => {
    render(
      <AvailableSurveyLineCard
        row={line({ survey_item_group: 'Nắp' })}
        lineItemGroup="Chai lọ"
        documentLabel="YCBG"
        attaching={false}
        onAttach={() => {}}
      />,
    )

    expect(screen.getByText('≠ phân loại')).toHaveAttribute('title', 'Khác phân loại của dòng YCBG')
  })

  it('does not flag a mismatch when the line has no item group to compare with', () => {
    render(
      <AvailableSurveyLineCard
        row={line({ survey_item_group: 'Nắp' })}
        lineItemGroup=""
        documentLabel="YCMH"
        attaching={false}
        onAttach={() => {}}
      />,
    )

    expect(screen.queryByText('≠ phân loại')).toBeNull()
  })

  it('attaches through a labelled button, and blocks it while a request is in flight', () => {
    const onAttach = vi.fn()
    const { rerender } = render(
      <AvailableSurveyLineCard
        row={line()}
        lineItemGroup="Chai lọ"
        documentLabel="YCMH"
        attaching={false}
        onAttach={onAttach}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: /Gắn/ }))
    expect(onAttach).toHaveBeenCalledTimes(1)

    rerender(
      <AvailableSurveyLineCard
        row={line()}
        lineItemGroup="Chai lọ"
        documentLabel="YCMH"
        attaching
        onAttach={onAttach}
      />,
    )
    expect(screen.getByRole('button', { name: /Gắn/ })).toBeDisabled()
  })

  it('missing supplier and price still render placeholders, not empty lines', () => {
    render(
      <AvailableSurveyLineCard
        row={line({ supplier_name: '', supplier_code: '', price_by_volume: 0, moq: 0 })}
        lineItemGroup=""
        documentLabel="YCMH"
        attaching={false}
        onAttach={() => {}}
      />,
    )

    expect(screen.getAllByText('—').length).toBeGreaterThan(0)
    expect(screen.getByText('Chưa có giá')).toBeInTheDocument()
    expect(screen.queryByText(/MOQ/)).toBeNull()
  })
})
