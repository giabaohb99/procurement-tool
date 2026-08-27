import { useQueryClient } from '@tanstack/react-query'
import { useCallback } from 'react'

import { queryKeys } from '@/shared/constants/query-keys'
import { documentApi, documentVersionApi } from '../api/document-api'

/**
 * NẠP TRƯỚC dữ liệu trang chi tiết ngay khi con trỏ rê vào dòng danh sách.
 *
 * Vì sao có: đo trên bản chạy thật, mở một văn bản 100 trang từ danh sách mất
 * **372ms**, trong đó gần một nửa chỉ là chờ mạng — và tệ hơn, hai lượt gọi
 * **nối đuôi nhau**: `/documents/:id/versions` phải xong thì
 * `/documents/:id/versions/:versionId` (chỗ chứa NỘI DUNG thật) mới bắt đầu.
 * Người dùng bấm xong ngồi nhìn khung trống suốt quãng đó.
 *
 * Quãng từ lúc rê chuột tới lúc bấm gần như luôn dài hơn 175ms, nên nạp ở nhịp
 * rê là lấp trọn phần chờ mạng mà **không phải đụng gì tới backend**.
 *
 * Nạp đúng HAI thứ mở màn: bản ghi văn bản và danh sách phiên bản. Cố tình
 * KHÔNG nạp nội dung phiên bản — muốn biết nạp bản nào thì phải chờ danh sách
 * trả về, mà chờ như thế là dựng lại đúng cái thác nước vừa muốn tránh; hơn nữa
 * nội dung là thứ nặng nhất, kéo về cho mọi dòng người dùng chỉ lướt qua là phí
 * băng thông của họ.
 *
 * `prefetchQuery` tự bỏ qua khi dữ liệu còn tươi, nên rê tới rê lui trên cùng
 * một dòng không sinh thêm lượt gọi nào.
 */
export function usePrefetchDocument() {
  const queryClient = useQueryClient()

  return useCallback(
    (documentId: number) => {
      if (!documentId || documentId <= 0) return

      void queryClient.prefetchQuery({
        queryKey: queryKeys.document.record(documentId),
        queryFn: () => documentApi.getById(documentId),
        //  Coi là còn tươi trong 30 giây: đủ để nhịp rê → bấm dùng lại, mà vẫn
        //  ngắn hơn nhiều so với nhịp hỏi lại của chính trang chi tiết nên
        //  không có chuyện mở ra thấy dữ liệu cũ.
        staleTime: 30_000,
      })
      void queryClient.prefetchQuery({
        queryKey: queryKeys.document.versions(documentId),
        queryFn: () => documentVersionApi.list(documentId),
        staleTime: 30_000,
      })
    },
    [queryClient],
  )
}
