import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import {
  deleteDossierAttachment,
  fetchDossierAttachments,
  uploadDossierAttachments,
  type DossierAttachment,
} from '../api/dossier-attachment-api'

/**
 * Khóa cục bộ — ngoại lệ được phép của luật "query key nằm ở
 * `shared/constants/query-keys.ts`": nó chỉ có ba hook trong tệp này dùng, và
 * không ai invalidate từ ngoài.
 */
const attachmentKeys = {
  ofDossier: (dossierId: number) => ['dossier', 'attachments', dossierId] as const,
}

/** Danh sách bản scan của MỘT hồ sơ. */
export function useDossierAttachments(dossierId: number) {
  return useQuery({
    queryKey: attachmentKeys.ofDossier(dossierId),
    queryFn: () => fetchDossierAttachments(dossierId),
    enabled: dossierId > 0,
  })
}

export function useUploadDossierAttachments(dossierId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (files: File[]) => uploadDossierAttachments(dossierId, files),
    onSuccess: (uploaded: DossierAttachment[]) => {
      toast.success(
        uploaded.length > 1 ? `Đã tải lên ${uploaded.length} tệp` : 'Đã tải lên tệp',
      )
      void queryClient.invalidateQueries({ queryKey: attachmentKeys.ofDossier(dossierId) })
    },
    //  ⚠️ KHÔNG khai `onError`: `httpClient` đã tự bày toast cho mọi lệnh khác
    //  GET. Thêm một toast nữa ở đây là người dùng nhận HAI câu báo lỗi cho một
    //  lần bấm — và hai câu đó có thể nói khác nhau.
  })
}

export function useDeleteDossierAttachment(dossierId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (linkId: number) => deleteDossierAttachment(linkId),
    onSuccess: () => {
      toast.success('Đã gỡ tệp')
      void queryClient.invalidateQueries({ queryKey: attachmentKeys.ofDossier(dossierId) })
    },
  })
}
