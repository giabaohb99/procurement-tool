import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import {
  renderFormulationCard,
  renderKindKeywordCard,
  renderRegulationCard,
  renderSynonymCard,
} from './customs-config-record-cards'

describe('customs config record cards', () => {
  it('keyword card: keyword, note, label chip and active chip', () => {
    render(renderKindKeywordCard({ id: 1, keyword: 'TECH', kind: 2, note: 'Nguyên liệu kỹ thuật', is_active: true }))

    expect(screen.getByText('TECH')).toBeInTheDocument()
    expect(screen.getByText('Nguyên liệu kỹ thuật')).toBeInTheDocument()
    expect(screen.getByText('Nguyên liệu')).toBeInTheDocument()
    expect(screen.getByText('Đang dùng')).toBeInTheDocument()
  })

  it('keyword card with an untagged kind shows no empty label chip', () => {
    const { container } = render(
      renderKindKeywordCard({ id: 2, keyword: 'X', kind: 0, note: '', is_active: false }),
    )

    //  Chỉ còn tên + chip trạng thái — chip nhãn rỗng sẽ là một ô xám không chữ chen giữa.
    expect(container.textContent).toBe('XNgừng dùng')
  })

  it('synonym card joins the ";" list and drops empty pieces', () => {
    render(renderSynonymCard({ id: 3, term: 'glyphosate', synonyms: 'glyfosat; ;glifosat;', note: '', is_active: true }))

    expect(screen.getByText('glyphosate')).toBeInTheDocument()
    expect(screen.getByText('glyfosat · glifosat')).toBeInTheDocument()
  })

  it('formulation card: code with Vietnamese name, falls back to English', () => {
    const { rerender } = render(
      renderFormulationCard({ id: 4, code: 'EC', name_en: 'Emulsifiable concentrate', name_vi: 'Nhũ dầu', description: 'Dạng lỏng', is_active: true }),
    )
    expect(screen.getByText('EC — Nhũ dầu')).toBeInTheDocument()

    rerender(
      renderFormulationCard({ id: 4, code: 'EC', name_en: 'Emulsifiable concentrate', name_vi: '', description: '', is_active: true }),
    )
    expect(screen.getByText('EC — Emulsifiable concentrate')).toBeInTheDocument()
  })

  it('regulation card reuses the config chips (list, CAS, status)', () => {
    render(
      renderRegulationCard({
        id: 5,
        list_code: 10,
        seq_no: '1',
        sort_order: 1,
        name: 'Paraquat dichloride',
        name_vi: 'Paraquat',
        cas_no: '1910-42-5',
        formula: 'C12H14Cl2N2',
        category: '',
        threshold_kg: null,
        mixture_pct: null,
        banned_year: 2026,
        legal_basis: '',
        note: '',
        is_active: true,
      }),
    )

    expect(screen.getByText('Paraquat')).toBeInTheDocument()
    expect(screen.getByText('Paraquat dichloride · C12H14Cl2N2')).toBeInTheDocument()
    expect(screen.getByText('CAS 1910-42-5')).toBeInTheDocument()
    expect(screen.getByText('Đang dùng')).toBeInTheDocument()
  })
})
