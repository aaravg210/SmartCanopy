import { NextRequest, NextResponse } from 'next/server'

const BACKEND = 'http://138.2.213.17:8000'

export async function GET() {
  return NextResponse.json({ route: 'cv/analyze', method: 'GET works' })
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.text()
    const res = await fetch(`${BACKEND}/api/cv/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body,
    })
    const data = await res.text()
    return new NextResponse(data, {
      status: res.status,
      headers: { 'Content-Type': 'application/json' },
    })
  } catch (e) {
    return NextResponse.json({ detail: String(e) }, { status: 502 })
  }
}
