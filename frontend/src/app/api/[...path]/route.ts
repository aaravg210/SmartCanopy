import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = 'http://138.2.213.17:8000'

async function proxyRequest(request: NextRequest, params: { path: string[] }) {
  const targetPath = '/api/' + params.path.join('/')
  const targetUrl = `${BACKEND_URL}${targetPath}${request.nextUrl.search}`

  const headers = new Headers()
  const contentType = request.headers.get('content-type')
  if (contentType) headers.set('content-type', contentType)

  const body =
    request.method !== 'GET' && request.method !== 'HEAD'
      ? await request.arrayBuffer()
      : undefined

  try {
    const response = await fetch(targetUrl, {
      method: request.method,
      headers,
      body: body ? Buffer.from(body) : undefined,
    })

    const responseBody = await response.arrayBuffer()
    const responseHeaders = new Headers()
    const ct = response.headers.get('content-type')
    if (ct) responseHeaders.set('content-type', ct)

    return new NextResponse(responseBody, {
      status: response.status,
      headers: responseHeaders,
    })
  } catch (err) {
    return NextResponse.json({ detail: 'Backend unreachable' }, { status: 502 })
  }
}

export async function GET(request: NextRequest, { params }: { params: { path: string[] } }) {
  return proxyRequest(request, params)
}

export async function POST(request: NextRequest, { params }: { params: { path: string[] } }) {
  return proxyRequest(request, params)
}

export async function PUT(request: NextRequest, { params }: { params: { path: string[] } }) {
  return proxyRequest(request, params)
}

export async function DELETE(request: NextRequest, { params }: { params: { path: string[] } }) {
  return proxyRequest(request, params)
}
