import { describe, expect, it } from 'vitest'

import { LEGACY_SURVEY_DRAFT_KEY, getSurveyDraftKey, restoreSurveyDraft } from './survey-new-draft'

// bao-CR-571 — lỗi có thật 02/10/2026: tài khoản Quyên mở «Tạo phiếu khảo sát» thấy nháp
// ngày 28/09 của chị Phương, ô NSPT (khóa) mang tên chị Phương. Khóa nháp từng dùng chung.

function memoryStorage(seed: Record<string, string> = {}) {
  const data = new Map(Object.entries(seed))
  return {
    data,
    getItem: (key: string) => data.get(key) ?? null,
    removeItem: (key: string) => {
      data.delete(key)
    },
  }
}

const QUYEN = { id: 22, full_name: 'Trần Nguyễn Phương Quyên' }
const PHUONG_DRAFT = JSON.stringify({ main_content: 'NCC vận chuyển', nspt: 'Trần Diễm Phương', created_by: 12 })

describe('restoreSurveyDraft', () => {
  it('never loads the shared legacy draft of another account and deletes it', () => {
    const storage = memoryStorage({ [LEGACY_SURVEY_DRAFT_KEY]: PHUONG_DRAFT })
    expect(restoreSurveyDraft(storage, QUYEN)).toBeNull()
    expect(storage.data.has(LEGACY_SURVEY_DRAFT_KEY)).toBe(false)
  })

  it('loads only the draft stored under the current account', () => {
    const storage = memoryStorage({
      [getSurveyDraftKey(12)]: PHUONG_DRAFT,
      [getSurveyDraftKey(22)]: JSON.stringify({ main_content: 'Bao bì', nspt: 'Trần Nguyễn Phương Quyên', created_by: 22 }),
    })
    expect(restoreSurveyDraft<{ main_content: string; nspt: string; created_by: number }>(storage, QUYEN))
      .toMatchObject({ main_content: 'Bao bì' })
  })

  it('always overwrites NSPT and creator with the logged-in account, even for a tampered draft', () => {
    const storage = memoryStorage({ [getSurveyDraftKey(22)]: PHUONG_DRAFT })
    expect(restoreSurveyDraft(storage, QUYEN)).toMatchObject({
      nspt: 'Trần Nguyễn Phương Quyên',
      created_by: 22,
    })
  })

  it('returns null for missing user, missing draft, broken JSON and non-object payloads', () => {
    expect(restoreSurveyDraft(memoryStorage({ [getSurveyDraftKey(0)]: PHUONG_DRAFT }), null)).toBeNull()
    expect(restoreSurveyDraft(memoryStorage(), QUYEN)).toBeNull()
    for (const raw of ['{khong-phai-json', 'null', '[]', '"chuoi"', '42']) {
      expect(restoreSurveyDraft(memoryStorage({ [getSurveyDraftKey(22)]: raw }), QUYEN)).toBeNull()
    }
  })

  it('keys differ per account and never fall back to the legacy key', () => {
    expect(getSurveyDraftKey(22)).not.toBe(getSurveyDraftKey(12))
    expect(getSurveyDraftKey(22)).not.toBe(LEGACY_SURVEY_DRAFT_KEY)
    expect(getSurveyDraftKey(undefined)).toBe(`${LEGACY_SURVEY_DRAFT_KEY}:0`)
  })
})
