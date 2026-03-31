import { useEffect, useState } from 'react';
import { Plus, Trash2, X, Check, Users, Globe } from 'lucide-react';
import { useAdminScope } from '@/auth';
import { Card } from '@/design-system/primitives/Card';
import { Button } from '@/design-system/primitives/Button';
import { Badge } from '@/design-system/primitives/Badge';
import { LoadingState } from '@/design-system/patterns/LoadingState';
import { EmptyState } from '@/design-system/patterns/EmptyState';
import { useData } from '@/data';
import { AdminPageShell, MetricCard, SearchInput } from '../components';
import type { ScenarioView, CollectionView } from '@/data/types';

type ScenarioWithScope = ScenarioView & { scope: 'global' | 'org' };

export function AdminOrgScenarios() {
  const { organisationId } = useAdminScope();
  const dataProvider = useData();
  const [scenarios, setScenarios] = useState<ScenarioWithScope[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<ScenarioWithScope | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [newScenario, setNewScenario] = useState({
    title: '',
    business_context: '',
    learner_objective: '',
    rubric_id: '',
    target_skill_slugs: '',
    constraints: '',
    stakeholder_tensions: '',
  });

  const refreshScenarios = async () => {
    if (!organisationId) return;
    setLoading(true);
    try {
      const [globalCollections, orgScenarios] = await Promise.all([
        dataProvider.listCollections(),
        dataProvider.listOrgScenarios(organisationId),
      ]);

      // Extract global scenarios from collections
      const orgScenarioIds = new Set(orgScenarios.map((s) => s.id));
      const globalScenarios: ScenarioWithScope[] = [];
      globalCollections.forEach((collection: CollectionView) => {
        collection.scenarios?.forEach((scenario: ScenarioView) => {
          if (!orgScenarioIds.has(scenario.id)) {
            globalScenarios.push({ ...scenario, scope: 'global' });
          }
        });
      });

      const mergedOrgScenarios: ScenarioWithScope[] = orgScenarios.map((s) => ({
        ...s,
        scope: 'org',
      }));

      setScenarios([...globalScenarios, ...mergedOrgScenarios]);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshScenarios();
  }, [dataProvider, organisationId]);

  const handleCreateScenario = async () => {
    if (!newScenario.title || !newScenario.business_context || !organisationId) return;
    setActionLoading(true);
    try {
      await dataProvider.createOrgScenario(organisationId, {
        title: newScenario.title,
        business_context: newScenario.business_context,
        learner_objective: newScenario.learner_objective,
        rubric_id: newScenario.rubric_id,
        target_skill_slugs: newScenario.target_skill_slugs.split(',').map(s => s.trim()).filter(Boolean),
        constraints: newScenario.constraints.split(',').map(s => s.trim()).filter(Boolean),
        stakeholder_tensions: newScenario.stakeholder_tensions.split(',').map(s => s.trim()).filter(Boolean),
      });
      setShowCreateModal(false);
      setNewScenario({
        title: '',
        business_context: '',
        learner_objective: '',
        rubric_id: '',
        target_skill_slugs: '',
        constraints: '',
        stakeholder_tensions: '',
      });
      refreshScenarios();
    } catch (error) {
      console.error('Failed to create scenario:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeleteScenario = async (id: string) => {
    if (!organisationId) return;
    const scenario = scenarios.find((s) => s.id === id);
    if (scenario?.scope === 'global') {
      alert('Global scenarios cannot be deleted');
      return;
    }
    if (!confirm('Are you sure you want to delete this scenario?')) return;
    try {
      await dataProvider.deleteOrgScenario(organisationId, id);
      if (selectedScenario?.id === id) setSelectedScenario(null);
      refreshScenarios();
    } catch (error) {
      console.error('Failed to delete scenario:', error);
    }
  };

  const filteredScenarios = scenarios.filter((s) =>
    search ? s.title.toLowerCase().includes(search.toLowerCase()) || s.id.toLowerCase().includes(search.toLowerCase()) : true
  );

  if (loading || !organisationId) {
    return (
      <AdminPageShell title="Org Scenarios" subtitle="Manage organization-specific scenarios">
        <LoadingState message="Loading scenarios..." />
      </AdminPageShell>
    );
  }

  return (
    <AdminPageShell
      title="Org Scenarios"
      subtitle="Manage organization-specific scenarios"
      actions={
        <Button icon={<Plus className="w-4 h-4" />} onClick={() => setShowCreateModal(true)}>
          New Scenario
        </Button>
      }
    >
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard
          label="Global Scenarios"
          value={scenarios.filter((s) => s.scope === 'global').length}
          icon={<Globe className="w-4 h-4" />}
        />
        <MetricCard
          label="Org Scenarios"
          value={scenarios.filter((s) => s.scope === 'org').length}
          icon={<Users className="w-4 h-4" />}
        />
        <MetricCard
          label="Total Scenarios"
          value={scenarios.length}
          icon={<Users className="w-4 h-4" />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="flex flex-col gap-4">
          <SearchInput
            value={search}
            onChange={setSearch}
            placeholder="Search scenarios..."
          />
          <div className="flex flex-col gap-2">
            {filteredScenarios.map((scenario) => (
              <div
                key={scenario.id}
                onClick={() => setSelectedScenario(scenario)}
                className={`flex items-center gap-3 py-2.5 px-3 rounded-lg transition-colors cursor-pointer ${
                  selectedScenario?.id === scenario.id
                    ? 'bg-accent/10 border border-accent/20'
                    : 'hover:bg-surface-secondary/50'
                }`}
              >
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${scenario.scope === 'global' ? 'bg-surface-secondary' : 'bg-accent/10'}`}>
                  {scenario.scope === 'global' ? <Globe className="w-4 h-4 text-content-secondary" /> : <Users className="w-4 h-4 text-accent" />}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-body-sm font-medium text-content-primary truncate">
                      {scenario.title}
                    </p>
                    <Badge variant={scenario.scope === 'global' ? 'default' : 'accent'} size="sm">
                      {scenario.scope === 'global' ? 'Global' : 'Org'}
                    </Badge>
                  </div>
                  <p className="text-body-xs text-content-tertiary truncate">
                    {scenario.lifecycle_state}
                  </p>
                </div>
              </div>
            ))}
            {filteredScenarios.length === 0 && (
              <EmptyState
                icon={<Users className="w-5 h-5" />}
                title="No scenarios found"
                description={search ? 'Try adjusting your search' : 'Create your first scenario to get started'}
              />
            )}
          </div>
        </Card>

        <Card className="lg:col-span-2 flex flex-col gap-4">
          {selectedScenario ? (
            <>
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-display text-body-md font-semibold text-content-primary">
                    {selectedScenario.title}
                  </h3>
                  <p className="text-body-xs text-content-tertiary font-mono">
                    {selectedScenario.id}
                  </p>
                </div>
                <Button
                  variant="secondary"
                  size="sm"
                  icon={<Trash2 className="w-4 h-4" />}
                  onClick={() => handleDeleteScenario(selectedScenario.id)}
                  disabled={selectedScenario?.scope === 'global'}
                  title={selectedScenario?.scope === 'global' ? 'Global scenarios cannot be deleted' : undefined}
                >
                  Delete
                </Button>
              </div>

              <div className="flex gap-2 flex-wrap">
                <Badge variant="default" size="sm">{selectedScenario.lifecycle_state}</Badge>
              </div>

              <div className="p-4 rounded-lg bg-surface-secondary/50 border border-line">
                <h4 className="text-body-sm font-medium text-content-secondary mb-2">Business Context</h4>
                <p className="text-body-sm text-content-primary whitespace-pre-wrap">
                  {selectedScenario.business_context}
                </p>
              </div>

              {selectedScenario.learner_objective && (
                <div className="p-4 rounded-lg bg-surface-secondary/50 border border-line">
                  <h4 className="text-body-sm font-medium text-content-secondary mb-2">Learner Objective</h4>
                  <p className="text-body-sm text-content-primary">
                    {selectedScenario.learner_objective}
                  </p>
                </div>
              )}

              <div className="p-4 rounded-lg bg-surface-secondary/50 border border-line">
                <h4 className="text-body-sm font-medium text-content-secondary mb-2">Rubric ID</h4>
                <p className="text-body-sm text-content-primary font-mono">
                  {selectedScenario.rubric_id}
                </p>
              </div>

              {selectedScenario.target_skill_slugs.length > 0 && (
                <div className="p-4 rounded-lg bg-surface-secondary/50 border border-line">
                  <h4 className="text-body-sm font-medium text-content-secondary mb-2">Target Skills</h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedScenario.target_skill_slugs.map((slug) => (
                      <Badge key={slug} variant="default" size="sm">{slug}</Badge>
                    ))}
                  </div>
                </div>
              )}

              {selectedScenario.constraints.length > 0 && (
                <div className="p-4 rounded-lg bg-surface-secondary/50 border border-line">
                  <h4 className="text-body-sm font-medium text-content-secondary mb-2">Constraints</h4>
                  <ul className="list-disc list-inside text-body-sm text-content-primary">
                    {selectedScenario.constraints.map((c, i) => (
                      <li key={i}>{c}</li>
                    ))}
                  </ul>
                </div>
              )}

              {selectedScenario.stakeholder_tensions.length > 0 && (
                <div className="p-4 rounded-lg bg-surface-secondary/50 border border-line">
                  <h4 className="text-body-sm font-medium text-content-secondary mb-2">Stakeholder Tensions</h4>
                  <ul className="list-disc list-inside text-body-sm text-content-primary">
                    {selectedScenario.stakeholder_tensions.map((t, i) => (
                      <li key={i}>{t}</li>
                    ))}
                  </ul>
                </div>
              )}

              {selectedScenario.mock_company && (
                <div className="p-4 rounded-lg bg-surface-secondary/50 border border-line">
                  <h4 className="text-body-sm font-medium text-content-secondary mb-2">Mock Company</h4>
                  <p className="text-body-sm text-content-primary">
                    <span className="font-medium">{selectedScenario.mock_company.name}</span> ({selectedScenario.mock_company.industry})
                  </p>
                  <p className="text-body-xs text-content-secondary mt-1">
                    {selectedScenario.mock_company.operating_context}
                  </p>
                </div>
              )}
            </>
          ) : (
            <div className="flex items-center justify-center py-16">
              <p className="text-body-sm text-content-tertiary">
                Select a scenario to view details
              </p>
            </div>
          )}
        </Card>
      </div>

      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-lg flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h3 className="font-display text-display-xs text-content-primary">New Scenario</h3>
              <button onClick={() => setShowCreateModal(false)} className="p-1 rounded hover:bg-surface-secondary">
                <X className="w-5 h-5 text-content-tertiary" />
              </button>
            </div>
            <div className="flex flex-col gap-3">
              <div>
                <label className="text-body-sm text-content-secondary mb-1 block">Title</label>
                <input
                  type="text"
                  value={newScenario.title}
                  onChange={(e) => setNewScenario({ ...newScenario, title: e.target.value })}
                  placeholder="Scenario title"
                  className="w-full px-3 py-2 rounded-lg border border-line bg-surface-primary text-content-primary placeholder:text-content-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50"
                />
              </div>
              <div>
                <label className="text-body-sm text-content-secondary mb-1 block">Business Context</label>
                <textarea
                  value={newScenario.business_context}
                  onChange={(e) => setNewScenario({ ...newScenario, business_context: e.target.value })}
                  placeholder="Describe the business context..."
                  rows={3}
                  className="w-full px-3 py-2 rounded-lg border border-line bg-surface-primary text-content-primary placeholder:text-content-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50 resize-none"
                />
              </div>
              <div>
                <label className="text-body-sm text-content-secondary mb-1 block">Learner Objective</label>
                <input
                  type="text"
                  value={newScenario.learner_objective}
                  onChange={(e) => setNewScenario({ ...newScenario, learner_objective: e.target.value })}
                  placeholder="What should the learner achieve?"
                  className="w-full px-3 py-2 rounded-lg border border-line bg-surface-primary text-content-primary placeholder:text-content-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50"
                />
              </div>
              <div>
                <label className="text-body-sm text-content-secondary mb-1 block">Rubric ID</label>
                <input
                  type="text"
                  value={newScenario.rubric_id}
                  onChange={(e) => setNewScenario({ ...newScenario, rubric_id: e.target.value })}
                  placeholder="rubric-id"
                  className="w-full px-3 py-2 rounded-lg border border-line bg-surface-primary text-content-primary placeholder:text-content-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50"
                />
              </div>
              <div>
                <label className="text-body-sm text-content-secondary mb-1 block">Target Skill Slugs (comma-separated)</label>
                <input
                  type="text"
                  value={newScenario.target_skill_slugs}
                  onChange={(e) => setNewScenario({ ...newScenario, target_skill_slugs: e.target.value })}
                  placeholder="skill-1, skill-2"
                  className="w-full px-3 py-2 rounded-lg border border-line bg-surface-primary text-content-primary placeholder:text-content-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50"
                />
              </div>
              <div>
                <label className="text-body-sm text-content-secondary mb-1 block">Constraints (comma-separated)</label>
                <input
                  type="text"
                  value={newScenario.constraints}
                  onChange={(e) => setNewScenario({ ...newScenario, constraints: e.target.value })}
                  placeholder="Constraint 1, Constraint 2"
                  className="w-full px-3 py-2 rounded-lg border border-line bg-surface-primary text-content-primary placeholder:text-content-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50"
                />
              </div>
              <div>
                <label className="text-body-sm text-content-secondary mb-1 block">Stakeholder Tensions (comma-separated)</label>
                <input
                  type="text"
                  value={newScenario.stakeholder_tensions}
                  onChange={(e) => setNewScenario({ ...newScenario, stakeholder_tensions: e.target.value })}
                  placeholder="Tension 1, Tension 2"
                  className="w-full px-3 py-2 rounded-lg border border-line bg-surface-primary text-content-primary placeholder:text-content-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="secondary" onClick={() => setShowCreateModal(false)}>Cancel</Button>
              <Button onClick={handleCreateScenario} loading={actionLoading} icon={<Check className="w-4 h-4" />}>
                Create
              </Button>
            </div>
          </Card>
        </div>
      )}
    </AdminPageShell>
  );
}
