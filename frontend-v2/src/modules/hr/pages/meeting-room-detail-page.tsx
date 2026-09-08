import { CrudDetailPage } from '@/shared/crud'
import { MEETING_ROOM_CRUD_CONFIG } from '../config/meeting-room-crud'

/** Chi tiết + THÊM MỚI phòng họp — cùng component, xem `CrudDetailPage`. */
export function MeetingRoomDetailPage() {
  return <CrudDetailPage config={MEETING_ROOM_CRUD_CONFIG} />
}
