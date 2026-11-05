import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import {
  CUSTOMS_BATCH_MODE,
  CUSTOMS_BATCH_STATUS,
  type CustomsImportBatch,
} from '../../types/customs'
import { CustomsBatchHistoryActions } from './customs-batch-history-actions'

vi.mock('../../api/customs-api', () => ({ downloadCustomsBatchFile: vi.fn(() => Promise.resolve()) }))

function batch(overrides: Partial<CustomsImportBatch> = {}): CustomsImportBatch {
  return {
    id: 9,
    mode: CUSTOMS_BATCH_MODE.apply,
    status: CUSTOMS_BATCH_STATUS.done,
    filename: 'a.xlsx',
    file_size: 1,
    has_file: true,
    total_rows: 1,
    created_count: 1,
    deleted_count: 0,
    skipped_count: 0,
    warning_count: 0,
    error_count: 0,
    error_summary: null,
    date_from: '',
    date_to: '',
    date_fixed: 0,
    created_at: null,
    created_by: null,
    created_by_name: null,
    started_at: null,
    finished_at: null,
    ...overrides,
  }
}

function mount(props: Partial<Parameters<typeof CustomsBatchHistoryActions>[0]> = {}) {
  const handlers = { onOpenLogs: vi.fn(), onRevert: vi.fn() }
  render(
    <CustomsBatchHistoryActions
      batch={batch()}
      canRevert
      revertPending={false}
      {...handlers}
      {...props}
    />,
  )
  return handlers
}

describe('CustomsBatchHistoryActions', () => {
  it('opens the batch log and asks to revert with the clicked batch', async () => {
    const { onOpenLogs, onRevert } = mount()

    await userEvent.click(screen.getByRole('button', { name: /Nhật ký lô/ }))
    await userEvent.click(screen.getByRole('button', { name: 'Hoàn tác lô nạp' }))
    expect(onOpenLogs).toHaveBeenCalledWith(expect.objectContaining({ id: 9 }))
    expect(onRevert).toHaveBeenCalledWith(expect.objectContaining({ id: 9 }))
  })

  it('locks revert for an old batch that replaced rows without a snapshot', () => {
    mount({ batch: batch({ deleted_count: 3, legacy_replace: true }) })

    expect(screen.getByRole('button', { name: 'Hoàn tác lô nạp' })).toBeDisabled()
  })

  it('locks every revert while one revert is running — no second request from a double tap', () => {
    mount({ revertPending: true })

    expect(screen.getByRole('button', { name: 'Hoàn tác lô nạp' })).toBeDisabled()
  })

  it('hides revert for a dry run and hides download when the batch kept no file', () => {
    mount({ batch: batch({ mode: CUSTOMS_BATCH_MODE.dryRun, has_file: false }) })
    expect(screen.queryByRole('button', { name: 'Hoàn tác lô nạp' })).toBeNull()
    expect(screen.queryByRole('button', { name: /Tải lại tệp gốc/ })).toBeNull()
  })

  it('without the revert right the button is gone even on a revertable batch', () => {
    mount({ canRevert: false })

    expect(screen.queryByRole('button', { name: 'Hoàn tác lô nạp' })).toBeNull()
    expect(screen.getByRole('button', { name: /Tải lại tệp gốc/ })).toBeInTheDocument()
  })
})
