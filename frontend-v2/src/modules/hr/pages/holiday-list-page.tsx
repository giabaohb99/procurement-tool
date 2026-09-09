import { CrudListPage } from '@/shared/crud'
import { HOLIDAY_CRUD_CONFIG } from '../config/holiday-crud'
import { LeaveSectionTabs } from '../components/leave-section-tabs'
import { LEAVE_SETTINGS_TOOLBAR_STICKY } from '../utils/leave-list-sticky'

export function HolidayListPage() {
  return (
    //  Ghim y như màn Loại nghỉ — hai màn nằm chung tab «Thiết lập», một màn
    //  ghim còn màn kia trôi thì chuyển qua lại đọc ra như hai phần mềm.
    <CrudListPage
      config={HOLIDAY_CRUD_CONFIG}
      beforeContent={<LeaveSectionTabs sticky />}
      toolbarClassName={LEAVE_SETTINGS_TOOLBAR_STICKY}
    />
  )
}
