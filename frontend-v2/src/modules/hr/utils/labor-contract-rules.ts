import { LABOR_CONTRACT_STATUS, labelOf } from '@/shared/constants/statuses'

/**
 * Luật thuần của HĐLĐ phía giao diện — chỉ để báo lỗi SỚM và ẩn/hiện ô. Backend
 * (`labor_contract/rules.py`) vẫn là chuẩn: sai lệch thì backend trả 400/422.
 * Danh sách NHÃN loại/trạng thái lấy từ `statuses.ts` (sinh từ backend), không gõ lại.
 */

/** Khớp `LaborContractType`. */
export const CONTRACT_TYPE_INDEFINITE = 3

/** Khớp `LaborContractStatus`. */
export const CONTRACT_STATUS = {
  DRAFT: 1,
  SIGNED: 2,
  EXPIRED: 3,
  TERMINATED: 4,
  CANCELLED: 5,
} as const

export type EndDateRule = 'required' | 'forbidden' | 'optional'

/** Khớp `REQUIRES_END_DATE` (1,2,4,5) / `FORBIDS_END_DATE` (3); loại 9 «Khác» tùy ý. */
export function endDateRule(contractType: number): EndDateRule {
  if (contractType === CONTRACT_TYPE_INDEFINITE) return 'forbidden'
  if ([1, 2, 4, 5].includes(contractType)) return 'required'
  return 'optional'
}

export function contractStatusLabel(status: number): string {
  return labelOf(LABOR_CONTRACT_STATUS, String(status)) || '—'
}

/** Mô tả hộp hỏi cho từng bước chuyển trạng thái (đích -> ô cần nhập). */
export interface TransitionSpec {
  toStatus: number
  /** Nhãn nút / tiêu đề hộp. */
  actionLabel: string
  dateLabel: string | null
  needsReason: boolean
  reasonLabel: string
  /** Bước không hoàn tác: hộp cảnh báo đỏ. */
  danger: boolean
}

const TRANSITION_SPECS: Record<number, TransitionSpec> = {
  [CONTRACT_STATUS.SIGNED]: {
    toStatus: CONTRACT_STATUS.SIGNED,
    actionLabel: 'Đánh dấu đã ký',
    dateLabel: 'Ngày ký',
    needsReason: false,
    reasonLabel: '',
    danger: false,
  },
  [CONTRACT_STATUS.CANCELLED]: {
    toStatus: CONTRACT_STATUS.CANCELLED,
    actionLabel: 'Hủy hợp đồng',
    dateLabel: null,
    needsReason: true,
    reasonLabel: 'Lý do hủy',
    danger: true,
  },
  [CONTRACT_STATUS.TERMINATED]: {
    toStatus: CONTRACT_STATUS.TERMINATED,
    actionLabel: 'Chấm dứt / thanh lý',
    dateLabel: 'Ngày chấm dứt',
    needsReason: true,
    reasonLabel: 'Lý do chấm dứt',
    danger: true,
  },
}

/** `undefined` khi mã đích lạ (backend thêm bước mới mà FE chưa biết) — nơi gọi bỏ qua. */
export function transitionSpecOf(toStatus: number): TransitionSpec | undefined {
  return TRANSITION_SPECS[toStatus]
}

/**
 * Kiểm đầu vào hộp chuyển trạng thái. Trả câu báo lỗi hoặc `null`.
 * `startDate` để chặn ngày chấm dứt trước ngày bắt đầu (backend cũng chặn).
 */
export function validateTransitionInput(
  spec: TransitionSpec,
  input: { date: string; reason: string },
  startDate: string,
): string | null {
  if (spec.dateLabel && !input.date) return `Chọn ${spec.dateLabel.toLowerCase()}`
  if (spec.toStatus === CONTRACT_STATUS.TERMINATED && input.date && input.date < startDate) {
    return 'Ngày chấm dứt không được trước ngày bắt đầu hợp đồng'
  }
  if (spec.needsReason && !input.reason.trim()) return `Nhập ${spec.reasonLabel.toLowerCase()}`
  if (input.reason.trim().length > 500) return 'Lý do tối đa 500 ký tự'
  return null
}

/** Bản ký: pdf/jpg/png <= 50MB — khớp backend (sniff byte đầu ở server). */
export const SIGNED_FILE_ACCEPT = '.pdf,.jpg,.jpeg,.png'
export const SIGNED_FILE_MAX_BYTES = 50 * 1024 * 1024

/** Trả câu lỗi hoặc `null`. Backend vẫn là chuẩn (kiểm cả nội dung thật của tệp). */
export function validateSignedFile(file: File): string | null {
  if (!/\.(pdf|jpe?g|png)$/i.test(file.name)) return 'Bản ký chỉ nhận PDF, JPG hoặc PNG'
  if (file.size <= 0) return 'Tệp rỗng'
  if (file.size > SIGNED_FILE_MAX_BYTES) return 'Bản ký lớn hơn 50 MB'
  return null
}
