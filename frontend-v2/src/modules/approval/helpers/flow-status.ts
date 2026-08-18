import type { ApprovalFlow } from '../types/approval'

export type FlowStatusTone = 'running' | 'waiting' | 'off'

export interface FlowStatus {
  label: string
  /** Câu giải thích, hiện khi rê chuột lên huy hiệu. */
  hint: string
  tone: FlowStatusTone
}

/**
 * Trạng thái THẬT của một luồng duyệt = cờ `is_active` của luồng **và** công
 * tắc bộ máy duyệt mới của loại chứng từ đó.
 *
 * Hai thứ này độc lập nhau ở backend, nên sinh ra một trạng thái rất dễ hiểu
 * nhầm: luồng bật nhưng công tắc của loại đang tắt — phiếu vẫn đi đường duyệt
 * cũ và luồng nằm im. Bảng cũ chỉ đọc `is_active` nên dán nhãn "Đang dùng" cho
 * đúng cái luồng chưa chạy phút nào, người khai luồng ngồi chờ mãi không thấy
 * phiếu vào.
 */
export function flowStatus(
  flow: Pick<ApprovalFlow, 'is_active'>,
  engineOn: boolean,
): FlowStatus {
  if (!flow.is_active) {
    return {
      label: 'Ngừng',
      hint: 'Luồng đã tắt. Phiếu mới không đi theo luồng này.',
      tone: 'off',
    }
  }

  if (!engineOn) {
    return {
      label: 'Chờ bật bộ máy',
      hint:
        'Luồng đã bật nhưng bộ máy duyệt mới của loại chứng từ này đang TẮT, ' +
        'nên phiếu vẫn đi đường duyệt cũ. Bật ở màn «Bật bộ máy duyệt».',
      tone: 'waiting',
    }
  }

  return {
    label: 'Đang chạy',
    hint: 'Phiếu tạo từ giờ đi theo luồng này.',
    tone: 'running',
  }
}
