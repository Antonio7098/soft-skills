import React, { useState, useEffect } from 'react';
import { Header } from '@/pages/Header';
import { ComponentGrid } from '@/pages/ComponentGrid';

function App() {
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedSource, setSelectedSource] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [isDarkTheme, setIsDarkTheme] = useState(false);

  useEffect(() => {
    // Check for system preference or saved preference
    const savedTheme = localStorage.getItem('theme');
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    
    if (savedTheme === 'dark' || (!savedTheme && systemPrefersDark)) {
      setIsDarkTheme(true);
      document.documentElement.setAttribute('data-theme', 'dark');
    }
  }, []);

  const handleThemeToggle = () => {
    const newTheme = !isDarkTheme;
    setIsDarkTheme(newTheme);
    document.documentElement.setAttribute('data-theme', newTheme ? 'dark' : 'light');
    localStorage.setItem('theme', newTheme ? 'dark' : 'light');
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Header
        selectedCategory={selectedCategory}
        selectedSource={selectedSource}
        searchQuery={searchQuery}
        onCategoryChange={setSelectedCategory}
        onSourceChange={setSelectedSource}
        onSearchChange={setSearchQuery}
        onThemeToggle={handleThemeToggle}
        isDarkTheme={isDarkTheme}
      />
      
      <main className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h2 className="text-3xl font-bold mb-2">Welcome to the Component Catalogue</h2>
          <p className="text-muted-foreground text-lg">
            Browse and explore components from all frontend drafts in one place.
          </p>
        </div>
        
        <ComponentGrid
          selectedCategory={selectedCategory}
          selectedSource={selectedSource}
          searchQuery={searchQuery}
        />
      </main>
    </div>
  );
}

export default App;
