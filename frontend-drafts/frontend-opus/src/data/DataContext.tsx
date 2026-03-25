import { createContext, useContext, type ReactNode } from 'react';
import type { DataProvider } from './provider';
import { mockDataProvider } from './mock-provider';

// ---------------------------------------------------------------------------
// React context — injects a DataProvider into the component tree.
// Default to mock; swap via <DataProviderProvider value={apiDataProvider}>.
// ---------------------------------------------------------------------------

const DataContext = createContext<DataProvider>(mockDataProvider);

interface DataProviderProps {
  readonly provider?: DataProvider;
  readonly children: ReactNode;
}

export function DataProviderProvider({ provider = mockDataProvider, children }: DataProviderProps) {
  return <DataContext.Provider value={provider}>{children}</DataContext.Provider>;
}

export function useData(): DataProvider {
  return useContext(DataContext);
}
