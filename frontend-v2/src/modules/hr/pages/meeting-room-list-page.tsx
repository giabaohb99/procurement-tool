import { CrudListPage } from '@/shared/crud'
import { MEETING_ROOM_CRUD_CONFIG } from '../config/meeting-room-crud'
import { RoomSectionTabs } from '../components/room-section-tabs'

export function MeetingRoomListPage() {
  return <CrudListPage config={MEETING_ROOM_CRUD_CONFIG} beforeContent={<RoomSectionTabs />} />
}
