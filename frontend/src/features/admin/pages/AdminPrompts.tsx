import { useEffect, useState } from 'react';
import { 
  FileText,
  Plus,
  GitCompare,
  BarChart3,
  ChevronRight,
} from 'lucide-react';
import { Card } from '@/design-system/primitives/Card';
import { Button } from '@/design-system/primitives/Button';
import { Badge } from '@/design-system/primitives/Badge';
import { LoadingState } from '@/design-system/patterns/LoadingState';
import { useData } from '@/data';
import { AdminPageShell, MetricCard, DataTable, SearchInput, StatusBadge } from '../components';
import type { PromptSummaryView, PromptVersionView } from '@/data/types';

export function AdminPrompts() {
  const dataProvider = useData();
  const [prompts, setPrompts] = useState<PromptSummaryView[]>([]);
  const [selectedPrompt, setSelectedPrompt] = useState<string | null>(null);
  const [versions, setVersions] = useState<PromptVersionView[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  useEffect(() => {
    setLoading(true);
    dataProvider.listPrompts()
      .then(setPrompts)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [dataProvider]);

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
          <Button variant="secondary" icon={<GitCompare className="w-4 h-4" />}>
            Compare
          </Button>
          <Button icon={<Plus className="w-4 h-4" />}>
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
    </AdminPageShell>
  );
}
