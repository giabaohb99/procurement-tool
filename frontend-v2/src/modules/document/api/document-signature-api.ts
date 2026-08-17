import { apiGet, apiPost } from '@/core/api'
import type {
  DocumentSignature,
  DocumentSignatureInput,
  SignKindOption,
} from '../types/document-signature'

const BASE_URL = '/api/documents'

export const documentSignatureApi = {
  list: (documentId: number) =>
    apiGet<DocumentSignature[]>(`${BASE_URL}/${documentId}/signatures`),

  kinds: () => apiGet<SignKindOption[]>(`${BASE_URL}/sign-kinds`),

  sign: (documentId: number, values: DocumentSignatureInput) =>
    apiPost<DocumentSignature>(`${BASE_URL}/${documentId}/signatures`, values),

  //  KHÔNG có hàm xóa — cố ý. Bảng chỉ ghi thêm; chữ ký gỡ được thì không còn
  //  là chữ ký. Ký nhầm thì mở phiên bản mới.
}
