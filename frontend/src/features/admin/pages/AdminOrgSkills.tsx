import { useEffect, useState } from 'react';
import { Plus, Edit, Trash2, X, Check, Star, Globe } from 'lucide-react';
import { useAdminScope } from '@/auth';
import { Card } from '@/design-system/primitives/Card';
import { Button } from '@/design-system/primitives/Button';
import { Badge } from '@/design-system/primitives/Badge';
import { LoadingState } from '@/design-system/patterns/LoadingState';
import { EmptyState } from '@/design-system/patterns/EmptyState';
import { useData } from '@/data';
import { AdminPageShell, MetricCard, SearchInput } from '../components';
import type { SkillView } from '@/data/types';

type SkillWithScope = SkillView & { scope: 'global' | 'org'; organisation_id?: string };

export function AdminOrgSkills() {
  const { organisationId } = useAdminScope();
  const dataProvider = useData();
  const [skills, setSkills] = useState<SkillWithScope[]>([]);
  const [selectedSkill, setSelectedSkill] = useState<SkillWithScope | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [newSkill, setNewSkill] = useState({ slug: '', name: '', description: '' });

  const orgId = organisationId;

  const refreshSkills = async () => {
    if (!orgId) return;
    setLoading(true);
    try {
      const [taxonomy, orgSkills] = await Promise.all([
        dataProvider.getTaxonomy(),
        dataProvider.listOrgSkills(orgId),
      ]);

      // Merge global and org skills - org skills take precedence
      const orgSkillSlugs = new Set(orgSkills.map((s) => s.slug));
      const globalSkills: SkillWithScope[] = taxonomy.skills
        .filter((s) => !orgSkillSlugs.has(s.slug))
        .map((s) => ({ ...s, scope: 'global' }));
      const mergedOrgSkills: SkillWithScope[] = orgSkills.map((s) => ({
        ...s,
        scope: 'org',
        organisation_id: orgId,
      }));

      setSkills([...globalSkills, ...mergedOrgSkills]);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refreshSkills();
  }, [dataProvider, orgId]);

  const handleCreateSkill = async () => {
    if (!newSkill.slug || !newSkill.name) return;
    setActionLoading(true);
    try {
      await dataProvider.createOrgSkill(orgId!, {
        slug: newSkill.slug.toLowerCase().replace(/\s+/g, '-'),
        name: newSkill.name,
        description: newSkill.description,
      });
      setShowCreateModal(false);
      setNewSkill({ slug: '', name: '', description: '' });
      refreshSkills();
    } catch (error) {
      console.error('Failed to create skill:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const handleUpdateSkill = async () => {
    if (!selectedSkill) return;
    setActionLoading(true);
    try {
      await dataProvider.updateOrgSkill(orgId!, selectedSkill.slug, {
        name: selectedSkill.name,
        description: selectedSkill.description,
      });
      setShowEditModal(false);
      refreshSkills();
    } catch (error) {
      console.error('Failed to update skill:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeleteSkill = async (slug: string) => {
    if (!orgId) return;
    const skill = skills.find((s) => s.slug === slug);
    if (skill?.scope === 'global') {
      alert('Global skills cannot be deleted');
      return;
    }
    if (!confirm('Are you sure you want to delete this skill?')) return;
    try {
      await dataProvider.deleteOrgSkill(orgId, slug);
      if (selectedSkill?.slug === slug) setSelectedSkill(null);
      refreshSkills();
    } catch (error) {
      console.error('Failed to delete skill:', error);
    }
  };

  const filteredSkills = skills.filter((s) =>
    search ? s.name.toLowerCase().includes(search.toLowerCase()) || s.slug.toLowerCase().includes(search.toLowerCase()) : true
  );

  if (loading || !orgId) {
    return (
      <AdminPageShell title="Org Skills" subtitle="Manage organization-specific skills">
        <LoadingState message="Loading skills..." />
      </AdminPageShell>
    );
  }

  return (
    <AdminPageShell
      title="Org Skills"
      subtitle="Manage organization-specific skills"
      actions={
        <Button icon={<Plus className="w-4 h-4" />} onClick={() => setShowCreateModal(true)}>
          New Skill
        </Button>
      }
    >
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard
          label="Global Skills"
          value={skills.filter((s) => s.scope === 'global').length}
          icon={<Globe className="w-4 h-4" />}
        />
        <MetricCard
          label="Org Skills"
          value={skills.filter((s) => s.scope === 'org').length}
          icon={<Star className="w-4 h-4" />}
        />
        <MetricCard
          label="Total Skills"
          value={skills.length}
          icon={<Star className="w-4 h-4" />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="flex flex-col gap-4">
          <SearchInput
            value={search}
            onChange={setSearch}
            placeholder="Search skills..."
          />
          <div className="flex flex-col gap-2">
            {filteredSkills.map((skill) => (
              <div
                key={skill.slug}
                onClick={() => setSelectedSkill(skill)}
                className={`flex items-center gap-3 py-2.5 px-3 rounded-lg transition-colors cursor-pointer ${
                  selectedSkill?.slug === skill.slug
                    ? 'bg-accent/10 border border-accent/20'
                    : 'hover:bg-surface-secondary/50'
                }`}
              >
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${skill.scope === 'global' ? 'bg-surface-secondary' : 'bg-accent/10'}`}>
                  {skill.scope === 'global' ? <Globe className="w-4 h-4 text-content-secondary" /> : <Star className="w-4 h-4 text-accent" />}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-body-sm font-medium text-content-primary truncate">
                      {skill.name}
                    </p>
                    <Badge variant={skill.scope === 'global' ? 'default' : 'accent'} size="sm">
                      {skill.scope === 'global' ? 'Global' : 'Org'}
                    </Badge>
                  </div>
                  <p className="text-body-xs text-content-tertiary truncate">
                    {skill.slug}
                  </p>
                </div>
              </div>
            ))}
            {filteredSkills.length === 0 && (
              <EmptyState
                icon={<Star className="w-5 h-5" />}
                title="No skills found"
                description={search ? 'Try adjusting your search' : 'Create your first skill to get started'}
              />
            )}
          </div>
        </Card>

        <Card className="lg:col-span-2 flex flex-col gap-4">
          {selectedSkill ? (
            <>
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-display text-body-md font-semibold text-content-primary">
                    {selectedSkill.name}
                  </h3>
                  <p className="text-body-xs text-content-tertiary">
                    {selectedSkill.slug}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="secondary"
                    size="sm"
                    icon={<Edit className="w-4 h-4" />}
                    onClick={() => setShowEditModal(true)}
                    disabled={selectedSkill?.scope === 'global'}
                    title={selectedSkill?.scope === 'global' ? 'Global skills cannot be edited' : undefined}
                  >
                    Edit
                  </Button>
                  <Button
                    variant="secondary"
                    size="sm"
                    icon={<Trash2 className="w-4 h-4" />}
                    onClick={() => handleDeleteSkill(selectedSkill.slug)}
                    disabled={selectedSkill?.scope === 'global'}
                    title={selectedSkill?.scope === 'global' ? 'Global skills cannot be deleted' : undefined}
                  >
                    Delete
                  </Button>
                </div>
              </div>

              <div className="p-4 rounded-lg bg-surface-secondary/50 border border-line">
                <h4 className="text-body-sm font-medium text-content-secondary mb-2">Description</h4>
                <p className="text-body-sm text-content-primary">
                  {selectedSkill.description || 'No description provided'}
                </p>
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center py-16">
              <p className="text-body-sm text-content-tertiary">
                Select a skill to view details
              </p>
            </div>
          )}
        </Card>
      </div>

      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-md flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h3 className="font-display text-display-xs text-content-primary">New Skill</h3>
              <button onClick={() => setShowCreateModal(false)} className="p-1 rounded hover:bg-surface-secondary">
                <X className="w-5 h-5 text-content-tertiary" />
              </button>
            </div>
            <div className="flex flex-col gap-3">
              <div>
                <label className="text-body-sm text-content-secondary mb-1 block">Name</label>
                <input
                  type="text"
                  value={newSkill.name}
                  onChange={(e) => setNewSkill({ ...newSkill, name: e.target.value })}
                  placeholder="Skill name"
                  className="w-full px-3 py-2 rounded-lg border border-line bg-surface-primary text-content-primary placeholder:text-content-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50"
                />
              </div>
              <div>
                <label className="text-body-sm text-content-secondary mb-1 block">Slug</label>
                <input
                  type="text"
                  value={newSkill.slug}
                  onChange={(e) => setNewSkill({ ...newSkill, slug: e.target.value })}
                  placeholder="skill-slug"
                  className="w-full px-3 py-2 rounded-lg border border-line bg-surface-primary text-content-primary placeholder:text-content-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50"
                />
              </div>
              <div>
                <label className="text-body-sm text-content-secondary mb-1 block">Description</label>
                <textarea
                  value={newSkill.description}
                  onChange={(e) => setNewSkill({ ...newSkill, description: e.target.value })}
                  placeholder="Skill description"
                  rows={3}
                  className="w-full px-3 py-2 rounded-lg border border-line bg-surface-primary text-content-primary placeholder:text-content-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50 resize-none"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="secondary" onClick={() => setShowCreateModal(false)}>Cancel</Button>
              <Button onClick={handleCreateSkill} loading={actionLoading} icon={<Check className="w-4 h-4" />}>
                Create
              </Button>
            </div>
          </Card>
        </div>
      )}

      {showEditModal && selectedSkill && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-md flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h3 className="font-display text-display-xs text-content-primary">Edit Skill</h3>
              <button onClick={() => setShowEditModal(false)} className="p-1 rounded hover:bg-surface-secondary">
                <X className="w-5 h-5 text-content-tertiary" />
              </button>
            </div>
            <div className="flex flex-col gap-3">
              <div>
                <label className="text-body-sm text-content-secondary mb-1 block">Name</label>
                <input
                  type="text"
                  value={selectedSkill.name}
                  onChange={(e) => setSelectedSkill({ ...selectedSkill, name: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border border-line bg-surface-primary text-content-primary focus:outline-none focus:ring-2 focus:ring-accent/50"
                />
              </div>
              <div>
                <label className="text-body-sm text-content-secondary mb-1 block">Description</label>
                <textarea
                  value={selectedSkill.description}
                  onChange={(e) => setSelectedSkill({ ...selectedSkill, description: e.target.value })}
                  rows={3}
                  className="w-full px-3 py-2 rounded-lg border border-line bg-surface-primary text-content-primary focus:outline-none focus:ring-2 focus:ring-accent/50 resize-none"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="secondary" onClick={() => setShowEditModal(false)}>Cancel</Button>
              <Button onClick={handleUpdateSkill} loading={actionLoading} icon={<Check className="w-4 h-4" />}>
                Save
              </Button>
            </div>
          </Card>
        </div>
      )}
    </AdminPageShell>
  );
}
