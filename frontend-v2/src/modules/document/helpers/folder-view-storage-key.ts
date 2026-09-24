/**
 * Khóa `localStorage` lưu chế độ Lưới/Danh sách của khung nội dung thư mục —
 * DÙNG CHUNG giữa một thư mục THẬT (`folder-documents-table.tsx`) và gốc
 * «Thư mục của bạn» (`folder-my-drive-panel.tsx`, duoc-CR-476) — đổi chế độ
 * ở một trong hai chỗ rồi mở/đóng thư mục phải giữ nguyên, không nhảy về
 * mặc định. Tách khỏi component để `use-folder-documents-table-state.ts`
 * (một HOOK) không phải import ngược từ tầng `components/`.
 */
export const FOLDER_VIEW_STORAGE_KEY = 'erp.document.folder-view-grid'
