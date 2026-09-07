import { NextRequest, NextResponse } from 'next/server'

const BACKEND = 'http://138.2.213.17:8000'

export async function GET(request: NextRequest) {
  try {
    const qs = request.nextUrl.search
    const res = await fetch(`${BACKEND}/api/species/search${qs}`)
    const data = await res.text()
    return new NextResponse(data, {
      status: res.status,
      headers: { 'Content-Type': 'application/json' },
    })
  } catch {
    return NextResponse.json({ detail: 'Backend unreachable' }, { status: 502 })
  }
}
