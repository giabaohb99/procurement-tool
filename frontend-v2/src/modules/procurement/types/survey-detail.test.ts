import { describe, expect, it } from 'vitest'

import { isSurveyDeletable, isSurveyReturnable } from './survey-detail'

// bao-CR-554 — «Trả về» phiếu khảo sát mở cả khi ĐÃ DUYỆT (hủy duyệt để sửa lại); Duyệt / Từ chối
// vẫn chỉ khi chờ duyệt. Backend `POST /{id}/reject` nhận đúng hai trạng thái này.
describe('isSurveyReturnable', () => {
  it('allows returning a submitted or an already approved survey', () => {
    expect(isSurveyReturnable('submitted')).toBe(true)
    expect(isSurveyReturnable('approved')).toBe(true)
  })

  it('refuses drafts, rejected, cancelled and unknown states', () => {
    for (const status of ['draft', 'rejected', 'cancelled', '', 'done', 'APPROVED']) {
      expect(isSurveyReturnable(status)).toBe(false)
    }
  })

  it('returnable and deletable never overlap — a ticket is either in flight or editable', () => {
    for (const status of ['draft', 'submitted', 'approved', 'rejected', 'cancelled']) {
      expect(isSurveyReturnable(status) && isSurveyDeletable(status)).toBe(false)
    }
  })
})
