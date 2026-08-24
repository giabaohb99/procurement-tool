import { FileText, X } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { FileDropzone } from '@/shared/ui/file-dropzone'
import { FormCard } from '@/shared/ui/form-card'
import { formatFileSize } from '@/shared/utils/format-file-size'

interface DocumentPendingAttachmentsProps {
  files: File[]
  onChange: (files: File[]) => void
}

/**
 * TỆP ĐÍNH KÈM chọn ngay lúc TẠO văn bản — giữ tạm ở trình duyệt, tải lên sau.
 *
 * Đính kèm treo vào **phiên bản** (`entity = 'document_version'`), mà phiên bản
 * 1.0 chỉ ra đời cùng lúc với văn bản. Nên ở form tạo không có gì để tải tệp lên
 * cả: tệp xếp hàng trong bộ nhớ y như quyền truy cập, phạm vi và kế hoạch clone,
 * rồi gửi ngay sau khi văn bản có id (xem `guiPhanXepHang`).
 *
 * Trước đây form tạo **không có chỗ đính kèm nào** — người soạn phải tạo văn bản
 * xong, vào tab Soạn thảo, mới thấy khối tệp. Với loại văn bản mà cái đính kèm
 * CHÍNH LÀ nội dung (bản scan có chữ ký, phụ lục Excel) thì đó là hai lần đi
 * đường cho một việc.
 *
 * Trùng tên thì vẫn nhận: hai tệp cùng tên ở hai thư mục là chuyện thường, và
 * backend lưu theo id chứ không theo tên.
 */
export function DocumentPendingAttachments({ files, onChange }: DocumentPendingAttachmentsProps) {
  return (
    <FormCard title="Tệp đính kèm">
      <div className="space-y-3">
        <FileDropzone
          hint="Kéo thả tệp vào đây hoặc bấm để chọn"
          onFiles={(picked) => onChange([...files, ...picked])}
        />

        <p className="text-xs text-muted-foreground">
          Tệp được tải lên ngay sau khi văn bản được tạo. Muốn thêm hay gỡ về sau thì mở
          tab <strong>Soạn thảo</strong> của văn bản.
        </p>

        {files.length > 0 && (
          <ul className="divide-y rounded-md border">
            {files.map((file, index) => (
              //  Khóa theo tên + cỡ + vị trí: cùng một tệp chọn hai lần vẫn là
              //  hai dòng, mà `File` thì không có id nào để bám.
              <li
                key={`${file.name}-${file.size}-${index}`}
                className="flex items-center gap-3 px-3 py-2"
              >
                <FileText className="size-4 shrink-0 text-muted-foreground" />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm">{file.name}</p>
                  <p className="text-xs text-muted-foreground">{formatFileSize(file.size)}</p>
                </div>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon-sm"
                  className="size-6 -my-px"
                  title="Bỏ tệp này"
                  aria-label={`Bỏ ${file.name}`}
                  onClick={() => onChange(files.filter((_, i) => i !== index))}
                >
                  <X className="size-4" />
                </Button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </FormCard>
  )
}
