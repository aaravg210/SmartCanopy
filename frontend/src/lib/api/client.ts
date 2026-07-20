/**
 * API Client for SmartCanopy backend
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public details?: unknown
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export async function apiClient<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_URL}${endpoint}`

  let response: Response
  try {
    response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    })
  } catch (error) {
    // Network error - backend is likely not running
    throw new ApiError(
      'Cannot connect to the analysis server. Please try again in a moment.',
      0
    )
  }

  if (!response.ok) {
    let errorMessage = `API Error: ${response.status}`
    try {
      const errorData = await response.json()
      errorMessage = errorData.detail || errorData.message || errorMessage
    } catch {
      // Response wasn't JSON
    }
    throw new ApiError(errorMessage, response.status)
  }

  return response.json()
}

export function getWebSocketUrl(conversationId: string): string {
  const wsProtocol = API_URL.startsWith('https') ? 'wss' : 'ws'
  const wsHost = API_URL.replace(/^https?:\/\//, '')
  return `${wsProtocol}://${wsHost}/api/agent/ws/${conversationId}`
}

export { API_URL }
