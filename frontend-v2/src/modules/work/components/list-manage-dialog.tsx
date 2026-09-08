import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Separator } from '@/shared/ui/separator'
import { useListInfoForm } from '../hooks/use-list-info-form'
import { WORK_ROLE, type WorkList } from '../types/work'
import { ListInfoPanel } from './list-info-panel'
import { ListMembersPanel } from './list-members-panel'

interface ListManageDialogProps {
  open: boolean
  list: WorkList
  /** Vai trò của CHÍNH mình trên dự án — quyết định sửa được gì (04 §3). */
  myRole: number | null
  onClose: () => void
}

/**
 * QUẢN LÝ DỰ ÁN — **một hộp, không tab**: Thông tin rồi tới Thành viên.
 *
 * Trước đây là hai mục rời trong menu («Thành viên» và «Sửa dự án»), rồi một hộp
 * hai tab. Cả hai đều sai cùng một kiểu: quản trị mở hộp này ra thường làm CẢ HAI
 * việc trong một lượt — đổi tên xong mời thêm người — nên chia ngăn chỉ tổ bắt họ
 * bấm qua lại và nhớ mình đang đứng ở đâu. Xếp dọc thì cuộn một cái là thấy hết.
 *
 * Thẻ *Trường của dự án* KHÔNG gộp vào đây: đó là cấu hình bộ nhãn tùy biến, mở
 * ra để làm việc lâu chứ không phải sửa vài ô rồi đóng.
 *
 * Người chỉ có quyền xem vẫn mở được — biết mình đang làm việc với ai không phải
 * quyền quản trị (A-02). Khối Thông tin lúc đó chuyển sang dạng chỉ đọc, khối
 * Thành viên bỏ hàng mời và các nút thao tác.
 */
export function ListManageDialog({ open, list, myRole, onClose }: ListManageDialogProps) {
  //  Hai NGƯỠNG khác nhau, đúng theo backend — đừng gộp làm một:
  //   · sửa thông tin dự án  → `update_list` gác bằng `CAN_OWN`;
  //   · mời / gỡ / đổi vai trò → `add_member` gác bằng `CAN_MANAGE`.
  //  Gộp lại thì hoặc Quản trị thấy ô nhập rồi ăn 403 lúc bấm Lưu, hoặc Chủ sở
  //  hữu mất hàng mời.
  const canEditInfo = myRole === WORK_ROLE.OWNER
  const form = useListInfoForm(list)

  return (
    <Dialog open={open} onOpenChange={(o) => !o && onClose()}>
      {/*  Chỉ nới BỀ NGANG. Không đặt `max-h-… overflow-y-auto` ở đây: từ
           03/09/2026 chính lớp overlay là khung cuộn (xem `shared/ui/dialog.tsx`),
           thêm một khung cuộn nữa ở đây là con lăn chuột chết. */}
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Quản lý dự án</DialogTitle>
        </DialogHeader>

        <div className="space-y-5">
          <ListInfoPanel list={list} form={form} canEdit={canEditInfo} />
          <Separator />
          <ListMembersPanel open={open} listId={list.id} myRole={myRole} />
        </div>

        {/*  Nút Lưu nằm ở ĐÁY HỘP, không nằm ngay dưới khối Thông tin: đáy hộp là
             chỗ mắt tìm nút xác nhận, và đặt lửng giữa hộp thì nó trông như đang
             xác nhận cho cả phần thành viên bên dưới. */}
        {canEditInfo && (
          <DialogFooter>
            <Button variant="outline" onClick={onClose}>
              Đóng
            </Button>
            <Button onClick={form.save} disabled={!form.canSave}>
              Lưu thông tin
            </Button>
          </DialogFooter>
        )}
      </DialogContent>
    </Dialog>
  )
}
