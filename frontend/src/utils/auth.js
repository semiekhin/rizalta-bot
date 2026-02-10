const TOKEN_KEY = 'rizalta_access_token'
const LEVEL_KEY = 'rizalta_access_level'

export function captureTokenFromURL() {
  const params = new URLSearchParams(window.location.search)
  const token = params.get('token')
  if (token) {
    localStorage.setItem(TOKEN_KEY, token)
    window.history.replaceState({}, '', window.location.pathname)
  }
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY) || ''
}

export function getAccessLevel() {
  return localStorage.getItem(LEVEL_KEY) || 'public'
}

export function isWhitelisted() {
  return getAccessLevel() === 'white'
}

export async function verifyAccess() {
  const token = getToken()
  if (!token) {
    localStorage.setItem(LEVEL_KEY, 'public')
    return 'public'
  }

  try {
    const res = await fetch('/api/access/check', {
      headers: { 'X-Access-Token': token }
    })
    const data = await res.json()
    localStorage.setItem(LEVEL_KEY, data.level)
    return data.level
  } catch {
    localStorage.setItem(LEVEL_KEY, 'public')
    return 'public'
  }
}

export function authFetch(url, options = {}) {
  const token = getToken()
  if (token) {
    options.headers = {
      ...options.headers,
      'X-Access-Token': token,
    }
  }
  return fetch(url, options)
}
