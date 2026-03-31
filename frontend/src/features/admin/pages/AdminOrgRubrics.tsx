import { useEffect, useState } from 'react';
import { Plus, Edit, Trash2, X, Check, Scale, Globe } from 'lucide-react';
import { useAdminScope } from '@/auth';
import { Card } from '@/design-system/primitives/Card';
import { Button } from '@/design-system/primitives/Button';
import { Badge } from '@/design-system/primitives/Badge';
import { LoadingState } from '@/design-system/patterns/LoadingState';
import { EmptyState } from '@/design-system/patterns/EmptyState';
import { useData } from '@/data';
import { AdminPageShell, MetricCard, SearchInput } from '../components';
import type { OrgRubricView, RubricView } from '@/data/types';

type RubricWithScope = (OrgRubricView | (RubricView & { criteria?: string[] })) & { scope: 'global' | 'org' };

export function AdminOrgRubrics() {
  const { organisationId } = useAdminScope();
  const dataProvider = useData();
  const [rubrics, setRubrics] = useState<RubricWithScope[]>([]);
  const [selectedRubric, setSelectedRubric] = useState<RubricWithScope | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [newRubric, setNewRubric] = useState({
    rubric_id: '',
    name: '',
    family: 'soft_skills',
    content_type: 'prompt_item',
  });

  const refreshRubrics = async () => {
    if (!organisationId) return;
    setLoading(true);
    try {
      const [taxonomy, orgRubrics] = await Promise.all([
        dataProvider.getTaxonomy(),
        dataProvider.listOrgRubrics(organisationId),
      ]);

      // Merge global and org rubrics - org rubrics take precedence
      const orgRubricIds = new Set(orgRubrics.map((r) => r.rubric_id));
      const globalRubrics: RubricWithScope[] = taxonomy.rubrics
        .filter((r) => !orgRubricIds.has(r.rubric_id))
        .map((r) => ({ ...r, scope: 'global', criteria: [] }));
      const mergedOrgRubrics: RubricWithScope[] = orgRubrics.map((r) => ({
        ...r,
        scope: 'org',
      }));

      setRubrics([...globalRubrics, ...mergedOrgRubrics]);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshRubrics();
  }, [dataProvider, organisationId]);

  const handleCreateRubric = async () => {
    if (!newRubric.rubric_id || !newRubric.name || !organisationId) return;
    setActionLoading(true);
    try {
      await dataProvider.createOrgRubric(organisationId, {
        rubric_id: newRubric.rubric_id,
        family: newRubric.family,
        version: '1.0',
        content_type: newRubric.content_type,
        schema_version: '1.0',
        name: newRubric.name,
      });
      setShowCreateModal(false);
      setNewRubric({ rubric_id: '', name: '', family: 'soft_skills', content_type: 'prompt_item' });
      refreshRubrics();
    } catch (error) {
      console.error('Failed to create rubric:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const handleUpdateRubric = async () => {
    if (!selectedRubric || !organisationId) return;
    setActionLoading(true);
    try {
      await dataProvider.updateOrgRubric(organisationId, selectedRubric.rubric_id, {
        name: selectedRubric.name,
      });
      setShowEditModal(false);
      refreshRubrics();
    } catch (error) {
      console.error('Failed to update rubric:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeleteRubric = async (rubricId: string) => {
    if (!organisationId) return;
    const rubric = rubrics.find((r) => r.rubric_id === rubricId);
    if (rubric?.scope === 'global') {
      alert('Global rubrics cannot be deleted');
      return;
    }
    if (!confirm('Are you sure you want to delete this rubric?')) return;
    try {
      await dataProvider.deleteOrgRubric(organisationId, rubricId);
      if (selectedRubric?.rubric_id === rubricId) setSelectedRubric(null);
      refreshRubrics();
    } catch (error) {
      console.error('Failed to delete rubric:', error);
    }
  };

  const filteredRubrics = rubrics.filter((r) =>
    search ? r.name.toLowerCase().includes(search.toLowerCase()) || r.rubric_id.toLowerCase().includes(search.toLowerCase()) : true
  );

  if (loading || !organisationId) {
    return (
      <AdminPageShell title="Org Rubrics" subtitle="Manage organization-specific rubrics">
        <LoadingState message="Loading rubrics..." />
      </AdminPageShell>
    );
  }

  return (
    <AdminPageShell
      title="Org Rubrics"
      subtitle="Manage organization-specific rubrics"
      actions={
        <Button icon={<Plus className="w-4 h-4" />} onClick={() => setShowCreateModal(true)}>
          New Rubric
        </Button>
      }
    >
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard
          label="Global Rubrics"
          value={rubrics.filter((r) => r.scope === 'global').length}
          icon={<Globe className="w-4 h-4" />}
        />
        <MetricCard
          label="Org Rubrics"
          value={rubrics.filter((r) => r.scope === 'org').length}
          icon={<Scale className="w-4 h-4" />}
        />
        <MetricCard
          label="Total Rubrics"
          value={rubrics.length}
          icon={<Scale className="w-4 h-4" />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="flex flex-col gap-4">
          <SearchInput
            value={search}
            onChange={setSearch}
            placeholder="Search rubrics..."
          />
          <div className="flex flex-col gap-2">
            {filteredRubrics.map((rubric) => (
              <div
                key={rubric.rubric_id}
                onClick={() => setSelectedRubric(rubric)}
                className={`flex items-center gap-3 py-2.5 px-3 rounded-lg transition-colors cursor-pointer ${
                  selectedRubric?.rubric_id === rubric.rubric_id
                    ? 'bg-accent/10 border border-accent/20'
                    : 'hover:bg-surface-secondary/50'
                }`}
              >
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${rubric.scope === 'global' ? 'bg-surface-secondary' : 'bg-accent/10'}`}>
                  {rubric.scope === 'global' ? <Globe className="w-4 h-4 text-content-secondary" /> : <Scale className="w-4 h-4 text-accent" />}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-body-sm font-medium text-content-primary truncate">
                      {rubric.name}
                    </p>
                    <Badge variant={rubric.scope === 'global' ? 'default' : 'accent'} size="sm">
                      {rubric.scope === 'global' ? 'Global' : 'Org'}
                    </Badge>
                  </div>
                  <p className="text-body-xs text-content-tertiary truncate">
                    {rubric.family} · v{rubric.version}
                  </p>
                </div>
              </div>
            ))}
            {filteredRubrics.length === 0 && (
              <EmptyState
                icon={<Scale className="w-5 h-5" />}
                title="No rubrics found"
                description={search ? 'Try adjusting your search' : 'Create your first rubric to get started'}
              />
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
                <div className="flex items-center gap-2">
                  <Button
                    variant="secondary"
                    size="sm"
                    icon={<Edit className="w-4 h-4" />}
                    onClick={() => setShowEditModal(true)}
                    disabled={selectedRubric?.scope === 'global'}
                    title={selectedRubric?.scope === 'global' ? 'Global rubrics cannot be edited' : undefined}
                  >
                    Edit
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    icon={<Trash2 className="w-4 h-4" />}
                    onClick={() => handleDeleteRubric(selectedRubric.rubric_id)}
                    disabled={selectedRubric?.scope === 'global'}
                    title={selectedRubric?.scope === 'global' ? 'Global rubrics cannot be deleted' : undefined}
                  >
                    Delete
                  </Button>
                </div>
              </div>

              <div className="p-4 rounded-lg bg-surface-secondary/50 border border-line">
                <h4 className="text-body-sm font-medium text-content-secondary mb-2">Rubric ID</h4>
                <p className="text-body-sm text-content-primary font-mono">
                  {selectedRubric.rubric_id}
                </p>
              </div>

              {(selectedRubric.criteria?.length ?? 0) > 0 && (
                <div className="p-4 rounded-lg bg-surface-secondary/50 border border-line">
                  <h4 className="text-body-sm font-medium text-content-secondary mb-2">Criteria</h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedRubric.criteria!.map((criterion) => (
                      <Badge key={criterion} variant="default" size="sm">{criterion}</Badge>
                    ))}
                  </div>
                </div>
              )}
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

      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-md flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h3 className="font-display text-display-xs text-content-primary">New Rubric</h3>
              <button onClick={() => setShowCreateModal(false)} className="p-1 rounded hover:bg-surface-secondary">
                <X className="w-5 h-5 text-content-tertiary" />
              </button>
            </div>
            <div className="flex flex-col gap-3">
              <div>
                <label className="text-body-sm text-content-secondary mb-1 block">Name</label>
                <input
                  type="text"
                  value={newRubric.name}
                  onChange={(e) => setNewRubric({ ...newRubric, name: e.target.value })}
                  placeholder="Rubric name"
                  className="w-full px-3 py-2 rounded-lg border border-line bg-surface-primary text-content-primary placeholder:text-content-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50"
                />
              </div>
              <div>
                <label className="text-body-sm text-content-secondary mb-1 block">Rubric ID</label>
                <input
                  type="text"
                  value={newRubric.rubric_id}
                  onChange={(e) => setNewRubric({ ...newRubric, rubric_id: e.target.value })}
                  placeholder="rubric-id"
                  className="w-full px-3 py-2 rounded-lg border border-line bg-surface-primary text-content-primary placeholder:text-content-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50"
                />
              </div>
              <div>
                <label className="text-body-sm text-content-secondary mb-1 block">Family</label>
                <select
                  value={newRubric.family}
                  onChange={(e) => setNewRubric({ ...newRubric, family: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border border-line bg-surface-primary text-content-primary focus:outline-none focus:ring-2 focus:ring-accent/50"
                >
                  <option value="soft_skills">Soft Skills</option>
                  <option value="technical">Technical</option>
                  <option value="leadership">Leadership</option>
                </select>
              </div>
              <div>
                <label className="text-body-sm text-content-secondary mb-1 block">Content Type</label>
                <select
                  value={newRubric.content_type}
                  onChange={(e) => setNewRubric({ ...newRubric, content_type: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border border-line bg-surface-primary text-content-primary focus:outline-none focus:ring-2 focus:ring-accent/50"
                >
                  <option value="prompt_item">Prompt Item</option>
                  <option value="scenario">Scenario</option>
                  <option value="interview">Interview</option>
                </select>
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="secondary" onClick={() => setShowCreateModal(false)}>Cancel</Button>
              <Button onClick={handleCreateRubric} loading={actionLoading} icon={<Check className="w-4 h-4" />}>
                Create
              </Button>
            </div>
          </Card>
        </div>
      )}

      {showEditModal && selectedRubric && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-md flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h3 className="font-display text-display-xs text-content-primary">Edit Rubric</h3>
              <button onClick={() => setShowEditModal(false)} className="p-1 rounded hover:bg-surface-secondary">
                <X className="w-5 h-5 text-content-tertiary" />
              </button>
            </div>
            <div className="flex flex-col gap-3">
              <div>
                <label className="text-body-sm text-content-secondary mb-1 block">Name</label>
                <input
                  type="text"
                  value={selectedRubric.name}
                  onChange={(e) => setSelectedRubric({ ...selectedRubric, name: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border border-line bg-surface-primary text-content-primary focus:outline-none focus:ring-2 focus:ring-accent/50"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="secondary" onClick={() => setShowEditModal(false)}>Cancel</Button>
              <Button onClick={handleUpdateRubric} loading={actionLoading} icon={<Check className="w-4 h-4" />}>
                Save
              </Button>
            </div>
          </Card>
        </div>
      )}
    </AdminPageShell>
  );
}
