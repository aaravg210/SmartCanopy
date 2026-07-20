import Link from 'next/link'

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-green-50 to-white flex flex-col">
      {/* Header */}
      <header className="px-6 py-5 flex items-center gap-3 border-b border-green-100 bg-white/80 backdrop-blur-sm sticky top-0 z-10">
        <div className="w-9 h-9 rounded-lg bg-green-600 flex items-center justify-center shrink-0">
          <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 3L5 10h3l-3 5h3l-4 6h16l-4-6h3l-3-5h3L12 3z" />
            <rect x="10.5" y="21" width="3" height="3" rx="0.5" />
          </svg>
        </div>
        <div>
          <h1 className="font-semibold text-gray-900 leading-tight">SmartCanopy</h1>
          <p className="text-xs text-green-700">Powered by Our City Forest</p>
        </div>
      </header>

      {/* Hero */}
      <section className="flex-1 flex flex-col items-center justify-center text-center px-6 py-20">
        <div className="max-w-xl">
          <span className="inline-block text-xs font-semibold uppercase tracking-widest text-green-700 bg-green-100 px-3 py-1 rounded-full mb-6">
            Bay Area Free Tree Program
          </span>

          <h2 className="text-4xl sm:text-5xl font-bold text-gray-900 leading-tight mb-5">
            Find the perfect spot for a <span className="text-green-600">free tree</span> on your street
          </h2>

          <p className="text-lg text-gray-600 mb-8">
            Enter your address and SmartCanopy uses satellite imagery to identify ideal
            planting locations — then Our City Forest plants a free tree there for you.
          </p>

          <Link
            href="/map"
            className="inline-flex items-center gap-2 bg-green-600 hover:bg-green-700 text-white font-semibold px-8 py-4 rounded-xl text-lg transition-colors shadow-lg shadow-green-200"
          >
            Find planting sites near me
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
            </svg>
          </Link>

          <p className="mt-4 text-sm text-gray-400">
            Works for San Jose, Sunnyvale, and surrounding Bay Area cities
          </p>
        </div>
      </section>

      {/* How it works */}
      <section className="bg-white border-t border-green-100 px-6 py-16">
        <div className="max-w-3xl mx-auto">
          <h3 className="text-xl font-semibold text-gray-900 text-center mb-10">How it works</h3>
          <div className="grid sm:grid-cols-3 gap-8">
            {[
              {
                step: '1',
                icon: '📍',
                title: 'Enter your address',
                desc: 'Type any Bay Area address. We analyze a 100m radius using NAIP satellite imagery.',
              },
              {
                step: '2',
                icon: '🛰️',
                title: 'AI finds planting sites',
                desc: 'Our computer vision pipeline detects gaps in canopy, checks slope and NDVI, and filters out roads and buildings.',
              },
              {
                step: '3',
                icon: '🌳',
                title: 'Get a free tree',
                desc: "Select a site, choose a species from OCF's approved list, and request free planting — Our City Forest does the rest.",
              },
            ].map(({ step, icon, title, desc }) => (
              <div key={step} className="text-center">
                <div className="text-3xl mb-3">{icon}</div>
                <p className="text-xs font-semibold text-green-600 uppercase tracking-wide mb-1">Step {step}</p>
                <h4 className="font-semibold text-gray-900 mb-2">{title}</h4>
                <p className="text-sm text-gray-500">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-gray-100 px-6 py-6 text-center">
        <p className="text-xs text-gray-400">
          SmartCanopy is an independent tool supporting urban forestry in the Bay Area.{' '}
          <a href="https://www.ourcityforest.org" target="_blank" rel="noopener noreferrer" className="text-green-600 hover:underline">
            Our City Forest
          </a>{' '}
          · Tree availability subject to change · Not affiliated with VTA or the City of San Jose
        </p>
      </footer>
    </main>
  )
}
