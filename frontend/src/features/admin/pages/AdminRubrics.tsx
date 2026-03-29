import { useEffect, useState } from 'react';
import { 
  Scale,
  Plus,
  Edit,
  ChevronRight,
  Layers,
} from 'lucide-react';
import { Card } from '@/design-system/primitives/Card';
import { Button } from '@/design-system/primitives/Button';
import { Badge } from '@/design-system/primitives/Badge';
import { LoadingState } from '@/design-system/patterns/LoadingState';
import { useData } from '@/data';
import { AdminPageShell, MetricCard, SearchInput } from '../components';
import type { RubricView, RubricAdminView } from '@/data/types';

export function AdminRubrics() {
  const dataProvider = useData();
  const [rubrics, setRubrics] = useState<RubricView[]>([]);
  const [selectedRubric, setSelectedRubric] = useState<RubricAdminView | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    setLoading(true);
    dataProvider.listRubrics()
      .then(setRubrics)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [dataProvider]);

  const handleSelectRubric = async (rubric: RubricView) => {
    try {
      const detail = await dataProvider.getRubric(rubric.rubric_id) as RubricAdminView;
      setSelectedRubric(detail);
    } catch (error) {
      console.error(error);
    }
  };

  const filteredRubrics = rubrics.filter((r) =>
    search ? r.name.toLowerCase().includes(search.toLowerCase()) : true
  );

  const families = new Set(rubrics.map((r) => r.family));
  const contentTypes = new Set(rubrics.map((r) => r.content_type));

  if (loading) {
    return (
      <AdminPageShell title="Rubrics" subtitle="Assessment criteria management">
        <LoadingState message="Loading rubrics..." />
      </AdminPageShell>
    );
  }

  return (
    <AdminPageShell
      title="Rubrics"
      subtitle="Manage assessment rubrics, criteria, and scoring configurations"
      actions={
        <Button icon={<Plus className="w-4 h-4" />}>
          New Rubric
        </Button>
      }
    >
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Total Rubrics"
          value={rubrics.length}
          icon={<Scale className="w-4 h-4" />}
        />
        <MetricCard
          label="Families"
          value={families.size}
          icon={<Layers className="w-4 h-4" />}
        />
        <MetricCard
          label="Content Types"
          value={contentTypes.size}
        />
        <MetricCard
          label="Total Criteria"
          value={selectedRubric?.criteria?.length || 0}
          subtitle="Select rubric to view"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="flex flex-col gap-4">
          <div className="flex items-center gap-3">
            <SearchInput
              value={search}
              onChange={setSearch}
              placeholder="Search rubrics..."
              className="flex-1"
            />
          </div>
          <div className="flex flex-col gap-2">
            {filteredRubrics.map((rubric) => (
              <div 
                key={rubric.rubric_id}
                onClick={() => handleSelectRubric(rubric)}
                className={`flex items-center gap-3 py-2.5 px-3 rounded-lg transition-colors cursor-pointer ${
                  selectedRubric?.rubric_id === rubric.rubric_id 
                    ? 'bg-accent/10 border border-accent/20' 
                    : 'hover:bg-surface-secondary/50'
                }`}
              >
                <div className="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center">
                  <Scale className="w-4 h-4 text-accent" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-body-sm font-medium text-content-primary truncate">
                    {rubric.name}
                  </p>
                  <p className="text-body-xs text-content-tertiary">
                    {rubric.family} · v{rubric.version}
                  </p>
                </div>
                <ChevronRight className="w-4 h-4 text-content-tertiary" />
              </div>
            ))}
            {filteredRubrics.length === 0 && (
              <p className="text-body-sm text-content-tertiary py-4 text-center">No rubrics found</p>
            )}
          </div>
        </Card>

        <Card className="lg:col-span-2 flex flex-col gap-4">
          {selectedRubric ? (
            <>
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-display text-body-md font-semibold text-content-primary">
                    {selectedRubric.name}
                  </h3>
                  <p className="text-body-xs text-content-tertiary">
                    {selectedRubric.family} · {selectedRubric.content_type} · v{selectedRubric.version}
                  </p>
                </div>
                <Button variant="secondary" size="sm" icon={<Edit className="w-4 h-4" />}>
                  Edit
                </Button>
              </div>

              <div className="flex flex-col gap-3">
                <h4 className="text-body-sm font-medium text-content-secondary">
                  Criteria ({selectedRubric.criteria?.length || 0})
                </h4>
                {selectedRubric.criteria?.map((criterion, idx) => (
                  <div 
                    key={criterion.criterion_ref}
                    className="p-3 rounded-lg bg-surface-secondary/50 border border-line"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <span className="w-5 h-5 rounded-full bg-accent/10 flex items-center justify-center text-body-xs font-medium text-accent">
                            {idx + 1}
                          </span>
                          <span className="text-body-sm font-medium text-content-primary">
                            {criterion.title}
                          </span>
                          {criterion.required && (
                            <Badge variant="error" size="sm">Required</Badge>
                          )}
                        </div>
                        <p className="text-body-xs text-content-secondary mt-1 ml-7">
                          {criterion.description}
                        </p>
                      </div>
                      <div className="text-right">
                        <span className="text-body-xs text-content-tertiary">Weight</span>
                        <p className="text-body-sm font-semibold text-content-primary">
                          {criterion.weight}
                        </p>
                      </div>
                    </div>
                    {criterion.levels && criterion.levels.length > 0 && (
                      <div className="mt-3 ml-7 flex gap-2">
                        {criterion.levels.map((level) => (
                          <Badge key={level.level} variant="default" size="sm">
                            L{level.level}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
                {(!selectedRubric.criteria || selectedRubric.criteria.length === 0) && (
                  <p className="text-body-sm text-content-tertiary py-4 text-center">
                    No criteria defined
                  </p>
                )}
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center py-16">
              <p className="text-body-sm text-content-tertiary">
                Select a rubric to view details
              </p>
            </div>
          )}
        </Card>
      </div>
    </AdminPageShell>
  );
}
