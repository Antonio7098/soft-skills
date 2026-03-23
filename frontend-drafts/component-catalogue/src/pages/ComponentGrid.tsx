import React, { Suspense } from 'react';
import { componentRegistry, categories, sources } from '@/lib/componentLoader';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/ui/components/Card';
import { Badge } from '@/ui/components/Badge';
import { Button } from '@/ui/components/Button';

interface ComponentGridProps {
  selectedCategory?: string;
  selectedSource?: string;
  searchQuery?: string;
}

export function ComponentGrid({ 
  selectedCategory, 
  selectedSource, 
  searchQuery 
}: ComponentGridProps) {
  const filteredComponents = componentRegistry.filter(component => {
    const matchesCategory = !selectedCategory || component.category === selectedCategory;
    const matchesSource = !selectedSource || component.source === selectedSource;
    const matchesSearch = !searchQuery || 
      component.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      component.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      component.source.toLowerCase().includes(searchQuery.toLowerCase());
    
    return matchesCategory && matchesSource && matchesSearch;
  });

  const groupedComponents = filteredComponents.reduce((acc, component) => {
    const key = `${component.name}-${component.source}`;
    if (!acc[key]) {
      acc[key] = [];
    }
    acc[key].push(component);
    return acc;
  }, {} as Record<string, typeof componentRegistry>);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {Object.entries(groupedComponents).map(([key, components]) => {
        const component = components[0];
        const Component = component.component;
        
        return (
          <Card key={key} className="group hover:shadow-lg transition-all">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">{component.name}</CardTitle>
                <Badge variant="secondary">{component.source}</Badge>
              </div>
              <CardDescription>{component.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Component Preview */}
                <div className="min-h-[80px] p-4 border rounded-md bg-muted/50 flex items-center justify-center">
                  <Suspense fallback={<div className="text-sm text-muted-foreground">Loading...</div>}>
                    <Component {...component.props} />
                  </Suspense>
                </div>
                
                {/* Component Metadata */}
                <div className="flex flex-wrap gap-2">
                  <Badge variant="outline">{component.category}</Badge>
                  {components.length > 1 && (
                    <Badge variant="outline">{components.length} variants</Badge>
                  )}
                </div>
                
                {/* Actions */}
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" className="flex-1">
                    View Code
                  </Button>
                  <Button variant="ghost" size="sm">
                    Copy
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
      
      {filteredComponents.length === 0 && (
        <div className="col-span-full text-center py-12">
          <div className="text-muted-foreground">
            No components found matching your filters.
          </div>
        </div>
      )}
    </div>
  );
}
