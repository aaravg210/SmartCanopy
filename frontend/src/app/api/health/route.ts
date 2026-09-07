import { NextResponse } from 'next/server'

const BACKEND = 'http://138.2.213.17:8000'

export async function GET() {
  try {
    const res = await fetch(`${BACKEND}/api/health`)
    const data = await res.text()
    return new NextResponse(data, {
      status: res.status,
      headers: { 'Content-Type': 'application/json' },
    })
  } catch {
    return NextResponse.json({ detail: 'Backend unreachable' }, { status: 502 })
  }
}
