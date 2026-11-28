import { describe, expect, it } from 'vitest'

import { ACTIONS, type PermissionAction } from '@/core/authorization/permission-types'
import {
  buildPrReturnLockNotice,
  isInvoiceCompanyOnly,
  isOrderLockedByPrReturn,
  isPoActionOpenWhilePrReturned,
  validateInvoiceCompanyOnly,
} from './invoice-company-return-lock'

/**
 * duoc-CR-803 — YCMH Đang mua hàng trả về chỉ để sửa Công ty nhận hóa đơn. Bốn luật nhỏ này quyết
 * định cả hai màn (YCMH chỉ mở ô công ty, ĐMH chỉ còn xem + in), sai một chữ là người dùng bấm
 * vào một loạt nút ăn lỗi 400 của backend.
 */

describe('isInvoiceCompanyOnly', () => {
  it('is on only when the backend says so explicitly', () => {
    expect(isInvoiceCompanyOnly({ invoice_company_only: true })).toBe(true)
    expect(isInvoiceCompanyOnly({ invoice_company_only: false })).toBe(false)
  })

  it('treats an older backend that does not send the key as off, never as on', () => {
    expect(isInvoiceCompanyOnly({})).toBe(false)
    expect(isInvoiceCompanyOnly(null)).toBe(false)
    expect(isInvoiceCompanyOnly(undefined)).toBe(false)
  })
})

describe('validateInvoiceCompanyOnly', () => {
  it('asks for the invoice company and nothing else', () => {
    expect(validateInvoiceCompanyOnly({ company_id: 0 })).toBe('Vui lòng chọn Công ty nhận hóa đơn')
    expect(validateInvoiceCompanyOnly({})).toBe('Vui lòng chọn Công ty nhận hóa đơn')
  })

  it('lets the request through once a company is picked, even if other required fields are empty', () => {
    //  Phiếu cũ thiếu mục đích / dòng hàng vẫn phải gửi duyệt lại được: backend bỏ qua các ô đó.
    expect(validateInvoiceCompanyOnly({ company_id: 5 })).toBeNull()
  })
})

describe('isOrderLockedByPrReturn', () => {
  it('reads only an explicit true', () => {
    expect(isOrderLockedByPrReturn({ locked_by_pr_return: true })).toBe(true)
    expect(isOrderLockedByPrReturn({ locked_by_pr_return: false })).toBe(false)
    expect(isOrderLockedByPrReturn({})).toBe(false)
    expect(isOrderLockedByPrReturn(null)).toBe(false)
    expect(isOrderLockedByPrReturn(undefined)).toBe(false)
  })
})

describe('isPoActionOpenWhilePrReturned', () => {
  const stillOpen: PermissionAction[] = ['read', 'print', 'export']

  it('leaves every action open when the order is not locked', () => {
    for (const action of ACTIONS) expect(isPoActionOpenWhilePrReturned(action, false)).toBe(true)
  })

  it('keeps only read, print and export while the source request is returned', () => {
    for (const action of ACTIONS) {
      expect(isPoActionOpenWhilePrReturned(action, true)).toBe(stillOpen.includes(action))
    }
  })

  it('closes every write action the backend blocks', () => {
    for (const action of ['create', 'write', 'delete', 'approve', 'cancel'] as PermissionAction[]) {
      expect(isPoActionOpenWhilePrReturned(action, true)).toBe(false)
    }
  })
})

describe('buildPrReturnLockNotice', () => {
  it('names the source request', () => {
    expect(buildPrReturnLockNotice('PYC09112601')).toBe(
      'Đơn đang tạm khóa: yêu cầu mua hàng PYC09112601 được trả về để sửa công ty nhận hóa đơn, chờ duyệt lại.',
    )
  })

  it('still reads as a sentence when the code is blank or padded', () => {
    expect(buildPrReturnLockNotice('  ')).toContain('yêu cầu mua hàng nguồn được trả về')
    expect(buildPrReturnLockNotice(' PYC1 ')).toContain('yêu cầu mua hàng PYC1 được')
  })
})
