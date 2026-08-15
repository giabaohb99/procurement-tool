import { useCallback } from 'react'

import { vi, type TranslationKey } from './vi'

/**
 * `t('auth.login')` — có gợi ý key và báo lỗi biên dịch nếu gõ sai.
 * Chỉ một ngôn ngữ nên chưa cần context/provider; thêm ngôn ngữ thì đổi ruột file này.
 */
export function useTranslation() {
  const t = useCallback((key: TranslationKey) => vi[key], [])
  return { t }
}

/** Bản dùng ngoài component (service, util). */
export const t = (key: TranslationKey) => vi[key]
