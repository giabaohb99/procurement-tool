import { describe, expect, it } from 'vitest'

import { isDispatched } from './purchase-request-detail'
import {
  isPrOptionStageOpen,
  MAX_OPTIONS_PER_LINE,
  PR_OPTION_STAGE_OPEN,
} from './purchase-request-options'

describe('isPrOptionStageOpen', () => {
  it('opens exactly the four working statuses after dispatch', () => {
    for (const status of ['dispatched', 'processing', 'purchasing', 'purchased']) {
      expect(isPrOptionStageOpen(status)).toBe(true)
    }
  })

  it('stays closed before dispatch — options must not be attachable on a draft', () => {
    for (const status of ['draft', 'submitted', 'approved', 'rejected']) {
      expect(isPrOptionStageOpen(status)).toBe(false)
    }
  })

  it('closes again when the request is finished or cancelled', () => {
    for (const status of ['completed', 'done', 'cancelled']) {
      expect(isPrOptionStageOpen(status)).toBe(false)
    }
  })

  it('treats garbage input as closed, never as writable', () => {
    expect(isPrOptionStageOpen('')).toBe(false)
    expect(isPrOptionStageOpen('DISPATCHED')).toBe(false)
    expect(isPrOptionStageOpen('unknown-status')).toBe(false)
  })

  /**
   * Màn xử lý mở theo isDispatched (để XEM cả phiếu đã đóng) nhưng chỉ GHI theo
   * stage-open — nếu stage-open lọt một trạng thái ngoài isDispatched thì nút
   * ghi hiện ra ở phiếu chưa điều phối, backend sẽ 400 hàng loạt.
   */
  it('every write-open status is also a dispatched status', () => {
    for (const status of PR_OPTION_STAGE_OPEN) {
      expect(isDispatched(status)).toBe(true)
    }
  })
})

describe('MAX_OPTIONS_PER_LINE', () => {
  it('matches the backend cap of 5 options per line', () => {
    expect(MAX_OPTIONS_PER_LINE).toBe(5)
  })
})
