import { QueryClient } from '@tanstack/react-query'
import { describe, expect, it } from 'vitest'

import { queryKeys } from '@/shared/constants/query-keys'
import { invalidateSelfContactQueries } from './use-my-contact'

/**
 * Tự sửa liên hệ xong phải nạp lại MỌI chỗ đang hiện liên hệ của người đó
 * (bao-CR-508). Sót một khóa thì chỗ đó hiện số cũ tới lúc hết `staleTime`, và
 * người dùng tưởng lưu chưa ăn — rồi bấm Lưu thêm lần nữa.
 *
 * Kiểm trên QueryClient THẬT (không giả `invalidateQueries`): thứ cần canh là
 * luật khớp tiền tố của TanStack với đúng các khóa trong `query-keys.ts`.
 */
function seededClient() {
  const client = new QueryClient()
  const keys = {
    mine: queryKeys.hr.myEmployee(),
    myContacts: queryKeys.hr.myEmployeeContacts(),
    detail: queryKeys.hr.employee(5),
    detailContacts: queryKeys.hr.employeeContacts(5),
    list: queryKeys.hr.employees({ page: 2, search: 'An' }),
    authMe: queryKeys.auth.me(),
    otherDetail: queryKeys.hr.employee(6),
    departments: queryKeys.hr.departments(),
  }
  for (const key of Object.values(keys)) client.setQueryData(key, { seeded: true })
  const isStale = (key: readonly unknown[]) => client.getQueryState(key)?.isInvalidated ?? false
  return { client, keys, isStale }
}

describe('invalidateSelfContactQueries', () => {
  it('refreshes the personal page, the HR detail, employee lists and the session', async () => {
    const { client, keys, isStale } = seededClient()

    await invalidateSelfContactQueries(client, 5)

    expect(isStale(keys.mine)).toBe(true)
    expect(isStale(keys.myContacts)).toBe(true)
    expect(isStale(keys.detail)).toBe(true)
    expect(isStale(keys.detailContacts)).toBe(true)
    expect(isStale(keys.list)).toBe(true)
    expect(isStale(keys.authMe)).toBe(true)
  })

  it("leaves other people's profiles and unrelated HR data alone", async () => {
    const { client, keys, isStale } = seededClient()

    await invalidateSelfContactQueries(client, 5)

    expect(isStale(keys.otherDetail)).toBe(false)
    expect(isStale(keys.departments)).toBe(false)
  })

  it('does not match every profile when the account has no linked employee (id 0)', async () => {
    const { client, keys, isStale } = seededClient()

    await invalidateSelfContactQueries(client, 0)

    expect(isStale(keys.detail)).toBe(false)
    expect(isStale(keys.otherDetail)).toBe(false)
  })
})
