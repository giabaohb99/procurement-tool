import { CrudListPage } from '@/shared/crud'
import { HrSetupTabs } from '../components/hr-setup-tabs'
import { MEETING_ROOM_CRUD_CONFIG } from '../config/meeting-room-crud'
import { LIST_TOOLBAR_STICKY_TOP } from '../utils/list-sticky'

export function MeetingRoomListPage() {
  return (
    <CrudListPage
      config={MEETING_ROOM_CRUD_CONFIG}
      topContent={<HrSetupTabs />}
      compactHeader
      toolbarClassName={LIST_TOOLBAR_STICKY_TOP}
    />
  )
}
