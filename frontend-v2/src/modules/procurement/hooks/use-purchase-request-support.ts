import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { purchaseRequestSupportApi } from '../api/purchase-request-support-api'

const supportKeys = {
  warehouses: ['procurement', 'purchase-request-print', 'warehouses'] as const,
  units: ['procurement', 'purchase-request', 'units'] as const,
  itemGroups: ['procurement', 'purchase-request', 'item-groups'] as const,
  products: (search: string) => ['procurement', 'purchase-request', 'products', search] as const,
  purchaseHistory: (productCode: string, page: number, search: string) =>
    ['procurement', 'purchase-request', 'purchase-history', productCode, page, search] as const,
  attachments: (entity: string, entityId: number) =>
    ['procurement', 'attachments', entity, entityId] as const,
  documentTypes: ['procurement', 'attachments', 'document-types'] as const,
  comments: (entity: string, entityId: number) =>
    ['procurement', 'comments', entity, entityId] as const,
  relatedOrders: (code: string) =>
    ['procurement', 'purchase-request-related-orders', code] as const,
}

export function usePurchaseRequestPrintWarehouses() {
  return useQuery({
    queryKey: supportKeys.warehouses,
    queryFn: purchaseRequestSupportApi.listWarehouses,
    staleTime: 5 * 60 * 1000,
  })
}

export function usePurchaseRequestWarehouses(enabled = true) {
  return useQuery({
    queryKey: supportKeys.warehouses,
    queryFn: purchaseRequestSupportApi.listWarehouses,
    enabled,
    staleTime: 5 * 60 * 1000,
  })
}

export function usePurchaseRequestUnits(enabled = true) {
  return useQuery({
    queryKey: supportKeys.units,
    queryFn: purchaseRequestSupportApi.listUnits,
    enabled,
    staleTime: 5 * 60 * 1000,
  })
}

export function usePurchaseRequestItemGroups(enabled = true) {
  return useQuery({
    queryKey: supportKeys.itemGroups,
    queryFn: purchaseRequestSupportApi.listItemGroups,
    enabled,
    staleTime: 5 * 60 * 1000,
  })
}

export function usePurchaseRequestProducts(search: string, enabled = true) {
  return useQuery({
    queryKey: supportKeys.products(search),
    queryFn: () => purchaseRequestSupportApi.listProducts(search),
    enabled,
    staleTime: 60 * 1000,
  })
}

export function useProductPurchaseHistory(
  productCode: string,
  page: number,
  pageSize: number,
  search: string,
  enabled = true,
) {
  return useQuery({
    queryKey: supportKeys.purchaseHistory(productCode, page, search),
    queryFn: () =>
      purchaseRequestSupportApi.listProductPurchaseHistory(
        productCode,
        page,
        pageSize,
        search,
      ),
    enabled: enabled && !!productCode,
    placeholderData: (previousData) => previousData,
    staleTime: 60 * 1000,
  })
}

export function usePurchaseRequestAttachments(entity: string, entityId: number) {
  return useQuery({
    queryKey: supportKeys.attachments(entity, entityId),
    queryFn: () => purchaseRequestSupportApi.listAttachments(entity, entityId),
    enabled: entityId > 0,
  })
}

export function useDocumentTypes() {
  return useQuery({
    queryKey: supportKeys.documentTypes,
    queryFn: purchaseRequestSupportApi.listDocumentTypes,
    staleTime: Number.POSITIVE_INFINITY,
  })
}

export function useUploadPurchaseRequestAttachments(
  entity: string,
  entityId: number,
  /** Đơn mua hàng cha — bắt buộc khi đính kèm vào một LẦN GIAO. */
  purchaseOrderId = 0,
) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ files, docType }: { files: File[]; docType?: string }) =>
      purchaseRequestSupportApi.uploadAttachments(
        entity,
        entityId,
        files,
        docType,
        purchaseOrderId,
      ),
    onSuccess: () => {
      toast.success('Đã tải lên tệp đính kèm')
      void queryClient.invalidateQueries({
        queryKey: supportKeys.attachments(entity, entityId),
      })
    },
  })
}

/**
 * Tải NHIỀU MỤC chứng từ trong một lượt — mỗi mục là một loại kèm một xấp tệp.
 *
 * Không gọi `useUploadPurchaseRequestAttachments` lặp lại vì hook đó bật toast
 * cho từng lượt: chọn ba loại chứng từ là ba thông báo chồng lên nhau, mà người
 * dùng chỉ bấm "Lưu chứng từ" một lần nên chỉ chờ một câu trả lời.
 */
export function useUploadDocumentBatches(entity: string, entityId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (batches: { docType: string; files: File[] }[]) => {
      // Tuần tự: mỗi mục là một yêu cầu ghi vào cùng một chứng từ, bắn song song
      // chỉ tổ bắt server khóa đi khóa lại một bản ghi.
      let uploaded = 0
      for (const batch of batches) {
        await purchaseRequestSupportApi.uploadAttachments(
          entity,
          entityId,
          batch.files,
          batch.docType,
        )
        uploaded += batch.files.length
      }
      return uploaded
    },
    onSuccess: (uploaded) => {
      toast.success(`Đã tải lên ${uploaded} tệp`)
      void queryClient.invalidateQueries({
        queryKey: supportKeys.attachments(entity, entityId),
      })
    },
  })
}

/**
 * Tải phiếu giao cho NHIỀU lần giao một lượt, dùng ngay sau khi lưu Đơn mua hàng.
 *
 * Khác `useUploadPurchaseRequestAttachments` ở chỗ đích đến chỉ biết lúc GỌI:
 * lần giao vừa thêm chưa có id, phải lưu đơn xong mới dò ra id để gắn tệp.
 */
export function useUploadDeliveryFiles() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({
      purchaseOrderId,
      batches,
    }: {
      purchaseOrderId: number
      batches: { deliveryId: number; files: File[] }[]
    }) => {
      // Tải tuần tự: mỗi lần giao là một yêu cầu riêng, bắn song song chỉ tổ
      // làm server phải khóa cùng một đơn nhiều lần.
      for (const batch of batches) {
        await purchaseRequestSupportApi.uploadAttachments(
          'delivery',
          batch.deliveryId,
          batch.files,
          '',
          purchaseOrderId,
        )
      }
      return batches
    },
    onSuccess: (batches) => {
      if (!batches.length) return
      toast.success(`Đã tải phiếu giao cho ${batches.length} lần giao`)
      batches.forEach((batch) => {
        void queryClient.invalidateQueries({
          queryKey: supportKeys.attachments('delivery', batch.deliveryId),
        })
      })
    },
  })
}

export function useDeletePurchaseRequestAttachment(entity: string, entityId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: purchaseRequestSupportApi.deleteAttachment,
    onSuccess: () => {
      toast.success('Đã xóa tệp đính kèm')
      void queryClient.invalidateQueries({
        queryKey: supportKeys.attachments(entity, entityId),
      })
    },
  })
}

/** Bình luận của một chứng từ: `purchase_request` hoặc `purchase_order`. */
export function useDocumentComments(entity: string, entityId: number) {
  return useQuery({
    queryKey: supportKeys.comments(entity, entityId),
    queryFn: () => purchaseRequestSupportApi.listComments(entity, entityId),
    enabled: entityId > 0,
  })
}

export function useCreateDocumentComment(entity: string, entityId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({
      body,
      parentId = 0,
      files = [],
    }: {
      body: string
      parentId?: number
      files?: File[]
    }) => {
      const uploaded = files.length
        ? await purchaseRequestSupportApi.uploadCommentFiles(files)
        : []
      return purchaseRequestSupportApi.createComment(
        entity,
        entityId,
        body,
        parentId,
        uploaded.map((file) => file.file_id),
      )
    },
    onSuccess: () => {
      toast.success('Đã gửi bình luận')
      void queryClient.invalidateQueries({ queryKey: supportKeys.comments(entity, entityId) })
    },
  })
}

export function useDocumentCommentActions(entity: string, entityId: number) {
  const queryClient = useQueryClient()
  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: supportKeys.comments(entity, entityId) })

  const toggleLike = useMutation({
    mutationFn: purchaseRequestSupportApi.toggleLike,
    onSuccess: () => void invalidate(),
  })
  const remove = useMutation({
    mutationFn: purchaseRequestSupportApi.deleteComment,
    onSuccess: () => {
      toast.success('Đã xóa bình luận')
      void invalidate()
    },
  })

  return { toggleLike, remove }
}

export function useRelatedPurchaseOrders(code: string) {
  return useQuery({
    queryKey: supportKeys.relatedOrders(code),
    queryFn: () => purchaseRequestSupportApi.listRelatedPurchaseOrders(code),
    enabled: !!code,
  })
}
