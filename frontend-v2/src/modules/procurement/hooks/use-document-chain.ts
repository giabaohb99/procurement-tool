import { useQuery } from '@tanstack/react-query'

import { documentChainApi } from '../api/document-chain-api'

/**
 * Khóa cục bộ: chỉ trang «Chứng từ theo chuỗi» dùng, và không ai làm mất hiệu
 * lực nó từ bên ngoài (tải/xóa tệp làm mất hiệu lực khóa `attachments` của đúng
 * chứng từ đó, còn chuỗi thì luôn nạp lại khi mở trang).
 */
const chainKeys = {
  chain: (purchaseOrderId: number) =>
    ['procurement', 'attachments', 'chain', purchaseOrderId] as const,
}

export function useDocumentChain(purchaseOrderId: number) {
  return useQuery({
    queryKey: chainKeys.chain(purchaseOrderId),
    queryFn: () => documentChainApi.listChain(purchaseOrderId),
    enabled: purchaseOrderId > 0,
  })
}
