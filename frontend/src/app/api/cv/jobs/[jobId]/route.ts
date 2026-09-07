import { NextRequest, NextResponse } from 'next/server'

const BACKEND = 'http://138.2.213.17:8000'

export async function GET(_request: NextRequest, { params }: { params: { jobId: string } }) {
  try {
    const res = await fetch(`${BACKEND}/api/cv/jobs/${params.jobId}`)
    const data = await res.text()
    return new NextResponse(data, {
      status: res.status,
      headers: { 'Content-Type': 'application/json' },
    })
  } catch {
    return NextResponse.json({ detail: 'Backend unreachable' }, { status: 502 })
  }
}
