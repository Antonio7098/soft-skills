import { createContext, useContext, type ReactNode } from 'react';
import type { DataProvider } from './provider';
import { switchingDataProvider } from './switching-provider';

// ---------------------------------------------------------------------------
// React context — injects a DataProvider into the component tree.
// Default to switching provider (tries real API, falls back to mock).
// ---------------------------------------------------------------------------

const DataContext = createContext<DataProvider>(switchingDataProvider);

interface DataProviderProps {
  readonly provider?: DataProvider;
  readonly children: ReactNode;
}

export function DataProviderProvider({ provider = switchingDataProvider, children }: DataProviderProps) {
  return <DataContext.Provider value={provider}>{children}</DataContext.Provider>;
}

export function useData(): DataProvider {
  return useContext(DataContext);
}