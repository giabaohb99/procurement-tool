/**
 * VĂN BẢN MẪU - nội dung khởi tạo được chép vào phiên bản 1.0 khi tạo văn bản.
 *
 * Danh sách không trả `content_html` để tránh tải hàng loạt nội dung dài. Chỉ
 * API chi tiết của một mẫu mới trả trường này.
 */
export interface DocumentTemplateListItem {
  id: number
  doc_type_id: number
  doc_type_name: string
  doc_type_code: string
  name: string
  description: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface DocumentTemplate extends DocumentTemplateListItem {
  content_html: string
}

export interface DocumentTemplateInput {
  doc_type_id: number
  name: string
  description: string
  content_html: string
  is_active: boolean
}
