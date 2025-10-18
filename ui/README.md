## Installation

```bash
npm install
```

## Running

```bash
npm run dev
```

## Project Structure

```
src/
├── assets/                # Static assets (images, animations, etc.)
├── components/            # Reusable UI building blocks
│   ├── AuthShell/         # Auth-specific wrappers
│   ├── auth/              # Route guards and auth-only components
│   ├── player/            # Player-focused UI widgets
│   ├── team/              # Team-focused UI widgets
│   └── ui/                # Primitive UI elements (buttons, inputs, etc.)
├── hooks/                 # React hooks and context providers
├── layouts/               # Application and auth layouts
├── lib/                   # Low-level setup (Supabase client, config)
├── pages/                 # Route-level views
├── router/                # Centralised routing configuration
├── services/              # Supabase data-access layer
├── styles/                # Global styles and themes
├── transforms/            # Helpers that shape DB rows into view models
├── types/                 # Shared TypeScript types
└── utils/                 # Generic helpers/utilities
```

## Building

```bash
npm run build
```

## Linting

```bash
npm run lint
```

## Formatting

```bash
npm run format
```
