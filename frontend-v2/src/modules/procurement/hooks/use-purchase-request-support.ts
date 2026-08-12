import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { purchaseRequestSupportApi } from '../api/purchase-request-support-api'

const supportKeys = {
  attachments: (entity: string, entityId: number) =>
    ['procurement', 'attachments', entity, entityId] as const,
  documentTypes: ['procurement', 'attachments', 'document-types'] as const,
  comments: (purchaseRequestId: number) =>
    ['procurement', 'purchase-request-comments', purchaseRequestId] as const,
  relatedOrders: (code: string) =>
    ['procurement', 'purchase-request-related-orders', code] as const,
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

export function useUploadPurchaseRequestAttachments(entity: string, entityId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ files, docType }: { files: File[]; docType?: string }) =>
      purchaseRequestSupportApi.uploadAttachments(entity, entityId, files, docType),
    onSuccess: () => {
      toast.success('Đã tải lên tệp đính kèm')
      void queryClient.invalidateQueries({
        queryKey: supportKeys.attachments(entity, entityId),
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

export function usePurchaseRequestComments(purchaseRequestId: number) {
  return useQuery({
    queryKey: supportKeys.comments(purchaseRequestId),
    queryFn: () => purchaseRequestSupportApi.listComments(purchaseRequestId),
    enabled: purchaseRequestId > 0,
  })
}

export function useCreatePurchaseRequestComment(purchaseRequestId: number) {
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
        purchaseRequestId,
        body,
        parentId,
        uploaded.map((file) => file.file_id),
      )
    },
    onSuccess: () => {
      toast.success('Đã gửi bình luận')
      void queryClient.invalidateQueries({ queryKey: supportKeys.comments(purchaseRequestId) })
    },
  })
}

export function usePurchaseRequestCommentActions(purchaseRequestId: number) {
  const queryClient = useQueryClient()
  const invalidate = () =>
    queryClient.invalidateQueries({ queryKey: supportKeys.comments(purchaseRequestId) })

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
