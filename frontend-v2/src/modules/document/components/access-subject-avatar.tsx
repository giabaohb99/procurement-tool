import { Briefcase, Building2, Shield, User } from 'lucide-react'

import { Avatar, AvatarFallback } from '@/shared/ui/avatar'
import { nameInitials } from '@/shared/utils/name-initials'
import { SUBJECT_KIND } from '../types/document-access'

const SUBJECT_ICONS: Record<number, typeof User> = {
  [SUBJECT_KIND.employee]: User,
  [SUBJECT_KIND.department]: Briefcase,
  [SUBJECT_KIND.company]: Building2,
  [SUBJECT_KIND.role]: Shield,
}

interface AccessSubjectAvatarProps {
  subjectKind: number
  subjectName: string
}

/**
 * Ảnh đại diện của một dòng quyền (thư mục lẫn văn bản) — NGƯỜI hiện chữ viết
 * tắt tên thật (`nameInitials`, kiểu Drive), ba loại còn lại (phòng ban/pháp
 * nhân/vai trò) dùng icon vì không có "tên người" để viết tắt theo đúng nghĩa.
 */
export function AccessSubjectAvatar({ subjectKind, subjectName }: AccessSubjectAvatarProps) {
  const Icon = SUBJECT_ICONS[subjectKind] ?? User
  return (
    <Avatar size="sm" className="shrink-0">
      <AvatarFallback>
        {subjectKind === SUBJECT_KIND.employee ? (
          nameInitials(subjectName || '?')
        ) : (
          <Icon className="size-3.5" />
        )}
      </AvatarFallback>
    </Avatar>
  )
}
