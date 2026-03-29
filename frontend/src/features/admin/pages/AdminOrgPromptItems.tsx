import { useEffect, useState } from 'react';
import { Plus, Trash2, X, Check, FileText } from 'lucide-react';
import { useAdminScope } from '@/auth';
import { Card } from '@/design-system/primitives/Card';
import { Button } from '@/design-system/primitives/Button';
import { Badge } from '@/design-system/primitives/Badge';
import { LoadingState } from '@/design-system/patterns/LoadingState';
import { EmptyState } from '@/design-system/patterns/EmptyState';
import { useData } from '@/data';
import { AdminPageShell, MetricCard, SearchInput } from '../components';
import type { PromptItemView } from '@/data/types';
import type { Difficulty } from '@/data/types/shared';

export function AdminOrgPromptItems() {
  const { organisationId } = useAdminScope();
  const dataProvider = useData();
  const [promptItems, setPromptItems] = useState<PromptItemView[]>([]);
  const [selectedItem, setSelectedItem] = useState<PromptItemView | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [newItem, setNewItem] = useState({
    title: '',
    prompt_text: '',
    prompt_type: 'quick_practice_prompt' as const,
    difficulty: 'intermediate' as Difficulty,
    rubric_id: '',
    target_skill_slugs: '',
  });

  const refreshPromptItems = () => {
    if (!organisationId) return;
    setLoading(true);
    dataProvider.listOrgPromptItems(organisationId)
      .then(setPromptItems)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    refreshPromptItems();
  }, [dataProvider, organisationId]);

  const handleCreatePromptItem = async () => {
    if (!newItem.title || !newItem.prompt_text || !organisationId) return;
    setActionLoading(true);
    try {
      await dataProvider.createOrgPromptItem(organisationId, {
        title: newItem.title,
        prompt_text: newItem.prompt_text,
        prompt_type: newItem.prompt_type,
        difficulty: newItem.difficulty,
        rubric_id: newItem.rubric_id,
        target_skill_slugs: newItem.target_skill_slugs.split(',').map(s => s.trim()).filter(Boolean),
      });
      setShowCreateModal(false);
      setNewItem({
        title: '',
        prompt_text: '',
        prompt_type: 'quick_practice_prompt',
        difficulty: 'intermediate',
        rubric_id: '',
        target_skill_slugs: '',
      });
      refreshPromptItems();
    } catch (error) {
      console.error('Failed to create prompt item:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeletePromptItem = async (id: string) => {
    if (!organisationId) return;
    if (!confirm('Are you sure you want to delete this prompt item?')) return;
    try {
      await dataProvider.deleteOrgPromptItem(organisationId, id);
      if (selectedItem?.id === id) setSelectedItem(null);
      refreshPromptItems();
    } catch (error) {
      console.error('Failed to delete prompt item:', error);
    }
  };

  const filteredItems = promptItems.filter((p) =>
    search ? p.title.toLowerCase().includes(search.toLowerCase()) || p.id.toLowerCase().includes(search.toLowerCase()) : true
  );

  if (loading || !organisationId) {
    return (
      <AdminPageShell title="Org Prompt Items" subtitle="Manage organization-specific prompt items">
        <LoadingState message="Loading prompt items..." />
      </AdminPageShell>
    );
  }

  return (
    <AdminPageShell
      title="Org Prompt Items"
      subtitle="Manage organization-specific prompt items"
      actions={
        <Button icon={<Plus className="w-4 h-4" />} onClick={() => setShowCreateModal(true)}>
          New Prompt Item
        </Button>
      }
    >
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <MetricCard
          label="Total Prompt Items"
          value={promptItems.length}
          icon={<FileText className="w-4 h-4" />}
        />
        <MetricCard
          label="By Type"
          value={new Set(promptItems.map((p) => p.prompt_type)).size}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="flex flex-col gap-4">
          <SearchInput
            value={search}
            onChange={setSearch}
            placeholder="Search prompt items..."
          />
          <div className="flex flex-col gap-2">
            {filteredItems.map((item) => (
              <div
                key={item.id}
                onClick={() => setSelectedItem(item)}
                className={`flex items-center gap-3 py-2.5 px-3 rounded-lg transition-colors cursor-pointer ${
                  selectedItem?.id === item.id
                    ? 'bg-accent/10 border border-accent/20'
                    : 'hover:bg-surface-secondary/50'
                }`}
              >
                <div className="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center">
                  <FileText className="w-4 h-4 text-accent" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-body-sm font-medium text-content-primary truncate">
                    {item.title}
                  </p>
                  <p className="text-body-xs text-content-tertiary truncate">
                    {item.prompt_type} · {item.difficulty}
                  </p>
                </div>
              </div>
            ))}
            {filteredItems.length === 0 && (
              <EmptyState
                icon={<FileText className="w-5 h-5" />}
                title="No prompt items found"
                description={search ? 'Try adjusting your search' : 'Create your first prompt item to get started'}
              />
            )}
          </div>
        </Card>

        <Card className="lg:col-span-2 flex flex-col gap-4">
          {selectedItem ? (
            <>
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-display text-body-md font-semibold text-content-primary">
                    {selectedItem.title}
                  </h3>
                  <p className="text-body-xs text-content-tertiary font-mono">
                    {selectedItem.id}
                  </p>
                </div>
                <Button
                  variant="secondary"
                  size="sm"
                  icon={<Trash2 className="w-4 h-4" />}
                  onClick={() => handleDeletePromptItem(selectedItem.id)}
                >
                  Delete
                </Button>
              </div>

              <div className="flex gap-2 flex-wrap">
                <Badge variant="default" size="sm">{selectedItem.prompt_type}</Badge>
                <Badge variant="default" size="sm">{selectedItem.difficulty}</Badge>
                <Badge variant="default" size="sm">{selectedItem.lifecycle_state}</Badge>
              </div>

              <div className="p-4 rounded-lg bg-surface-secondary/50 border border-line">
                <h4 className="text-body-sm font-medium text-content-secondary mb-2">Prompt Text</h4>
                <p className="text-body-sm text-content-primary whitespace-pre-wrap">
                  {selectedItem.prompt_text}
                </p>
              </div>

              <div className="p-4 rounded-lg bg-surface-secondary/50 border border-line">
                <h4 className="text-body-sm font-medium text-content-secondary mb-2">Rubric ID</h4>
                <p className="text-body-sm text-content-primary font-mono">
                  {selectedItem.rubric_id}
                </p>
              </div>

              {selectedItem.target_skill_slugs.length > 0 && (
                <div className="p-4 rounded-lg bg-surface-secondary/50 border border-line">
                  <h4 className="text-body-sm font-medium text-content-secondary mb-2">Target Skills</h4>
                  <div className="flex flex-wrap gap-2">
                    {selectedItem.target_skill_slugs.map((slug) => (
                      <Badge key={slug} variant="default" size="sm">{slug}</Badge>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : (
            <div className="flex items-center justify-center py-16">
              <p className="text-body-sm text-content-tertiary">
                Select a prompt item to view details
              </p>
            </div>
          )}
        </Card>
      </div>

      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-md flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h3 className="font-display text-display-xs text-content-primary">New Prompt Item</h3>
              <button onClick={() => setShowCreateModal(false)} className="p-1 rounded hover:bg-surface-secondary">
                <X className="w-5 h-5 text-content-tertiary" />
              </button>
            </div>
            <div className="flex flex-col gap-3">
              <div>
                <label className="text-body-sm text-content-secondary mb-1 block">Title</label>
                <input
                  type="text"
                  value={newItem.title}
                  onChange={(e) => setNewItem({ ...newItem, title: e.target.value })}
                  placeholder="Prompt item title"
                  className="w-full px-3 py-2 rounded-lg border border-line bg-surface-primary text-content-primary placeholder:text-content-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50"
                />
              </div>
              <div>
                <label className="text-body-sm text-content-secondary mb-1 block">Prompt Text</label>
                <textarea
                  value={newItem.prompt_text}
                  onChange={(e) => setNewItem({ ...newItem, prompt_text: e.target.value })}
                  placeholder="Enter the prompt text..."
                  rows={4}
                  className="w-full px-3 py-2 rounded-lg border border-line bg-surface-primary text-content-primary placeholder:text-content-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50 resize-none"
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-body-sm text-content-secondary mb-1 block">Prompt Type</label>
                  <select
                    value={newItem.prompt_type}
                    onChange={(e) => setNewItem({ ...newItem, prompt_type: e.target.value as typeof newItem.prompt_type })}
                    className="w-full px-3 py-2 rounded-lg border border-line bg-surface-primary text-content-primary focus:outline-none focus:ring-2 focus:ring-accent/50"
                  >
                    <option value="quick_practice">Quick Practice</option>
                    <option value="interview">Interview</option>
                    <option value="scenario">Scenario</option>
                  </select>
                </div>
                <div>
                  <label className="text-body-sm text-content-secondary mb-1 block">Difficulty</label>
                  <select
                    value={newItem.difficulty}
                    onChange={(e) => setNewItem({ ...newItem, difficulty: e.target.value as Difficulty })}
                    className="w-full px-3 py-2 rounded-lg border border-line bg-surface-primary text-content-primary focus:outline-none focus:ring-2 focus:ring-accent/50"
                  >
                    <option value="beginner">Beginner</option>
                    <option value="intermediate">Intermediate</option>
                    <option value="advanced">Advanced</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="text-body-sm text-content-secondary mb-1 block">Rubric ID</label>
                <input
                  type="text"
                  value={newItem.rubric_id}
                  onChange={(e) => setNewItem({ ...newItem, rubric_id: e.target.value })}
                  placeholder="rubric-id"
                  className="w-full px-3 py-2 rounded-lg border border-line bg-surface-primary text-content-primary placeholder:text-content-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50"
                />
              </div>
              <div>
                <label className="text-body-sm text-content-secondary mb-1 block">Target Skill Slugs (comma-separated)</label>
                <input
                  type="text"
                  value={newItem.target_skill_slugs}
                  onChange={(e) => setNewItem({ ...newItem, target_skill_slugs: e.target.value })}
                  placeholder="skill-1, skill-2"
                  className="w-full px-3 py-2 rounded-lg border border-line bg-surface-primary text-content-primary placeholder:text-content-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="secondary" onClick={() => setShowCreateModal(false)}>Cancel</Button>
              <Button onClick={handleCreatePromptItem} loading={actionLoading} icon={<Check className="w-4 h-4" />}>
                Create
              </Button>
            </div>
          </Card>
        </div>
      )}
    </AdminPageShell>
  );
}
