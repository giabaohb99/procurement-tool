import { z } from 'zod'

/**
 * Số điện thoại KHÁC của hồ sơ nhân sự (duoc-CR-694) — dùng chung cho form hồ sơ và form tự sửa liên hệ.
 *
 * `phone` vẫn là SỐ CHÍNH; các số còn lại nằm ở `extra_phones` (tối đa 4 → tổng 5 số). Luật phải khớp
 * `backend/app/modules/employee/phone_rules.py`: chỉ chữ số, khoảng trắng và `+ . - ( )`; 8–15 chữ số;
 * không trùng nhau (so sau khi bỏ ký tự phân cách) và không trùng số chính; số ≤ 20 ký tự, nhãn ≤ 50.
 */
export const MAX_EXTRA_PHONES = 4
export const MIN_PHONE_DIGITS = 8
export const MAX_PHONE_DIGITS = 15

/** Gợi ý nhãn — người dùng vẫn gõ tự do được. */
export const PHONE_LABEL_SUGGESTIONS = ['Cá nhân', 'Công việc', 'Zalo', 'Nhà riêng', 'Khác'] as const

export interface ExtraPhone {
  number: string
  label: string
}

const PHONE_CHARS = /^[0-9\s+.\-()]+$/

/** Chỉ giữ chữ số — để so trùng («0901 234 567» = «0901.234.567»). */
export function digitsOf(value: string): string {
  return value.replace(/\D/g, '')
}

/** Câu lỗi của MỘT số (rỗng = hợp lệ). Số trống không bị coi là lỗi: dòng trống bị bỏ khi gửi. */
export function phoneNumberError(value: string): string | null {
  const v = value.trim()
  if (!v) return null
  if (v.length > 20) return 'Số điện thoại tối đa 20 ký tự'
  if (!PHONE_CHARS.test(v)) return 'Chỉ gồm chữ số, khoảng trắng và các ký tự + . - ( )'
  const n = digitsOf(v).length
  if (n < MIN_PHONE_DIGITS || n > MAX_PHONE_DIGITS) {
    return `Số điện thoại phải có từ ${MIN_PHONE_DIGITS} đến ${MAX_PHONE_DIGITS} chữ số`
  }
  return null
}

export const extraPhoneSchema = z.object({
  number: z.string().superRefine((v, ctx) => {
    const message = phoneNumberError(v)
    if (message) ctx.addIssue({ code: 'custom', message })
  }),
  label: z.string().trim().max(50, 'Nhãn tối đa 50 ký tự'),
})

export const extraPhonesSchema = z
  .array(extraPhoneSchema)
  .max(MAX_EXTRA_PHONES, `Chỉ nhập tối đa ${MAX_EXTRA_PHONES} số điện thoại khác`)

/** Bỏ dòng trống số, cắt khoảng trắng — dạng gửi lên API. */
export function cleanExtraPhones(list: readonly ExtraPhone[] | undefined | null): ExtraPhone[] {
  return (list ?? [])
    .map((p) => ({ number: p.number.trim(), label: p.label.trim() }))
    .filter((p) => p.number !== '')
}

export function sameExtraPhones(
  a: readonly ExtraPhone[] | undefined | null,
  b: readonly ExtraPhone[] | undefined | null,
): boolean {
  const x = cleanExtraPhones(a)
  const y = cleanExtraPhones(b)
  return x.length === y.length && x.every((p, i) => p.number === y[i].number && p.label === y[i].label)
}

/**
 * Chỉ số các dòng bị TRÙNG (với dòng đứng trước hoặc với số chính). Dùng cho cả báo lỗi từng dòng
 * trong ô nhập lẫn kiểm tra cuối trước khi gửi.
 */
export function duplicatePhoneIndexes(main: string, extras: readonly ExtraPhone[]): Set<number> {
  const seen = new Set<string>()
  const mainDigits = digitsOf(main)
  if (mainDigits) seen.add(mainDigits)
  const dup = new Set<number>()
  extras.forEach((p, i) => {
    const d = digitsOf(p.number)
    if (!d) return
    if (seen.has(d)) dup.add(i)
    else seen.add(d)
  })
  return dup
}

/** Câu lỗi cấp form: số phụ trùng nhau / trùng số chính. `null` = ổn. */
export function extraPhonesFormError(main: string, extras: readonly ExtraPhone[]): string | null {
  return duplicatePhoneIndexes(main, extras).size > 0
    ? 'Có số điện thoại bị nhập trùng (kể cả trùng số chính)'
    : null
}

/**
 * «Đặt làm chính»: hoán đổi số chính với số phụ thứ `index` — CẢ số lẫn nhãn, nên không nhãn nào bị mất.
 */
export function swapWithMain(
  main: ExtraPhone,
  extras: readonly ExtraPhone[],
  index: number,
): { main: ExtraPhone; extras: ExtraPhone[] } {
  const target = extras[index]
  if (!target) return { main, extras: [...extras] }
  return {
    main: { number: target.number, label: target.label },
    extras: extras.map((p, i) => (i === index ? { number: main.number, label: main.label } : p)),
  }
}
