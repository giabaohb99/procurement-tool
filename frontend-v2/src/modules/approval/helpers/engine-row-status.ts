export type EngineRowTone = 'running' | 'idle' | 'off'

export interface EngineRowStatus {
  label: string
  hint: string
  tone: EngineRowTone
}

/**
 * Trạng thái thật của MỘT loại chứng từ trên màn bật bộ máy.
 *
 * Công tắc bật **chưa chắc** đã có gì chạy: `instance_service.bat_dau()` không
 * tìm được luồng nào của loại đó thì trả `None` và phiếu lặng lẽ đi tiếp đường
 * duyệt cũ. Người quản trị bật công tắc, thấy nút đã xanh, rồi ngồi chờ mãi
 * không thấy phiếu nào vào bộ máy mới — nên trạng thái này phải nói ra.
 */
export function engineRowStatus(soLuong: number, dangBat: boolean): EngineRowStatus {
  if (!dangBat) {
    return {
      label: 'Đường duyệt cũ',
      hint:
        soLuong > 0
          ? `Đã khai ${soLuong} luồng nhưng chưa bật — phiếu vẫn đi đường duyệt cũ.`
          : 'Phiếu đi theo đường duyệt cũ đang chạy.',
      tone: 'off',
    }
  }

  if (soLuong === 0) {
    return {
      label: 'Bật nhưng chưa có luồng',
      hint: 'Chưa khai luồng nào cho loại này nên phiếu vẫn đi đường duyệt cũ. Khai luồng rồi mới có tác dụng.',
      tone: 'idle',
    }
  }

  return {
    label: 'Bộ máy mới',
    hint: `Phiếu tạo từ giờ chạy theo ${soLuong} luồng đã khai.`,
    tone: 'running',
  }
}
