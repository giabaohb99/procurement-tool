import { describe, expect, it } from 'vitest'

import { toRoutePattern } from './route-pattern'

describe('toRoutePattern', () => {
  it('replaces router param values with :name', () => {
    expect(toRoutePattern('/procurement/purchase-orders/129', { id: '129' })).toBe('/procurement/purchase-orders/:id')
    expect(toRoutePattern('/x/abc-slug/y', { slug: 'abc-slug' })).toBe('/x/:slug/y')
  })

  it('still masks numbers and uuids when no params are given', () => {
    expect(toRoutePattern('/a/42/b/550e8400-e29b-41d4-a716-446655440000')).toBe('/a/:id/b/:id')
  })

  it('never keeps the query string or hash', () => {
    const out = toRoutePattern('/procurement/purchase-requests?q=nguyen#frag')
    expect(out).toBe('/procurement/purchase-requests')
    expect(out).not.toContain('nguyen')
  })

  it('masks segments with characters the backend would reject', () => {
    expect(toRoutePattern('/search/Nguy%E1%BB%85n')).toBe('/search/:id')
    expect(toRoutePattern('/search/Nguyễn')).toBe('/search/:id')
  })

  it('truncates to 120 chars and keeps root for empty input', () => {
    expect(toRoutePattern(`/${'a'.repeat(500)}`).length).toBe(120)
    expect(toRoutePattern('')).toBe('/')
    expect(toRoutePattern('/')).toBe('/')
  })

  it('does not treat a splat param as a literal value', () => {
    expect(toRoutePattern('/files/secret', { '*': 'secret' })).toBe('/files/secret')
  })

  it('always yields a string the backend regex accepts', () => {
    const out = toRoutePattern('/a b/ü/..//%zz/<script>', {})
    expect(out).toMatch(/^\/[A-Za-z0-9/_:\-.]*$/)
  })
})
