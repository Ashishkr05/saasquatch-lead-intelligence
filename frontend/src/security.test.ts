import { describe, expect, it } from 'vitest'
import { safeWebsiteUrl } from './security'

describe('safeWebsiteUrl', () => {
  it('allows absolute HTTP and HTTPS company links', () => {
    expect(safeWebsiteUrl('https://example.com/about')).toBe('https://example.com/about')
    expect(safeWebsiteUrl('http://example.com')).toBe('http://example.com/')
  })

  it('rejects script, data, relative, and malformed links', () => {
    expect(safeWebsiteUrl('javascript:alert(1)')).toBeNull()
    expect(safeWebsiteUrl('data:text/html,bad')).toBeNull()
    expect(safeWebsiteUrl('/relative')).toBeNull()
    expect(safeWebsiteUrl('not a url')).toBeNull()
    expect(safeWebsiteUrl(null)).toBeNull()
  })
})
