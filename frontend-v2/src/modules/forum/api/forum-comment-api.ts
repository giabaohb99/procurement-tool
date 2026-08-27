import { apiDelete, apiGet, apiPost } from '@/core/api'
import type { MentionPerson } from '@/shared/ui/mention-input'

/**
 * Bình luận của bài viết diễn đàn — đi qua bộ máy bình luận DÙNG CHUNG
 * `/api/comments` (CR-031/033) với entity cố định `forum_post`: backend đã có
 * nhánh kiểm ĐỐI TƯỢNG XEM của bài trong `resolve_doc`, chuông "được nhắc tên" /
 * "bình luận mới" cũng đi chung đường đó, phía này không phải làm gì thêm.
 *
 * Không import từ `modules/procurement` (luật: module không mượn ruột module
 * khác) — kiểu dữ liệu là hợp đồng của API chung nên khai lại ở đây.
 */

export interface ForumCommentFile {
  link_id: number
  filename: string
  url: string
  content_type: string
  size: number
  is_image: boolean
}

export interface ForumCommentMention {
  user_id: number
  name: string
}

export interface ForumComment {
  id: number
  entity: string
  entity_id: number
  body: string
  parent_id: number
  author_id: number
  author_name: string
  author_code: string
  author_avatar: string
  created_at: string
  can_delete: boolean
  like_count: number
  liked: boolean
  /** Chỉ bình luận GỐC mới mang số này. */
  reply_count?: number
  reply_to_user_id: number
  reply_to_name: string
  mentions: ForumCommentMention[]
  files: ForumCommentFile[]
}

/** Một trang bình luận gốc, cũ → mới; phản hồi tải riêng khi bung. */
export interface ForumCommentPage {
  items: ForumComment[]
  total: number
  total_roots: number
  older_count: number
  oldest_id: number
}

const COMMENT_URL = '/api/comments'
const ENTITY = 'forum_post'

export function fetchPostComments(postId: number, beforeId = 0): Promise<ForumCommentPage> {
  return apiGet<ForumCommentPage>(COMMENT_URL, {
    params: {
      entity: ENTITY,
      entity_id: postId,
      limit: 10,
      before_id: beforeId || undefined,
    },
  })
}

export function fetchCommentReplies(commentId: number): Promise<ForumComment[]> {
  return apiGet<ForumComment[]>(`${COMMENT_URL}/${commentId}/replies`)
}

/** Gợi ý người để `@`: chưa gõ thì chỉ người dính tới bài, gõ rồi thì cả công ty. */
export function searchMentionablePeople(postId: number, q = ''): Promise<MentionPerson[]> {
  return apiGet<MentionPerson[]>(`${COMMENT_URL}/mentionable`, {
    params: { entity: ENTITY, entity_id: postId, q },
  })
}

/** Tệp đính kèm bình luận tải TRƯỚC, lấy `file_id` rồi mới gửi kèm (khuôn CR-033). */
export function uploadCommentFiles(
  files: File[],
): Promise<{ file_id: number; filename: string }[]> {
  const body = new FormData()
  body.append('entity', 'comment')
  files.forEach((file) => body.append('files', file))
  return apiPost<{ file_id: number; filename: string }[]>('/api/attachments/upload-file', body)
}

export function createPostComment(
  postId: number,
  body: string,
  parentId = 0,
  fileIds: number[] = [],
): Promise<ForumComment> {
  return apiPost<ForumComment>(COMMENT_URL, {
    entity: ENTITY,
    entity_id: postId,
    body,
    parent_id: parentId,
    file_ids: fileIds,
  })
}

export function toggleCommentLike(commentId: number): Promise<{ liked: boolean; count: number }> {
  return apiPost<{ liked: boolean; count: number }>(`${COMMENT_URL}/${commentId}/like`, {})
}

/** Xóa bình luận của mình — bình luận gốc cuốn theo mọi phản hồi. */
export function deletePostComment(commentId: number): Promise<null> {
  return apiDelete<null>(`${COMMENT_URL}/${commentId}`)
}
