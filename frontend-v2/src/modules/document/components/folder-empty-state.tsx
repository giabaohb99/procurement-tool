import { FolderOpen } from 'lucide-react'

/**
 * TRẠNG THÁI RỖNG kiểu Drive — CHỈ dựng khi thư mục KHÔNG CÓ GÌ cả (không thư
 * mục con, không văn bản). Chỉ icon mờ + một câu, KHÔNG có nút: tạo thư mục đi
 * nút «+ Mới» ở đầu khung cây hoặc nút `+` trên dòng cây — đại ca bỏ nút «Tạo
 * thư mục mới» ở đây 24/09/2026 vì nó lặp lại hai chỗ đó.
 */
export function FolderEmptyState() {
  return (
    <div className="flex flex-col items-center gap-3 py-16 text-center">
      <FolderOpen className="size-12 text-muted-foreground/40" />
      <p className="text-sm text-muted-foreground">Thư mục này chưa có gì.</p>
    </div>
  )
}
