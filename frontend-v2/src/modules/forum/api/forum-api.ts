import { apiDelete, apiGet, apiPost } from '@/core/api'

import type {
  ForumFeedPage,
  ForumPost,
  ForumPostLiker,
  ForumUploadedFile,
  NewForumPost,
} from '../types/forum-post'

const FORUM_URL = '/api/forum'
const ATTACHMENT_URL = '/api/attachments'

/**
 * Một trang feed, mới → cũ. `beforeId` = id nhỏ nhất đang hiện trên màn
 * (0 = trang đầu) — con trỏ, không phải số trang.
 */
export function fetchForumFeed(beforeId: number, limit = 20): Promise<ForumFeedPage> {
  return apiGet<ForumFeedPage>(`${FORUM_URL}/posts`, {
    params: { limit, before_id: beforeId },
  })
}

/** Tủ bài viết của một người — trang CHÍNH MÌNH backend trả cả bài bị ẩn. */
export function fetchUserPosts(
  userId: number,
  beforeId: number,
  limit = 20,
): Promise<ForumFeedPage> {
  return apiGet<ForumFeedPage>(`${FORUM_URL}/users/${userId}/posts`, {
    params: { limit, before_id: beforeId },
  })
}

/** Một bài viết — 403 khi người xem ngoài đối tượng xem của bài. */
export function fetchForumPost(id: number): Promise<ForumPost> {
  return apiGet<ForumPost>(`${FORUM_URL}/posts/${id}`)
}

/**
 * Tải ảnh/video lên TRƯỚC, giữ `file_id`, rồi mới gắn vào bài lúc đăng (khuôn
 * tải-trước-gắn-sau của phiếu hỗ trợ). Backend kiểm đuôi (ảnh + mp4/webm,
 * D-Q3) và trần 50MB/tệp theo `FILE_POLICY` entity `forum_post`.
 */
export function uploadForumMedia(files: File[]): Promise<ForumUploadedFile[]> {
  const body = new FormData()
  body.append('entity', 'forum_post')
  files.forEach((file) => body.append('files', file))
  return apiPost<ForumUploadedFile[]>(`${ATTACHMENT_URL}/upload-file`, body)
}

export function createForumPost(input: NewForumPost): Promise<ForumPost> {
  return apiPost<ForumPost>(`${FORUM_URL}/posts`, input)
}

/** Xóa bài của CHÍNH MÌNH (admin ẩn/xóa là F5, đi đường khác). */
export function deleteForumPost(id: number): Promise<null> {
  return apiDelete<null>(`${FORUM_URL}/posts/${id}`)
}

/** Bật/tắt thích một bài — backend trả trạng thái + số đếm SAU khi bấm (D-Q6: không chuông). */
export function toggleForumPostLike(id: number): Promise<{ liked: boolean; count: number }> {
  return apiPost<{ liked: boolean; count: number }>(`${FORUM_URL}/posts/${id}/like`, {})
}

/** Ai đã thích bài — mở khi bấm vào số đếm. */
export function fetchForumPostLikes(id: number): Promise<ForumPostLiker[]> {
  return apiGet<ForumPostLiker[]>(`${FORUM_URL}/posts/${id}/likes`)
}

// ── Kiểm duyệt (F5) — chỉ tài khoản có grant `forum_post` gọi được, người
// thường ăn 403; FE gác nút bằng `post.can_moderate`.

/** Ẩn bài — lý do BẮT BUỘC (QĐ-D1), backend 400 nếu để trống. */
export function hideForumPost(id: number, reason: string): Promise<null> {
  return apiPost<null>(`${FORUM_URL}/posts/${id}/hide`, { reason })
}

/** Khôi phục bài đã ẩn về feed — không cần lý do. */
export function restoreForumPost(id: number): Promise<null> {
  return apiPost<null>(`${FORUM_URL}/posts/${id}/restore`, {})
}

/** Xóa bài (kiểm duyệt) — bài biến khỏi mọi mắt nhưng backend giữ dòng đối soát. */
export function removeForumPost(id: number, reason: string): Promise<null> {
  return apiPost<null>(`${FORUM_URL}/posts/${id}/remove`, { reason })
}
