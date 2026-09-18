import { CrudListPage } from '@/shared/crud'
import { MEETING_ROOM_CRUD_CONFIG } from '../config/meeting-room-crud'
import { LIST_TOOLBAR_STICKY_TOP } from '../utils/list-sticky'

export function MeetingRoomListPage() {
  return (
    <CrudListPage
      config={MEETING_ROOM_CRUD_CONFIG}
      toolbarClassName={LIST_TOOLBAR_STICKY_TOP}
    />
  )
}
