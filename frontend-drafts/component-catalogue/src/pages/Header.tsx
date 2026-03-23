import React, { useState } from 'react';
import { Button } from '@/ui/components/Button';
import { Badge } from '@/ui/components/Badge';
import { categories, sources } from '@/lib/componentLoader';
import { Search, Filter, Moon, Sun } from 'lucide-react';

interface HeaderProps {
  selectedCategory: string;
  selectedSource: string;
  searchQuery: string;
  onCategoryChange: (category: string) => void;
  onSourceChange: (source: string) => void;
  onSearchChange: (query: string) => void;
  onThemeToggle: () => void;
  isDarkTheme: boolean;
}

export function Header({
  selectedCategory,
  selectedSource,
  searchQuery,
  onCategoryChange,
  onSourceChange,
  onSearchChange,
  onThemeToggle,
  isDarkTheme
}: HeaderProps) {
  return (
    <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 sticky top-0 z-50">
      <div className="container mx-auto px-4 py-4">
        <div className="flex flex-col lg:flex-row gap-4 items-start lg:items-center justify-between">
          {/* Title */}
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold">Component Catalogue</h1>
            <Badge variant="secondary">
              {sources.length} Sources
            </Badge>
          </div>

          {/* Search */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
            <input
              type="text"
              placeholder="Search components..."
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>

          {/* Controls */}
          <div className="flex items-center gap-3">
            {/* Category Filter */}
            <select
              value={selectedCategory}
              onChange={(e) => onCategoryChange(e.target.value)}
              className="px-3 py-2 border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="">All Categories</option>
              {categories.map(category => (
                <option key={category} value={category}>{category}</option>
              ))}
            </select>

            {/* Source Filter */}
            <select
              value={selectedSource}
              onChange={(e) => onSourceChange(e.target.value)}
              className="px-3 py-2 border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="">All Sources</option>
              {sources.map(source => (
                <option key={source} value={source}>{source}</option>
              ))}
            </select>

            {/* Theme Toggle */}
            <Button
              variant="ghost"
              size="icon"
              onClick={onThemeToggle}
              className="rounded-full"
            >
              {isDarkTheme ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </Button>
          </div>
        </div>

        {/* Active Filters */}
        {(selectedCategory || selectedSource || searchQuery) && (
          <div className="flex flex-wrap gap-2 mt-3">
            {selectedCategory && (
              <Badge variant="outline" className="cursor-pointer" onClick={() => onCategoryChange('')}>
                Category: {selectedCategory} ×
              </Badge>
            )}
            {selectedSource && (
              <Badge variant="outline" className="cursor-pointer" onClick={() => onSourceChange('')}>
                Source: {selectedSource} ×
              </Badge>
            )}
            {searchQuery && (
              <Badge variant="outline" className="cursor-pointer" onClick={() => onSearchChange('')}>
                Search: {searchQuery} ×
              </Badge>
            )}
          </div>
        )}
      </div>
    </header>
  );
}
