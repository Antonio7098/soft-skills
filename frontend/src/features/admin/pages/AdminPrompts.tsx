import { useEffect, useState } from 'react';
import { 
  FileText,
  Plus,
  GitCompare,
  BarChart3,
  ChevronRight,
  X,
  Check,
} from 'lucide-react';
import { Card } from '@/design-system/primitives/Card';
import { Button } from '@/design-system/primitives/Button';
import { Badge } from '@/design-system/primitives/Badge';
import { LoadingState } from '@/design-system/patterns/LoadingState';
import { useData } from '@/data';
import { AdminPageShell, MetricCard, DataTable, SearchInput, StatusBadge, FilterSelect } from '../components';
import type { PromptSummaryView, PromptVersionView, PromptCompareView } from '@/data/types';

export function AdminPrompts() {
  const dataProvider = useData();
  const [prompts, setPrompts] = useState<PromptSummaryView[]>([]);
  const [selectedPrompt, setSelectedPrompt] = useState<string | null>(null);
  const [versions, setVersions] = useState<PromptVersionView[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showCompareModal, setShowCompareModal] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [newPrompt, setNewPrompt] = useState({ name: '', prompt_type: 'assessment', template: '' });
  const [compareVersionA, setCompareVersionA] = useState('');
  const [compareVersionB, setCompareVersionB] = useState('');
  const [compareResult, setCompareResult] = useState<PromptCompareView | null>(null);
  const [showVersionModal, setShowVersionModal] = useState(false);
  const [selectedVersion, setSelectedVersion] = useState<PromptVersionView | null>(null);

  const refreshPrompts = () => {
    setLoading(true);
    dataProvider.listPrompts()
      .then(setPrompts)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    refreshPrompts();
  }, [dataProvider]);

  const handleCreatePrompt = async () => {
    if (!newPrompt.name || !newPrompt.template) return;
    setActionLoading(true);
    try {
      await dataProvider.createPrompt({
        name: newPrompt.name,
        version: '1.0',
        prompt_type: newPrompt.prompt_type,
        template: newPrompt.template,
        variables_schema: { type: 'object', properties: {} },
      });
      setShowCreateModal(false);
      setNewPrompt({ name: '', prompt_type: 'assessment', template: '' });
      refreshPrompts();
    } catch (error) {
      console.error('Failed to create prompt:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const handleCompare = async () => {
    if (!selectedPrompt || !compareVersionA || !compareVersionB) return;
    setActionLoading(true);
    try {
      const result = await dataProvider.comparePrompts({
        name: selectedPrompt,
        version_a: compareVersionA,
        version_b: compareVersionB,
      });
      setCompareResult(result);
    } catch (error) {
      console.error('Failed to compare prompts:', error);
    } finally {
      setActionLoading(false);
    }
  };

  useEffect(() => {
    if (selectedPrompt) {
      dataProvider.listPromptVersions(selectedPrompt)
        .then(setVersions)
        .catch(console.error);
    } else {
      setVersions([]);
    }
  }, [dataProvider, selectedPrompt]);

  const filteredPrompts = prompts.filter((p) =>
    search ? p.name.toLowerCase().includes(search.toLowerCase()) : true
  );

  const publishedCount = prompts.filter((p) => p.status === 'published').length;
  const draftCount = prompts.filter((p) => p.status === 'draft').length;

  const columns = [
    {
      key: 'name',
      header: 'Prompt',
      render: (prompt: PromptSummaryView) => (
        <div className="flex flex-col gap-0.5">
          <span className="font-medium">{prompt.name}</span>
          <span className="text-body-xs text-content-tertiary">{prompt.prompt_type}</span>
        </div>
      ),
    },
    {
      key: 'latest_version',
      header: 'Version',
      width: '100px',
      render: (prompt: PromptSummaryView) => (
        <Badge variant="default" size="sm">v{prompt.latest_version}</Badge>
      ),
    },
    {
      key: 'status',
      header: 'Status',
      width: '100px',
      render: (prompt: PromptSummaryView) => (
        <StatusBadge status={prompt.status as 'draft' | 'published' | 'archived'} />
      ),
    },
    {
      key: 'created_at',
      header: 'Created',
      width: '120px',
      render: (prompt: PromptSummaryView) => (
        <span className="text-content-secondary">
          {new Date(prompt.created_at).toLocaleDateString()}
        </span>
      ),
    },
    {
      key: 'actions',
      header: '',
      width: '48px',
      render: () => (
        <ChevronRight className="w-4 h-4 text-content-tertiary" />
      ),
    },
  ];

  if (loading) {
    return (
      <AdminPageShell title="Prompts" subtitle="Prompt template management">
        <LoadingState message="Loading prompts..." />
      </AdminPageShell>
    );
  }

  return (
    <AdminPageShell
      title="Prompts"
      subtitle="Manage prompt templates, versions, and A/B testing"
      actions={
        <div className="flex items-center gap-2">
          <Button 
            variant="secondary" 
            icon={<GitCompare className="w-4 h-4" />}
            onClick={() => setShowCompareModal(true)}
            disabled={!selectedPrompt || versions.length < 2}
          >
            Compare
          </Button>
          <Button icon={<Plus className="w-4 h-4" />} onClick={() => setShowCreateModal(true)}>
            New Prompt
          </Button>
        </div>
      }
    >
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Total Prompts"
          value={prompts.length}
          icon={<FileText className="w-4 h-4" />}
        />
        <MetricCard
          label="Published"
          value={publishedCount}
          trend="positive"
        />
        <MetricCard
          label="Drafts"
          value={draftCount}
        />
        <MetricCard
          label="Prompt Types"
          value={new Set(prompts.map((p) => p.prompt_type)).size}
          icon={<BarChart3 className="w-4 h-4" />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2 flex flex-col gap-4">
          <div className="flex items-center gap-3">
            <SearchInput
              value={search}
              onChange={setSearch}
              placeholder="Search prompts..."
              className="w-64"
            />
            <div className="flex-1" />
            <span className="text-body-xs text-content-tertiary">
              {filteredPrompts.length} prompts
            </span>
          </div>
          <DataTable
            columns={columns}
            data={filteredPrompts}
            keyExtractor={(prompt) => prompt.name}
            onRowClick={(prompt) => setSelectedPrompt(prompt.name)}
            emptyMessage="No prompts found"
          />
        </Card>

        <Card className="flex flex-col gap-4">
          <h3 className="font-display text-body-md font-semibold text-content-primary">
            {selectedPrompt ? `${selectedPrompt} Versions` : 'Select a Prompt'}
          </h3>
          {selectedPrompt && versions.length > 0 ? (
            <div className="flex flex-col gap-2">
              {versions.map((version) => (
                <div 
                  key={version.id}
                  onClick={() => { setSelectedVersion(version); setShowVersionModal(true); }}
                  className="flex items-center gap-3 py-2.5 px-3 rounded-lg hover:bg-surface-secondary/50 transition-colors cursor-pointer"
                >
                  <div className="w-8 h-8 rounded-lg bg-accent/10 flex items-center justify-center">
                    <span className="text-body-xs font-semibold text-accent">v{version.version}</span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-body-sm font-medium text-content-primary">
                      Version {version.version}
                    </p>
                    <p className="text-body-xs text-content-tertiary">
                      {new Date(version.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <StatusBadge status={version.status as 'draft' | 'published' | 'archived'} />
                </div>
              ))}
            </div>
          ) : (
            <p className="text-body-sm text-content-tertiary py-8 text-center">
              {selectedPrompt ? 'No versions found' : 'Click a prompt to view versions'}
            </p>
          )}
        </Card>
      </div>

      {/* Create Prompt Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-lg flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h3 className="font-display text-display-xs text-content-primary">New Prompt</h3>
              <button onClick={() => setShowCreateModal(false)} className="p-1 rounded hover:bg-surface-secondary">
                <X className="w-5 h-5 text-content-tertiary" />
              </button>
            </div>
            <div className="flex flex-col gap-3">
              <div>
                <label className="text-body-sm text-content-secondary mb-1 block">Name</label>
                <input
                  type="text"
                  value={newPrompt.name}
                  onChange={(e) => setNewPrompt({ ...newPrompt, name: e.target.value })}
                  placeholder="prompt-name"
                  className="w-full px-3 py-2 rounded-lg border border-line bg-surface-primary text-content-primary placeholder:text-content-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50"
                />
              </div>
              <div>
                <label className="text-body-sm text-content-secondary mb-1 block">Type</label>
                <select
                  value={newPrompt.prompt_type}
                  onChange={(e) => setNewPrompt({ ...newPrompt, prompt_type: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border border-line bg-surface-primary text-content-primary focus:outline-none focus:ring-2 focus:ring-accent/50"
                >
                  <option value="assessment">Assessment</option>
                  <option value="generation">Generation</option>
                  <option value="feedback">Feedback</option>
                  <option value="system">System</option>
                </select>
              </div>
              <div>
                <label className="text-body-sm text-content-secondary mb-1 block">Template</label>
                <textarea
                  value={newPrompt.template}
                  onChange={(e) => setNewPrompt({ ...newPrompt, template: e.target.value })}
                  placeholder="Enter prompt template..."
                  rows={6}
                  className="w-full px-3 py-2 rounded-lg border border-line bg-surface-primary text-content-primary placeholder:text-content-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50 resize-none"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="secondary" onClick={() => setShowCreateModal(false)}>Cancel</Button>
              <Button onClick={handleCreatePrompt} loading={actionLoading} icon={<Check className="w-4 h-4" />}>
                Create
              </Button>
            </div>
          </Card>
        </div>
      )}

      {/* Compare Modal */}
      {showCompareModal && selectedPrompt && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-2xl flex flex-col gap-4 max-h-[80vh] overflow-auto">
            <div className="flex items-center justify-between">
              <h3 className="font-display text-display-xs text-content-primary">Compare Versions: {selectedPrompt}</h3>
              <button onClick={() => { setShowCompareModal(false); setCompareResult(null); }} className="p-1 rounded hover:bg-surface-secondary">
                <X className="w-5 h-5 text-content-tertiary" />
              </button>
            </div>
            <div className="flex items-center gap-4">
              <FilterSelect
                value={compareVersionA}
                onChange={setCompareVersionA}
                options={versions.map((v) => ({ value: v.version, label: `v${v.version}` }))}
                placeholder="Version A"
                className="flex-1"
              />
              <GitCompare className="w-5 h-5 text-content-tertiary" />
              <FilterSelect
                value={compareVersionB}
                onChange={setCompareVersionB}
                options={versions.map((v) => ({ value: v.version, label: `v${v.version}` }))}
                placeholder="Version B"
                className="flex-1"
              />
              <Button onClick={handleCompare} loading={actionLoading} size="sm">
                Compare
              </Button>
            </div>
            {compareResult && (
              <div className="flex flex-col gap-4 mt-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="flex flex-col gap-2">
                    <h4 className="text-body-sm font-medium text-content-secondary">Version A (v{compareResult.version_a.version})</h4>
                    <pre className="p-3 rounded-lg bg-surface-secondary/50 text-body-xs text-content-primary overflow-auto max-h-48">
                      {compareResult.version_a.template}
                    </pre>
                  </div>
                  <div className="flex flex-col gap-2">
                    <h4 className="text-body-sm font-medium text-content-secondary">Version B (v{compareResult.version_b.version})</h4>
                    <pre className="p-3 rounded-lg bg-surface-secondary/50 text-body-xs text-content-primary overflow-auto max-h-48">
                      {compareResult.version_b.template}
                    </pre>
                  </div>
                </div>
                {compareResult.diff_summary && (
                  <div className="p-3 rounded-lg bg-accent/5 border border-accent/20">
                    <h4 className="text-body-sm font-medium text-content-primary mb-2">Diff Summary</h4>
                    <p className="text-body-sm text-content-secondary">{compareResult.diff_summary}</p>
                  </div>
                )}
              </div>
            )}
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="secondary" onClick={() => { setShowCompareModal(false); setCompareResult(null); }}>Close</Button>
            </div>
          </Card>
        </div>
      )}

      {/* Version Detail Modal */}
      {showVersionModal && selectedVersion && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <Card className="w-full max-w-2xl max-h-[80vh] flex flex-col gap-4 overflow-hidden">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-display text-display-xs text-content-primary">{selectedPrompt}</h3>
                <p className="text-body-sm text-content-tertiary">Version {selectedVersion.version}</p>
              </div>
              <button onClick={() => { setShowVersionModal(false); setSelectedVersion(null); }} className="p-1 rounded hover:bg-surface-secondary">
                <X className="w-5 h-5 text-content-tertiary" />
              </button>
            </div>
            <div className="flex items-center gap-2">
              <StatusBadge status={selectedVersion.status as 'draft' | 'published' | 'archived'} />
              <span className="text-body-xs text-content-tertiary">
                Created {new Date(selectedVersion.created_at).toLocaleString()}
              </span>
            </div>
            <div className="flex flex-col gap-2 overflow-y-auto">
              <h4 className="text-body-sm font-medium text-content-secondary">Template</h4>
              <pre className="p-4 rounded-lg bg-surface-secondary/50 border border-line text-body-sm text-content-primary whitespace-pre-wrap overflow-auto max-h-[50vh] font-mono">
                {selectedVersion.template}
              </pre>
            </div>
            <div className="flex justify-end gap-2 pt-2 border-t border-line">
              <Button variant="secondary" onClick={() => { setShowVersionModal(false); setSelectedVersion(null); }}>Close</Button>
            </div>
          </Card>
        </div>
      )}
    </AdminPageShell>
  );
}
