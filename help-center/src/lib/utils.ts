import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

/** Gộp class Tailwind, class sau ghi đè class trước khi trùng nhóm tiện ích. */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
