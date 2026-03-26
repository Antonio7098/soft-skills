import { LayoutDashboard, MessageSquare, FolderOpen, TrendingUp, Settings, Sparkles } from 'lucide-react';
import type { NavRoute } from '@/types';

export const NAV_ROUTES: NavRoute[] = [
  { path: '/', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/practice', label: 'Practice', icon: MessageSquare },
  { path: '/generate', label: 'Generate', icon: Sparkles },
  { path: '/collections', label: 'Collections', icon: FolderOpen },
  { path: '/progress', label: 'Progress', icon: TrendingUp },
  { path: '/settings', label: 'Settings', icon: Settings },
];
