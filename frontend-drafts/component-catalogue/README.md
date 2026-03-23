# Component Catalogue

A unified catalogue showcasing all components from the frontend drafts in the soft-skills project.

## Overview

This component catalogue aggregates and displays components from multiple frontend implementations:
- **frontend-gemini**: React + TypeScript + Tailwind CSS
- **frontend-healer**: React + TypeScript + Custom Design System
- **frontend-hunter**: React + TypeScript + CSS Variables
- **frontend-minimax**: React + TypeScript + Component Library
- **frontend-opus**: React + TypeScript + Design System

## Features

- **Unified View**: Browse all components from different frontend drafts in one place
- **Filtering**: Filter by component category, source project, or search terms
- **Live Previews**: See rendered components with default props
- **Component Metadata**: View descriptions, categories, and source information
- **Theme Support**: Toggle between light and dark themes
- **Responsive Design**: Works on desktop and mobile devices

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

1. Navigate to the component-catalogue directory:
```bash
cd soft-skills/frontend-drafts/component-catalogue
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

4. Open [http://localhost:5173](http://localhost:5173) in your browser.

### Build

To create a production build:
```bash
npm run build
```

## Project Structure

```
component-catalogue/
├── src/
│   ├── ui/components/     # Catalogue UI components
│   ├── pages/              # Main application pages
│   ├── lib/                # Component loading logic
│   ├── utils/              # Utility functions
│   ├── App.tsx             # Main application
│   ├── main.tsx            # Entry point
│   └── index.css           # Global styles
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## Component Loading

The catalogue dynamically imports components from each frontend draft using React.lazy() and dynamic imports. This approach:

- Keeps the bundle size small
- Allows components to be loaded on-demand
- Provides clear separation between the catalogue and component sources

### Adding New Components

To add a new component to the catalogue:

1. Update `src/lib/componentLoader.ts` with the new component import
2. Add the component to the `componentRegistry` array with appropriate metadata
3. The component will automatically appear in the catalogue

### Component Metadata

Each component in the registry includes:

- `name`: Component name
- `description`: Brief description of the component
- `component`: The lazy-loaded React component
- `category`: Component category (Actions, Layout, Display, etc.)
- `source`: Which frontend draft it comes from
- `props`: Default props for preview

## Categories

Components are organized into categories:

- **Actions**: Buttons, forms, interactive elements
- **Layout**: Cards, containers, structural components
- **Display**: Badges, avatars, status indicators
- **Navigation**: Menus, breadcrumbs, links
- **Feedback**: Modals, alerts, notifications

## Sources

Components are sourced from different frontend implementations, each with their own design philosophy:

- **frontend-gemini**: Modern, clean design with Tailwind CSS
- **frontend-healer**: Token-based design system with CSS variables
- **frontend-hunter**: Elevated design with hover effects
- **frontend-minimax**: Minimal, functional components
- **frontend-opus**: Corporate design system

## Development

### Adding New Frontend Sources

To add a new frontend draft to the catalogue:

1. Create a new component import section in `componentLoader.ts`
2. Add the components to the registry with the appropriate source identifier
3. The new source will automatically appear in the source filter dropdown

### Customizing the Catalogue

The catalogue can be customized by modifying:

- **Styling**: Update `src/index.css` for theme and layout changes
- **Components**: Modify UI components in `src/ui/components/`
- **Layout**: Update `src/App.tsx` and page components
- **Data**: Modify `src/lib/componentLoader.ts` for component registry changes

## Technical Details

- **Framework**: React 19 with TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS with custom theme
- **Icons**: Lucide React
- **State Management**: React hooks (useState, useEffect)

## Contributing

When adding new components or making changes:

1. Ensure components are properly typed with TypeScript
2. Follow the existing code style and patterns
3. Test components work correctly in the catalogue
4. Update documentation as needed

## Troubleshooting

### Common Issues

1. **Components not loading**: Check that the import paths in `componentLoader.ts` are correct
2. **Styling issues**: Verify that CSS variables and Tailwind classes are properly configured
3. **Type errors**: Ensure all components have proper TypeScript definitions

### Development Tips

- Use the browser dev tools to inspect component loading
- Check the Network tab for dynamic import failures
- Verify CSS variables are being applied correctly
- Test with different screen sizes for responsive behavior
