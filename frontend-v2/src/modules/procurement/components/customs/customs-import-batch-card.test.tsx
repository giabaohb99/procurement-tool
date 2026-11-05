import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import {
  CUSTOMS_BATCH_MODE,
  CUSTOMS_BATCH_STATUS,
  type CustomsImportBatch,
} from '../../types/customs'
import { CustomsImportBatchCard } from './customs-import-batch-card'

function batch(overrides: Partial<CustomsImportBatch> = {}): CustomsImportBatch {
  return {
    id: 41,
    mode: CUSTOMS_BATCH_MODE.apply,
    status: CUSTOMS_BATCH_STATUS.done,
    filename: 'GTT02_ATRAZINE_2026_01_den_2026_06_ban_xuat_lan_cuoi.xlsx',
    file_size: 1024,
    has_file: true,
    total_rows: 120,
    created_count: 100,
    updated_count: 5,
    deleted_count: 2,
    skipped_count: 0,
    warning_count: 3,
    error_count: 0,
    error_summary: null,
    date_from: '2026-01-01',
    date_to: '2026-06-30',
    date_fixed: 4,
    duplicate_rows: 6,
    existing_rows: 7,
    created_at: '2026-07-01T08:00:00',
    created_by: 1,
    created_by_name: 'Nguyễn Thu Mi',
    started_at: null,
    finished_at: '2026-07-01T08:05:00',
    ...overrides,
  }
}

/** Số đứng cạnh nhãn trong lưới NHÃN – SỐ. */
function statValue(label: string): string {
  const term = screen.getByText(label, { selector: 'dt' })
  return term.parentElement ? within(term.parentElement).getByRole('definition').textContent ?? '' : ''
}

describe('CustomsImportBatchCard', () => {
  it('history card: file name, batch number, mode, uploader, time and the history counts', () => {
    render(<CustomsImportBatchCard batch={batch()} context="history" />)

    expect(
      screen.getByText('GTT02_ATRAZINE_2026_01_den_2026_06_ban_xuat_lan_cuoi.xlsx'),
    ).toBeInTheDocument()
    expect(screen.getByText(/Lô #41 · Ghi thật · Nguyễn Thu Mi · 01\/07\/2026/)).toBeInTheDocument()
    expect(screen.getByText('01/01/2026 → 30/06/2026')).toBeInTheDocument()
    expect(statValue('Thêm mới')).toBe('100')
    expect(statValue('Ghi đè')).toBe('5')
    expect(statValue('Xóa')).toBe('2')
    //  Bỏ qua = đã có + trùng trong tệp, đúng như cột của bảng Lịch sử nạp.
    expect(statValue('Bỏ qua (trùng)')).toBe('13')
    expect(statValue('Vá ngày')).toBe('4')
  })

  it('dry-run card uses the dry-run column labels and splits the skipped rows', () => {
    render(<CustomsImportBatchCard batch={batch({ mode: CUSTOMS_BATCH_MODE.dryRun })} context="dryRun" />)

    expect(statValue('Dòng mới')).toBe('100')
    expect(statValue('Đã có')).toBe('7')
    expect(statValue('Trùng trong tệp')).toBe('6')
    expect(statValue('Cảnh báo')).toBe('3')
    expect(screen.queryByText(/Lô #41/)).toBeNull()
  })

  it('apply card switches to past-tense labels like the table header does', () => {
    render(<CustomsImportBatchCard batch={batch()} context="apply" />)

    expect(statValue('Đã thêm')).toBe('100')
    expect(statValue('Đã ghi đè')).toBe('5')
    expect(statValue('Đã xóa')).toBe('2')
  })

  it('a batch still running shows dashes, not zeros that read as "nothing new"', () => {
    render(
      <CustomsImportBatchCard
        batch={batch({ status: CUSTOMS_BATCH_STATUS.running, created_count: 0 })}
        context="dryRun"
      />,
    )

    expect(statValue('Dòng mới')).toBe('—')
    expect(statValue('Đã có')).toBe('—')
  })

  it('old batches without the newer count fields read as 0, never "undefined" or NaN', () => {
    const { container } = render(
      <CustomsImportBatchCard
        batch={batch({ updated_count: undefined, existing_rows: undefined, duplicate_rows: undefined })}
        context="history"
      />,
    )

    expect(container.textContent).not.toMatch(/undefined|NaN/)
    expect(statValue('Bỏ qua (trùng)')).toBe('0')
  })

  it('a batch without dates shows a dash for the range', () => {
    render(<CustomsImportBatchCard batch={batch({ date_from: '', date_to: '' })} context="history" />)

    expect(screen.getByText('—', { selector: 'span' })).toBeInTheDocument()
  })

  it('renders the actions passed in, and none otherwise', () => {
    const { rerender } = render(
      <CustomsImportBatchCard
        batch={batch()}
        context="history"
        actions={<button type="button">Nhật ký lô</button>}
      />,
    )
    expect(screen.getByRole('button', { name: 'Nhật ký lô' })).toBeInTheDocument()

    rerender(<CustomsImportBatchCard batch={batch()} context="history" />)
    expect(screen.queryByRole('button')).toBeNull()
  })
})
