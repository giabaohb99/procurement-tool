import { TriangleAlert } from 'lucide-react'

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/shared/ui/alert-dialog'
import { prerequisiteText } from '../helpers/prerequisite-text'
import type { DocPrerequisite } from '../types/document-link-rule'

interface DocumentPrerequisiteDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Tên loại đang chọn — nói tên ra thì người dùng biết cảnh báo nói về cái gì. */
  docTypeName: string
  items: DocPrerequisite[]
  /** Người dùng chọn "Vẫn tạo" — văn bản được tạo y như khi không có cảnh báo. */
  onConfirm: () => void
}

/**
 * CẢNH BÁO THIẾU VĂN BẢN TIÊN QUYẾT, hỏi ngay lúc bấm Tạo (E04b).
 *
 * Loại đang chọn có quan hệ bắt buộc tới một loại khác, mà trong kho chưa có
 * văn bản nào còn hiệu lực để trỏ vào — tạo xong sẽ mắc kẹt ở bước gửi duyệt.
 *
 * **Cảnh báo, không chặn.** Soạn con trước rồi ban hành cha sau là việc có
 * thật (cả hai đang chạy song song, hoặc cha đang nằm ở bàn người khác). Chặn
 * cứng ở đây là chặn nhầm, mà người bị chặn thì không có đường đi tiếp. Cổng
 * thật vẫn nằm ở bước gửi duyệt, nơi backend đếm quan hệ đã khai thật.
 *
 * Hỏi ở nhịp bấm Tạo chứ không phải banner cạnh ô chọn loại: người dùng lướt
 * qua banner mà không đọc, còn ở đây họ phải bấm một cái mới đi tiếp được.
 */
export function DocumentPrerequisiteDialog({
  open,
  onOpenChange,
  docTypeName,
  items,
  onConfirm,
}: DocumentPrerequisiteDialogProps) {
  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2">
            <TriangleAlert className="size-5 text-amber-600" />
            Chưa có văn bản để gắn quan hệ bắt buộc
          </AlertDialogTitle>
          <AlertDialogDescription asChild>
            <div className="space-y-3">
              <p>
                Loại <strong className="text-foreground">{docTypeName}</strong> yêu cầu gắn với
                các văn bản sau, nhưng hệ thống chưa tìm thấy văn bản còn hiệu lực nào:
              </p>

              {/*  Đánh số theo ĐÚNG thứ tự người khai đã xếp ở màn loại văn bản
                   (backend trả về đã sắp sẵn theo `sort_order`): thiếu ba thứ
                   thì người dùng còn biết đi làm cái nào trước.

                   Tên loại tách khỏi phần tình trạng: đó là thứ người đọc quét
                   mắt tìm, nhồi cả bốn thông tin vào một dòng chữ thì dòng nào
                   cũng dài bằng nhau và không có điểm bám. */}
              <ol className="divide-y divide-amber-200 overflow-hidden rounded-md border border-amber-200 bg-amber-50">
                {items.map((item, index) => (
                  <li
                    key={`${item.relation}-${item.target_type_id ?? 0}`}
                    className="flex items-baseline gap-2 px-3 py-2 text-sm text-amber-900"
                  >
                    <span className="tabular-nums">{index + 1}.</span>
                    <div>
                      <p>
                        <strong>{item.target_type_name}</strong>
                        <span className="text-amber-800">
                          {' '}
                          — quan hệ «{item.relation_label}»
                        </span>
                      </p>
                      <p className="text-amber-800">{prerequisiteText(item)}</p>
                    </div>
                  </li>
                ))}
              </ol>

              <p>
                Bạn vẫn tạo văn bản được. Tuy nhiên phải gắn đủ các quan hệ trên thì mới{' '}
                <strong className="text-foreground">gửi duyệt</strong> được.
              </p>
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>

        <AlertDialogFooter>
          <AlertDialogCancel>Quay lại</AlertDialogCancel>
          <AlertDialogAction onClick={onConfirm}>Vẫn tạo văn bản</AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
