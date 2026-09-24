import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { apiPatch } from '@/core/api'
import { queryKeys } from '@/shared/constants/query-keys'
import type { DocKind, DossierProgressStatus } from '../types/dossier-applicability'

/**
 * Ô nào KHÔNG gửi thì giữ nguyên — đường này là PATCH.
 *
 * ⚠️ `planned_date: null` (xóa ngày) khác hẳn *không gửi khóa đó* (đừng đụng
 * vào). Gửi `undefined` thì `JSON.stringify` bỏ khóa luôn, đúng ý «đừng đụng»;
 * muốn xóa ngày phải gửi `null` tường minh.
 */
export interface DossierProgressPayload {
  status?: DossierProgressStatus
  required?: boolean
  assignee_id?: number
  planned_date?: string | null
  note?: string
  file_note?: string
  /** `[]` = bỏ hết tiên quyết. Không gửi khóa này = đừng đụng vào. */
  depends?: number[]
}

/**
 * Đặt TIẾN ĐỘ của một tờ hồ sơ TRÊN CHỨNG TỪ ĐANG MỞ.
 *
 * ⚠️ **Không đụng tới tờ hồ sơ trong kho.** Đường này ghi vào
 * `tab_dossier_progress`, nên tick xong ở phiếu này thì phiếu khác không đổi
 * theo — khác hẳn `PATCH /api/dossiers/{id}`, thứ sửa chính tờ giấy dùng chung.
 *
 * ⚠️ Quyền: backend đòi quyền **ghi trên chứng từ**, không phải `dossier.write`.
 * Ai sửa được phiếu thì tick được hồ sơ của phiếu đó.
 */
export function useSetDossierProgress(docKind: DocKind, docId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      dossierId,
      payload,
    }: {
      dossierId: number
      payload: DossierProgressPayload
    }) =>
      apiPatch(
        `/api/dossiers/applicable/${dossierId}/progress?doc_kind=${docKind}&doc_id=${docId}`,
        payload,
      ),
    onSuccess: () => {
      //  Chỉ dọn kết quả của CHÍNH phiếu này. Dọn cả `queryKeys.dossier.all` là
      //  kéo theo mọi phiếu khác đang nằm trong bộ nhớ đệm gọi lại — mà tiến độ
      //  của chúng vừa được tách ra khỏi nhau, không còn ảnh hưởng gì tới nhau.
      queryClient.invalidateQueries({ queryKey: queryKeys.dossier.applicable(docKind, docId) })
    },
    onError: () => {
      //  Ô tick là thao tác một-cú-bấm, không có form nào để báo lỗi tại chỗ —
      //  im lặng thì người dùng tưởng đã lưu. Hay gặp nhất: thiếu quyền ghi
      //  trên chính tờ phiếu (403).
      toast.error('Không lưu được tiến độ hồ sơ')
    },
  })
}
