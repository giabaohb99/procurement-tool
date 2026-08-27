import { describe, expect, it } from 'vitest'

import { readLastAudience, saveLastAudience } from './last-audience'

function fakeStorage(initial: Record<string, string> = {}) {
  const store = new Map(Object.entries(initial))
  return {
    getItem: (key: string) => store.get(key) ?? null,
    setItem: (key: string, value: string) => void store.set(key, value),
  }
}

describe('readLastAudience / saveLastAudience', () => {
  it('chưa từng đăng thì mặc định Toàn tập đoàn (3)', () => {
    expect(readLastAudience(fakeStorage())).toBe(3)
  })

  it('nhớ lại đúng lựa chọn của lần đăng trước', () => {
    const storage = fakeStorage()
    saveLastAudience(1, storage)
    expect(readLastAudience(storage)).toBe(1)
  })

  it('giá trị rác trong localStorage thì về mặc định chứ không NaN', () => {
    expect(readLastAudience(fakeStorage({ 'forum.last-audience': 'abc' }))).toBe(3)
    expect(readLastAudience(fakeStorage({ 'forum.last-audience': '7' }))).toBe(3)
  })
})
