import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { useTheme } from '@/providers/ThemeProvider';
import { Bell, User } from 'lucide-react';
import { Button } from '@/ui/components/Button';

export function AppLayout() {
  const { theme, setTheme } = useTheme();

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden">
      <Sidebar />
      <main className="flex-1 flex flex-col min-w-0">
        <header className="h-16 border-b border-border px-8 flex items-center justify-between bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 z-10 sticky top-0">
          <div className="flex-1" />
          <div className="flex items-center gap-4">
            <select 
              value={theme}
              onChange={(e) => setTheme(e.target.value as any)}
              className="bg-secondary text-secondary-foreground border-border rounded-md text-sm px-3 py-1.5 focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="professional">Professional</option>
              <option value="brutalist">Brutalist</option>
              <option value="neo-corporate">Neo Corporate</option>
            </select>
            
            <Button variant="ghost" size="icon" className="rounded-full">
              <Bell className="w-4 h-4" />
            </Button>
            <Button variant="secondary" size="icon" className="rounded-full">
              <User className="w-4 h-4" />
            </Button>
          </div>
        </header>
        
        <div className="flex-1 overflow-auto p-8">
          <div className="max-w-7xl mx-auto">
            <Outlet />
          </div>
        </div>
      </main>
    </div>
  );
}
