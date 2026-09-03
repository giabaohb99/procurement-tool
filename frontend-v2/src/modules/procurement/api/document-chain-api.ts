import { apiGet, downloadFile } from '@/core/api'
import type { ChainAttachment } from '../types/document-chain'

const CHAIN_URL = '/api/attachments/chain'

export const documentChainApi = {
  /**
   * Toàn bộ chứng từ của chuỗi một đơn mua hàng.
   *
   * Backend chỉ nhận `entity = 'purchase_order'` (nấc khác trả 400), nên tham số
   * ở đây cố định luôn cho khỏi ai gọi nhầm bằng id yêu cầu mua hàng.
   */
  listChain: (purchaseOrderId: number) =>
    apiGet<ChainAttachment[]>(CHAIN_URL, {
      params: { entity: 'purchase_order', entity_id: purchaseOrderId },
    }),

  /** Tải trọn chuỗi thành một tệp nén, backend xếp sẵn theo thư mục nấc/loại. */
  downloadChainZip: (purchaseOrderId: number, filename: string) =>
    downloadFile(
      `${CHAIN_URL}/zip?entity=purchase_order&entity_id=${purchaseOrderId}`,
      filename,
    ),

  /**
   * Tải MỘT tệp qua API có kiểm quyền, không qua `url` đọc thẳng kho lưu trữ —
   * để backend còn chặn được người vừa bị thu hồi quyền.
   */
  downloadChainFile: (linkId: number, filename: string) =>
    downloadFile(`/api/attachments/${linkId}/download`, filename),
}
