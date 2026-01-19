# SmartCanopy Frontend

Interactive map-based UI for the SmartCanopy urban tree planting AI system.

## Features

- **3-Tier Map System**
  - **Tier 1 (City)**: U.S. cities color-coded by tree canopy coverage
  - **Tier 2 (Neighborhood)**: Heatmap showing planting need by area
  - **Tier 3 (Street)**: Satellite imagery with AI-detected planting sites

- **CV Analysis Integration**: Enter any address to run computer vision analysis
- **AI Agent Chat**: WebSocket-powered chat with SmartCanopy AI
- **Site Details**: View characteristics, get species recommendations

## Prerequisites

- Node.js 18+ and npm
- Mapbox account and access token
- Backend API running at localhost:8000

## Setup

1. Install dependencies:
```bash
npm install
```

2. Create `.env.local` from the example:
```bash
cp .env.example .env.local
```

3. Add your Mapbox token to `.env.local`:
```
NEXT_PUBLIC_MAPBOX_TOKEN=pk.your_token_here
NEXT_PUBLIC_API_URL=http://localhost:8000
```

4. Start the development server:
```bash
npm run dev
```

5. Open http://localhost:3000

## Architecture

```
src/
├── app/                 # Next.js App Router pages
├── components/
│   ├── map/            # Map components (MapContainer, layers)
│   ├── panels/         # Side panels (SiteDetail, Filters)
│   ├── chat/           # Chat components
│   └── ui/             # Reusable UI components
├── stores/             # Zustand state stores
├── lib/
│   ├── api/           # API client functions
│   └── mapbox/        # Mapbox configuration
├── types/              # TypeScript interfaces
└── data/mock/          # Mock data for Tier 1/2
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

## Backend Integration

The frontend connects to these backend endpoints:

| Endpoint | Purpose |
|----------|---------|
| `POST /api/cv/analyze` | Run CV analysis on address |
| `GET /api/cv/analysis/{id}` | Get analysis results |
| `WS /api/agent/ws/{id}` | WebSocket chat streaming |
| `GET /api/species/search` | Search tree species |

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Maps**: Mapbox GL JS
- **State**: Zustand
- **Styling**: Tailwind CSS
- **Language**: TypeScript
