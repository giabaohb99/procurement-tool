/**
 * Tiêu đề TRANG SỬA của danh mục Đặt xe: tên bản ghi + một dòng tóm tắt mờ.
 *
 * ⚠️ Truyền vào giá trị ĐANG NHẬP chứ không phải giá trị đã lưu — sửa loại xe
 * hay hạng bằng lái là dòng tóm tắt đổi theo ngay, người dùng thấy trước hệ quả
 * của thứ mình vừa gõ mà không phải bấm Lưu để kiểm chứng.
 *
 * Dùng chung cho biểu mẫu Xe và Tài xế: hai trang đứng cạnh nhau trong cùng một
 * menu nên phải cùng một cỡ chữ.
 */
export function CatalogRecordTitle({ title, summary }: { title: string; summary: string }) {
  return (
    <div className="min-w-0">
      <h1 className="truncate text-xl font-semibold tracking-tight text-navy dark:text-foreground">
        {title}
      </h1>
      <p className="truncate text-xs text-muted-foreground">{summary}</p>
    </div>
  )
}
