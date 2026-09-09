import { CrudListPage } from '@/shared/crud'
import { MEETING_ROOM_CRUD_CONFIG } from '../config/meeting-room-crud'
import { RoomSectionTabs } from '../components/room-section-tabs'
import { LIST_SECTION_TOOLBAR_STICKY } from '../utils/list-sticky'

export function MeetingRoomListPage() {
  return (
    //  Khổ hẹp: dải chuyển màn ghim đỉnh, thanh công cụ ghim ngay dưới nó — mốc
    //  `top` của `LIST_SECTION_TOOLBAR_STICKY` bằng đúng 40px chiều cao dải trên.
    //  Cùng khuôn với màn Quỹ phép năm; ở đây cũng chỉ có MỘT hàng điều hướng.
    <CrudListPage
      config={MEETING_ROOM_CRUD_CONFIG}
      beforeContent={<RoomSectionTabs sticky />}
      toolbarClassName={LIST_SECTION_TOOLBAR_STICKY}
    />
  )
}
