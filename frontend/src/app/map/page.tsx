'use client'

import dynamic from 'next/dynamic'
import { Suspense } from 'react'

// Dynamic import to avoid SSR issues with Mapbox
const MapContainer = dynamic(
  () => import('@/components/map/MapContainer'),
  {
    ssr: false,
    loading: () => <MapLoadingState />,
  }
)

function MapLoadingState() {
  return (
    <div className="w-full h-screen flex items-center justify-center bg-gray-100">
      <div className="text-center">
        <div className="w-12 h-12 border-4 border-canopy-500 border-t-transparent rounded-full spinner mx-auto mb-4" />
        <p className="text-gray-600">Loading map...</p>
      </div>
    </div>
  )
}

export default function MapPage() {
  return (
    <main className="relative w-full h-screen">
      <Suspense fallback={<MapLoadingState />}>
        <MapContainer />
      </Suspense>
    </main>
  )
}
