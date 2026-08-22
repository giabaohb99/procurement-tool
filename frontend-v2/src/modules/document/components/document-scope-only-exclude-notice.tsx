import { TriangleAlert } from 'lucide-react'

/**
 * Cảnh báo khi phạm vi chỉ toàn dòng LOẠI TRỪ — xem `helpers/scope-only-exclude`.
 *
 * Dùng chung cho cả màn Tạo văn bản lẫn thẻ Phạm vi ở trang chi tiết: hai chỗ
 * này khai cùng một thứ, người dùng mắc cùng một lỗi, nên phải nói cùng một câu.
 *
 * Cố ý KHÔNG chặn thao tác. Có tình huống hợp lệ hiếm gặp (soạn trước khung
 * loại trừ rồi thêm dòng bao gồm sau), và chặn cứng ở đây thì người dùng không
 * lưu nổi bản nháp đang soạn dở.
 */
export function DocumentScopeOnlyExcludeNotice() {
  return (
    <div
      role="alert"
      className="flex gap-3 rounded-md border border-destructive/40 bg-destructive/5 px-4 py-3"
    >
      <TriangleAlert className="mt-0.5 size-4 shrink-0 text-destructive" />
      <div className="text-sm">
        <p className="font-medium text-destructive">
          Đang chỉ có dòng loại trừ — ban hành xong văn bản sẽ không tới một ai.
        </p>
        <p className="text-muted-foreground">
          Khai bất kỳ dòng nào là tắt mặc định «áp cho toàn bộ pháp nhân ban hành». Muốn trừ ai đó
          ra thì phải khai thêm một dòng <strong>Bao gồm</strong> nói rõ áp cho ai trước — thường là
          bao gồm chính pháp nhân đứng tên văn bản.
        </p>
      </div>
    </div>
  )
}
