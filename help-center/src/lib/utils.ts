import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

/** Gộp class Tailwind, class sau ghi đè class trước khi trùng nhóm tiện ích. */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/** Bỏ thẻ HTML của nội dung Quill, rút gọn thành trích đoạn hiển thị dưới tiêu đề bài viết. */
export function excerptFromHtml(html: string, maxLen = 150): string {
  const text = (html || '').replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim()
  if (!text) return ''
  return text.length > maxLen ? text.slice(0, maxLen) + '…' : text
}
