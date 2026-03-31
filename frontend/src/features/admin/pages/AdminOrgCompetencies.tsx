import { useEffect, useState } from 'react';
import { Plus, Edit, Trash2, X, Check, Target, Globe } from 'lucide-react';
import { useAdminScope } from '@/auth';
import { Card } from '@/design-system/primitives/Card';
import { Button } from '@/design-system/primitives/Button';
import { Badge } from '@/design-system/primitives/Badge';
import { LoadingState } from '@/design-system/patterns/LoadingState';
import { EmptyState } from '@/design-system/patterns/EmptyState';
import { useData } from '@/data';
import { AdminPageShell, MetricCard, SearchInput } from '../components';
import type { CompetencyView } from '@/data/types';

type CompetencyWithScope = CompetencyView & { scope: 'global' | 'org'; organisation_id?: string };

export function AdminOrgCompetencies() {
  const { organisationId } = useAdminScope();
  const dataProvider = useData();
  const [competencies, setCompetencies] = useState<CompetencyWithScope[]>([]);
  const [selectedCompetency, setSelectedCompetency] = useState<CompetencyWithScope | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [newCompetency, setNewCompetency] = useState({ slug: '', name: '', description: '', skill_slugs: '' });

  const orgId = organisationId;

  const refreshCompetencies = async () => {
    if (!orgId) return;
    setLoading(true);
    try {
      const [taxonomy, orgCompetencies] = await Promise.all([
        dataProvider.getTaxonomy(),
        dataProvider.listOrgCompetencies(orgId),
      ]);

      // Merge global and org competencies - org competencies take precedence
      const orgCompetencySlugs = new Set(orgCompetencies.map((c) => c.slug));
      const globalCompetencies: CompetencyWithScope[] = taxonomy.competencies
        .filter((c) => !orgCompetencySlugs.has(c.slug))
        .map((c) => ({ ...c, scope: 'global' }));
      const mergedOrgCompetencies: CompetencyWithScope[] = orgCompetencies.map((c) => ({
        ...c,
        scope: 'org',
        organisation_id: orgId,
      }));

      setCompetencies([...globalCompetencies, ...mergedOrgCompetencies]);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshCompetencies();
  }, [dataProvider, orgId]);

  const handleCreateCompetency = async () => {
    if (!newCompetency.slug || !newCompetency.name) return;
    setActionLoading(true);
    try {
      await dataProvider.createOrgCompetency(orgId!, {
        slug: newCompetency.slug.toLowerCase().replace(/\s+/g, '-'),
        name: newCompetency.name,
        description: newCompetency.description,
        skill_slugs: newCompetency.skill_slugs.split(',').map(s => s.trim()).filter(Boolean),
      });
      setShowCreateModal(false);
      setNewCompetency({ slug: '', name: '', description: '', skill_slugs: '' });
      refreshCompetencies();
    } catch (error) {
      console.error('Failed to create competency:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const handleUpdateCompetency = async () => {
    if (!selectedCompetency) return;
    setActionLoading(true);
    try {
      await dataProvider.updateOrgCompetency(orgId!, selectedCompetency.slug, {
        name: selectedCompetency.name,
        description: selectedCompetency.description,
        skill_slugs: selectedCompetency.skill_slugs,
      });
      setShowEditModal(false);
      refreshCompetencies();
    } catch (error) {
      console.error('Failed to update competency:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeleteCompetency = async (slug: string) => {
    if (!organisationId) return;
    const competency = competencies.find((c) => c.slug === slug);
    if (competency?.scope === 'global') {
      alert('Global competencies cannot be deleted');
      return;
    }
    if (!confirm('Are you sure you want to delete this competency?')) return;
    try {
      await dataProvider.deleteOrgCompetency(organisationId, slug);
      if (selectedCompetency?.slug === slug) setSelectedCompetency(null);
      refreshCompetencies();
    } catch (error) {
      console.error('Failed to delete competency:', error);
    }
  };

  const filteredCompetencies = competencies.filter((c) =>
    search ? c.name.toLowerCase().includes(search.toLowerCase()) || c.slug.toLowerCase().includes(search.toLowerCase()) : true
  );

  if (loading || !orgId) {
    return (
      <AdminPageShell title="Org Competencies" subtitle="Manage organization-specific competencies">
        <LoadingState message="Loading competencies..." />
      </AdminPageShell>
    );
  }

  return (
    <AdminPageShell
      title="Org Competencies"
      subtitle="Manage organization-specific competencies"
      actions={
        <Button icon={<Plus className="w-4 h-4" />} onClick={() => setShowCreateModal(true)}>
          New Competency
        </Button>
      }
    >
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard
          label="Global Competencies"
          value={competencies.filter((c) => c.scope === 'global').length}
          icon={<Globe className="w-4 h-4" />}
        />
        <MetricCard
          label="Org Competencies"
          value={competencies.filter((c) => c.scope === 'org').length}
          icon={<Target className="w-4 h-4" />}
        />
        <MetricCard
          label="Total Competencies"
          value={competencies.length}
          icon={<Target className="w-4 h-4" />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="flex flex-col gap-4">
          <SearchInput
            value={search}
            onChange={setSearch}
            placeholder="Search competencies..."
          />
          <div className="flex flex-col gap-2">
            {filteredCompetencies.map((competency) => (
              <div
                key={competency.slug}
                onClick={() => setSelectedCompetency(competency)}
                className={`flex items-center gap-3 py-2.5 px-3 rounded-lg transition-colors cursor-pointer ${
                  selectedCompetency?.slug === competency.slug
                    ? 'bg-accent/10 border border-accent/20'
                    : 'hover:bg-surface-secondary/50'
                }`}
              >
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${competency.scope === 'global' ? 'bg-surface-secondary' : 'bg-accent/10'}`}>
                  {competency.scope === 'global' ? <Globe className="w-4 h-4 text-content-secondary" /> : <Target className="w-4 h-4 text-accent" />}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-body-sm font-medium text-content-primary truncate">
                      {competency.name}
                    </p>
                    <Badge variant={competency.scope === 'global' ? 'default' : 'accent'} size="sm">
                      {competency.scope === 'global' ? 'Global' : 'Org'}
                    </Badge>
                  </div>
                  <p className="text-body-xs text-content-tertiary truncate">
                    {competency.slug}
                  </p>
                </div>
              </div>
            ))}
            {filteredCompetencies.length === 0 && (
              <EmptyState
                icon={<Target className="w-5 h-5" />}
                title="No competencies found"
                description={search ? 'Try adjusting your search' : 'Create your first competency to get started'}
              />
            )}
          </div>
        </Card>

        <Card className="lg:col-span-2 flex flex-col gap-4">
          {selectedCompetency ? (
            <>
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-display text-body-md font-semibold text-content-primary">
                    {selectedCompetency.name}
                  </h3>
                  <p className="text-body-xs text-content-tertiary">
                    {selectedCompetency.slug}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="secondary"
                    size="sm"
                    icon={<Edit className="w-4 h-4" />}
                    onClick={() => setShowEditModal(true)}
                    disabled={selectedCompetency?.scope === 'global'}
                    title={selectedCompetency?.scope === 'global' ? 'Global competencies cannot be edited' : undefined}
                  >
                    Edit
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    icon={<Trash2 className="w-4 h-4" />}
                    onClick={() => handleDeleteCompetency(selectedCompetency.slug)}
                    disabled={selectedCompetency?.scope === 'global'}
                    title={selectedCompetency?.scope === 'global' ? 'Global competencies cannot be deleted' : undefined}
                  >
                    Delete
                  </Button>
                </div>
              </div>

              <div className="p-4 rounded-lg bg-surface-secondary/50 border border-line">
                <h4 className="text-body-sm font-medium text-content-secondary mb-2">Description</h4>
                <p className="text-body-sm text-content-primary">
                  {selectedCompetency.description || 'No description provided'}
                </p>
              </div>

              {selectedCompetency.skill_slugs.length > 0 && (
                <div className="p-4 rounded-lg bg-surface-secondary/50 border border-line">
                  <h4 className="text-body-sm font-medium text-content-secondary mb-2">Linked Skills</h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedCompetency.skill_slugs.map((slug) => (
                      <Badge key={slug} variant="default" size="sm">{slug}</Badge>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="flex items-center justify-center py-16">
              <p className="text-body-sm text-content-tertiary">
                Select a competency to view details
              </p>
            </div>
          )}
        </Card>
      </div>

      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-md flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h3 className="font-display text-display-xs text-content-primary">New Competency</h3>
              <button onClick={() => setShowCreateModal(false)} className="p-1 rounded hover:bg-surface-secondary">
                <X className="w-5 h-5 text-content-tertiary" />
              </button>
            </div>
            <div className="flex flex-col gap-3">
              <div>
                <label className="text-body-sm text-content-secondary mb-1 block">Name</label>
                <input
                  type="text"
                  value={newCompetency.name}
                  onChange={(e) => setNewCompetency({ ...newCompetency, name: e.target.value })}
                  placeholder="Competency name"
                  className="w-full px-3 py-2 rounded-lg border border-line bg-surface-primary text-content-primary placeholder:text-content-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50"
                />
              </div>
              <div>
                <label className="text-body-sm text-content-secondary mb-1 block">Slug</label>
                <input
                  type="text"
                  value={newCompetency.slug}
                  onChange={(e) => setNewCompetency({ ...newCompetency, slug: e.target.value })}
                  placeholder="competency-slug"
                  className="w-full px-3 py-2 rounded-lg border border-line bg-surface-primary text-content-primary placeholder:text-content-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50"
                />
              </div>
              <div>
                <label className="text-body-sm text-content-secondary mb-1 block">Description</label>
                <textarea
                  value={newCompetency.description}
                  onChange={(e) => setNewCompetency({ ...newCompetency, description: e.target.value })}
                  placeholder="Competency description"
                  rows={3}
                  className="w-full px-3 py-2 rounded-lg border border-line bg-surface-primary text-content-primary placeholder:text-content-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50 resize-none"
                />
              </div>
              <div>
                <label className="text-body-sm text-content-secondary mb-1 block">Skill Slugs (comma-separated)</label>
                <input
                  type="text"
                  value={newCompetency.skill_slugs}
                  onChange={(e) => setNewCompetency({ ...newCompetency, skill_slugs: e.target.value })}
                  placeholder="skill-1, skill-2, skill-3"
                  className="w-full px-3 py-2 rounded-lg border border-line bg-surface-primary text-content-primary placeholder:text-content-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="secondary" onClick={() => setShowCreateModal(false)}>Cancel</Button>
              <Button onClick={handleCreateCompetency} loading={actionLoading} icon={<Check className="w-4 h-4" />}>
                Create
              </Button>
            </div>
          </Card>
        </div>
      )}

      {showEditModal && selectedCompetency && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-md flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h3 className="font-display text-display-xs text-content-primary">Edit Competency</h3>
              <button onClick={() => setShowEditModal(false)} className="p-1 rounded hover:bg-surface-secondary">
                <X className="w-5 h-5 text-content-tertiary" />
              </button>
            </div>
            <div className="flex flex-col gap-3">
              <div>
                <label className="text-body-sm text-content-secondary mb-1 block">Name</label>
                <input
                  type="text"
                  value={selectedCompetency.name}
                  onChange={(e) => setSelectedCompetency({ ...selectedCompetency, name: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border border-line bg-surface-primary text-content-primary focus:outline-none focus:ring-2 focus:ring-accent/50"
                />
              </div>
              <div>
                <label className="text-body-sm text-content-secondary mb-1 block">Description</label>
                <textarea
                  value={selectedCompetency.description}
                  onChange={(e) => setSelectedCompetency({ ...selectedCompetency, description: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 rounded-lg border border-line bg-surface-primary text-content-primary focus:outline-none focus:ring-2 focus:ring-accent/50 resize-none"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="secondary" onClick={() => setShowEditModal(false)}>Cancel</Button>
              <Button onClick={handleUpdateCompetency} loading={actionLoading} icon={<Check className="w-4 h-4" />}>
                Save
              </Button>
            </div>
          </Card>
        </div>
      )}
    </AdminPageShell>
  );
}
