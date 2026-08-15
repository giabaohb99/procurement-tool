import { useCallback, useMemo, useSyncExternalStore } from 'react'

import { useAuth } from '@/core/auth/use-auth'
import type { LocalCollection, SaveOptions } from '../store/local-collection'

/**
 * Lớp hook dùng chung cho mọi kho tạm của phân hệ Văn bản
 * (xem `store/local-collection.ts`).
 *
 * Khi backend có API: thay từng hàm ở đây bằng react-query, trang gọi vẫn giữ
 * nguyên cách dùng.
 */

/** Danh sách bản ghi. */
export function useCollectionItems<T extends { id: number }>(
  collection: LocalCollection<T>,
): T[] {
  return useSyncExternalStore(collection.subscribe, collection.getState).items
}

/** Một bản ghi theo id; `undefined` = id lạ hoặc đã bị xóa. */
export function useCollectionItem<T extends { id: number }>(
  collection: LocalCollection<T>,
  id?: number,
): T | undefined {
  const items = useCollectionItems(collection)
  return items.find((item) => item.id === id)
}

/** Lịch sử thao tác của MỘT bản ghi, mới nhất trước. */
export function useCollectionHistory<T extends { id: number }>(
  collection: LocalCollection<T>,
  id?: number,
) {
  const { history } = useSyncExternalStore(collection.subscribe, collection.getState)
  return useMemo(
    () => (id ? history.filter((entry) => entry.recordId === id) : []),
    [history, id],
  )
}

/** Lưu / xóa, đã gắn sẵn tên người đang đăng nhập vào lịch sử thao tác. */
export function useCollectionActions<T extends { id: number }>(
  collection: LocalCollection<T>,
) {
  const { user } = useAuth()
  const actor = user?.full_name ?? 'Không rõ'

  const save = useCallback(
    (values: Omit<T, 'id'>, id?: number, options?: SaveOptions) =>
      collection.save(values, actor, id, options),
    [collection, actor],
  )

  const remove = useCallback(
    (id: number) => collection.remove(id, actor),
    [collection, actor],
  )

  return { save, remove }
}
