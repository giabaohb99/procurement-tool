import { apiGet, downloadFile } from '@/core/api'
import type { MyLaborContractListResult } from '../types/my-labor-contract'

const ME_URL = '/api/me/labor-contracts'

/** API "Hợp đồng của tôi" — CHỈ ĐỌC; người xem do server suy ra từ phiên đăng nhập, không gửi id nhân sự. */
export const myLaborContractApi = {
  list: () => apiGet<MyLaborContractListResult>(ME_URL),

  /** Bản mềm (.docx) đã sinh. Tên tệp do server đặt. */
  downloadDocument: (id: number, fallbackName: string) => downloadFile(`${ME_URL}/${id}/document`, fallbackName),

  /** Bản đã ký (scan). */
  downloadSignedFile: (id: number, fallbackName: string) => downloadFile(`${ME_URL}/${id}/signed-file`, fallbackName),
}
