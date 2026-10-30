import {
  BookOpen,
  LayoutDashboard,
  MessagesSquare,
  Plug,
  ScrollText,
  Send,
  Settings2,
  SlidersHorizontal,
  Sparkles,
  UsersRound,
} from 'lucide-react'

import type { ErpModule } from '@/app/router/module-definition'
import { aiSkillRoutes } from '@/modules/ai-skill/routes'
import { assistantRoutes } from '@/modules/assistant/routes'
import { appRoutes } from '@/shared/constants/app-routes'

const SETS_PATH = `${appRoutes.aiSkill.root}/sets`
const SKILLS_PATH = `${appRoutes.aiSkill.root}/skills`

/**
 * Phân hệ AI (bao-CR-696, đại ca chốt 30/10/2026) — gộp hai phân hệ cũ *Trợ lý AI* (`modules/assistant`) và *Kho
 * skill AI* (`modules/ai-skill`) thành MỘT thẻ trên màn chọn phân hệ. Mã màn hình vẫn nằm ở hai thư mục cũ, đường dẫn
 * cũ giữ nguyên (`/assistant/...`, `/ai-skill/...` qua `extraPaths`); thư mục này chỉ khai menu.
 *
 * Không khai `entity` cấp phân hệ: phân hệ mở cho nhiều khóa (`assistant`, `ai_skill`, `ai_mcp_key_admin`,
 * `agent_group`) và `canOpenModule` đếm mục menu còn hiện — mỗi mục tự gác khóa của mình, giữ đúng như hai phân hệ cũ.
 *
 * `path` là `/assistant` để bấm thẻ vào thẳng khung chat. Người không có quyền Trợ lý AI thì `ModuleLayout` tự đưa về
 * màn đầu tiên họ xem được (`firstAccessibleNavPath`), nên thứ tự mục dưới đây cũng là thứ tự ưu tiên đáp xuống.
 *
 * Màn "AI của tôi" của từng người nằm ở Trang cá nhân (`/me?tab=ai-connect`), ai cũng có — không ở đây.
 */
export const aiModule: ErpModule = {
  id: 'ai',
  title: 'AI',
  description: 'Trợ lý AI, kết nối AI riêng của nhân sự, kho skill, nhật ký sử dụng và cấu hình.',
  icon: Sparkles,
  path: appRoutes.assistant.root,
  extraPaths: [appRoutes.aiSkill.root],
  accent: 'bg-violet-500/10 text-violet-600 dark:text-violet-400',
  enabled: true,

  nav: [
    {
      label: 'Trợ lý AI',
      path: appRoutes.assistant.root,
      icon: Sparkles,
      end: true,
      entity: 'assistant',
    },
    {
      //  Màn Khóa nhân sự cũ (G5) nâng cấp: mỗi dòng là một kết nối — khóa riêng hay OAuth, ứng dụng nào.
      label: 'Kết nối',
      path: appRoutes.aiSkill.keys,
      icon: Plug,
      entity: 'ai_mcp_key_admin',
    },
    {
      //  `end` + `matchPaths`: không có `end` thì `/ai-skill` sáng ở MỌI trang con; còn chi tiết bộ và trang soạn vẫn
      //  phải làm sáng mục này.
      label: 'Bộ skill',
      path: appRoutes.aiSkill.root,
      icon: BookOpen,
      entity: 'ai_skill',
      end: true,
      matchPaths: [SETS_PATH, SKILLS_PATH],
      group: 'Kho skill',
    },
    //  Hai mục ẨN giữ chốt gác quyền cho `/ai-skill/sets/:id` và `/ai-skill/skills/:id` (gõ thẳng URL thiếu quyền thì bị
    //  chặn tử tế) — xem `ModuleNavItem.hidden`.
    { label: 'Chi tiết bộ skill', path: SETS_PATH, entity: 'ai_skill', hidden: true, group: 'Kho skill' },
    { label: 'Soạn skill', path: SKILLS_PATH, entity: 'ai_skill', hidden: true, group: 'Kho skill' },
    {
      //  Số liệu cần quyền quản lý bot AI (`agent_group.read`); gác mục theo hai khóa của kho skill để người chỉ quản lý
      //  bot không thấy mục rỗng — người thiếu `agent_group` mở ra thấy trang tự nói rõ, không ăn 403.
      label: 'Tổng quan',
      path: appRoutes.aiSkill.overview,
      icon: LayoutDashboard,
      entities: ['ai_skill', 'ai_mcp_key_admin'],
      group: 'Giám sát',
    },
    {
      //  Máy chủ tự giới hạn người thường chỉ xem lượt của mình.
      label: 'Nhật ký sử dụng',
      path: appRoutes.aiSkill.logs,
      icon: ScrollText,
      entities: ['ai_skill', 'ai_mcp_key_admin'],
      group: 'Giám sát',
    },
    {
      //  Bot Telegram đã đóng băng tính năng (17/10/2026) nên thu vào một mục sổ xuống, ĐÓNG sẵn — chỉ tự mở khi đang
      //  đứng ở một màn con. Quyền của mục cha = có ít nhất một mục con hiện; `entities` khai cho bài kiểm "mục nào cũng
      //  gác khóa".
      //  ⚠️ `path` phải là route CÓ THẬT và là màn của người quản lý bot: `firstAccessibleNavPath` có thể chọn mục cha
      //  cho người KHÔNG có `assistant` (chỉ có `agent_group`) — trỏ vào Nhóm chat là họ đáp xuống trang 403. Người có
      //  `assistant` thì luôn vào được gốc `/assistant`, không bao giờ đi nhánh dự phòng đó.
      label: 'Bot Telegram',
      path: appRoutes.assistant.botUsers,
      icon: Send,
      entities: ['assistant', 'agent_group'],
      group: 'Giám sát',
      children: [
        {
          //  ai-CR-123: ai vào được Trợ lý AI đều xem được nhóm MÌNH là thành viên; `agent_group` mở thêm "Tất cả nhóm".
          label: 'Nhóm chat',
          path: appRoutes.assistant.groups,
          icon: MessagesSquare,
          entity: 'assistant',
        },
        {
          //  ai-CR-131: chỉ người quản lý bot AI.
          label: 'Người dùng bot',
          path: appRoutes.assistant.botUsers,
          icon: UsersRound,
          entity: 'agent_group',
        },
      ],
    },
    {
      //  Cấu hình cổng MCP (G7) đòi `agent_group.read` / `.write` — gác mục theo hai khóa của kho skill, trang tự giải
      //  thích khi thiếu quyền quản lý bot AI, tự chuyển chỉ xem khi thiếu quyền ghi.
      label: 'Cấu hình chung',
      path: appRoutes.aiSkill.settings,
      icon: Settings2,
      entities: ['ai_skill', 'ai_mcp_key_admin'],
      group: 'Cấu hình',
    },
    {
      //  Ứng dụng AI tự đăng ký OAuth (bao-CR-635) — chỉ để quản trị dọn đăng ký ứng dụng, nên CHỈ người quản lý bot AI
      //  (`agent_group`, đúng khóa đường API đòi) mới thấy mục.
      label: 'Nâng cao',
      path: appRoutes.aiSkill.oauthClients,
      icon: SlidersHorizontal,
      entity: 'agent_group',
      group: 'Cấu hình',
    },
    //  Mục "Giới thiệu" (`/ai-skill/intro`) TẠM ẨN ngày 26/10/2026 — xem chú thích route ở `modules/ai-skill/routes.tsx`.
  ],

  routes: [...assistantRoutes, ...aiSkillRoutes],
}
