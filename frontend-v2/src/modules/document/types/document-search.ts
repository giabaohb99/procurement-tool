/**
 * Kết quả TÌM KIẾM TOÀN VĂN văn bản (phase 07, duoc-CR-477) —
 * `GET /api/documents/search` (`backend/app/modules/document/search_service.py`).
 *
 * Mỗi dòng kết quả có hình dạng GIỐNG HỆT `DocumentRecord` của danh sách
 * thường (cùng `serializer.serialize_many`) CỘNG thêm khóa `search` — điểm
 * khớp, nơi trúng, và đoạn trích để tô sáng.
 */
import type { DocumentRecord } from './document-record'

/**
 * Đoạn trích ±80 ký tự quanh lần trúng đầu tiên — `text` là CHỮ THẬT (có dấu,
 * chưa gập), `highlights` là offset TRONG chính `text` (không phải trong toàn
 * văn), dùng thẳng với `search-snippet.tsx` để tô `<mark>`.
 */
export interface DocumentSearchSnippet {
  text: string
  /** `[[start, end], ...]` — nửa khoảng mở [start, end), có thể rỗng. */
  highlights: [number, number][]
}

/** Nơi khớp CHÍNH của một dòng kết quả — quyết định nhãn "trúng trong: …". */
export type DocumentSearchMatchedIn = 'meta' | 'body' | 'file' | ''

export interface DocumentSearchHit {
  /** `3×meta + 2×body + 1×file` — chỉ dùng để SẮP HẠNG, không hiển thị số. */
  score: number
  matched_in: DocumentSearchMatchedIn
  /** "Nội dung" · "Tệp ‹tên tệp›" · "" (khớp thuần trên siêu dữ liệu). */
  match_label: string
  /** `null` khi khớp thuần trên siêu dữ liệu (không có đoạn trích để tô). */
  snippet: DocumentSearchSnippet | null
}

export interface DocumentSearchResult extends DocumentRecord {
  search: DocumentSearchHit
}
