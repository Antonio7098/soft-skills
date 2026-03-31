import { useEffect, useState, useMemo } from 'react';
import { 
  FileText,
  Plus,
  ChevronRight,
  ChevronDown,
  X,
  Check,
  Code,
  AlertCircle,
} from 'lucide-react';
import { Card } from '@/design-system/primitives/Card';
import { Button } from '@/design-system/primitives/Button';
import { Badge } from '@/design-system/primitives/Badge';
import { LoadingState } from '@/design-system/patterns/LoadingState';
import { useData } from '@/data';
import { AdminPageShell, MetricCard, SearchInput, StatusBadge } from '../components';
import type { PromptSummaryView, PromptVersionView } from '@/data/types';

// Extract variables from template using {{variable}} syntax
function extractVariables(template: string): string[] {
  const matches = template.match(/\{\{(\w+)\}\}/g);
  if (!matches) return [];
  return [...new Set(matches.map((m) => m.slice(2, -2)))].sort();
}

// Component to render template with highlighted variables
function TemplateWithHighlights({ template }: { template: string }) {
  const parts = template.split(/(\{\{\w+\}\})/g);
  return (
    <pre className="whitespace-pre-wrap font-mono text-body-sm text-content-primary">
      {parts.map((part, i) => {
        const isVariable = /^\{\{\w+\}\}$/.test(part);
        if (isVariable) {
          return (
            <span
              key={i}
              className="bg-accent/20 text-accent font-semibold px-1 py-0.5 rounded"
            >
              {part}
            </span>
          );
        }
        return <span key={i}>{part}</span>;
      })}
    </pre>
  );
}

export function AdminPrompts() {
  const dataProvider = useData();
  const [prompts, setPrompts] = useState<PromptSummaryView[]>([]);
  const [versions, setVersions] = useState<Record<string, PromptVersionView[]>>({});
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [expandedPrompts, setExpandedPrompts] = useState<Set<string>>(new Set());
  const [selectedVersion, setSelectedVersion] = useState<PromptVersionView | null>(null);
  const [showVersionModal, setShowVersionModal] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showCreateVersionModal, setShowCreateVersionModal] = useState(false);
  const [selectedPromptName, setSelectedPromptName] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [newPrompt, setNewPrompt] = useState({ name: '', prompt_type: 'assessment', description: '' });
  const [newVersion, setNewVersion] = useState<{
    template: string;
    variables: Record<string, string>;
  }>({ template: '', variables: {} });

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

  const loadVersions = async (promptName: string) => {
    if (versions[promptName]) return; // Already loaded
    try {
      const promptVersions = await dataProvider.listPromptVersions(promptName);
      setVersions((prev) => ({ ...prev, [promptName]: promptVersions }));
    } catch (error) {
      console.error('Failed to load versions:', error);
    }
  };

  const toggleExpand = (promptName: string) => {
    setExpandedPrompts((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(promptName)) {
        newSet.delete(promptName);
      } else {
        newSet.add(promptName);
        loadVersions(promptName);
      }
      return newSet;
    });
  };

  const handleCreatePrompt = async () => {
    if (!newPrompt.name) return;
    setActionLoading(true);
    try {
      await dataProvider.createPrompt({
        name: newPrompt.name,
        version: '1.0.0',
        prompt_type: newPrompt.prompt_type,
        template: 'New prompt template with {{variable}} placeholders',
        variables_schema: { type: 'object', properties: {} },
      });
      setShowCreateModal(false);
      setNewPrompt({ name: '', prompt_type: 'assessment', description: '' });
      refreshPrompts();
    } catch (error) {
      console.error('Failed to create prompt:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const handleCreateVersion = async () => {
    if (!selectedPromptName || !newVersion.template) return;
    setActionLoading(true);
    try {
      // Get parent version ID if available
      const promptVersions = versions[selectedPromptName] || [];
      const parentVersion = promptVersions[0];
      
      await dataProvider.createPrompt({
        name: selectedPromptName,
        version: '1.0.0', // Will be auto-incremented by backend
        prompt_type: parentVersion?.prompt_type || 'assessment',
        template: newVersion.template,
        variables_schema: { type: 'object', properties: {} },
        parent_version_id: parentVersion?.id || null,
      });
      setShowCreateVersionModal(false);
      setNewVersion({ template: '', variables: {} });
      loadVersions(selectedPromptName);
    } catch (error) {
      console.error('Failed to create version:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const openVersionModal = (version: PromptVersionView) => {
    setSelectedVersion(version);
    setShowVersionModal(true);
  };

  const openCreateVersionModal = (promptName: string) => {
    setSelectedPromptName(promptName);
    const promptVersions = versions[promptName] || [];
    const latestVersion = promptVersions[0];
    
    // Pre-fill with parent template if available
    const template = latestVersion?.template || '';
    const variables = extractVariables(template);
    const initialVariableValues = Object.fromEntries(variables.map((v) => [v, '']));
    
    setNewVersion({
      template,
      variables: initialVariableValues,
    });
    setShowCreateVersionModal(true);
  };

  const filteredPrompts = useMemo(() => {
    if (!search) return prompts;
    return prompts.filter((p) => 
      p.name.toLowerCase().includes(search.toLowerCase()) ||
      p.prompt_type.toLowerCase().includes(search.toLowerCase())
    );
  }, [prompts, search]);

  const publishedCount = prompts.filter((p) => p.status === 'published').length;
  const draftCount = prompts.filter((p) => p.status === 'draft').length;

  // Get required variables for template being edited
  const requiredVariables = useMemo(() => {
    if (!newVersion.template) return [];
    return extractVariables(newVersion.template);
  }, [newVersion.template]);

  if (loading) {
    return (
      <AdminPageShell title="System Prompts" subtitle="Manage LLM system prompts and versions">
        <LoadingState message="Loading prompts..." />
      </AdminPageShell>
    );
  }

  return (
    <AdminPageShell
      title="System Prompts"
      subtitle="Manage LLM system prompts, versions, and templates"
      actions={
        <Button icon={<Plus className="w-4 h-4" />} onClick={() => setShowCreateModal(true)}>
          New Base Prompt
        </Button>
      }
    >
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Total Base Prompts"
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
          icon={<Code className="w-4 h-4" />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Base Prompts List */}
        <Card className="lg:col-span-1 flex flex-col gap-4">
          <SearchInput
            value={search}
            onChange={setSearch}
            placeholder="Search base prompts..."
          />
          <div className="flex flex-col gap-1">
            {filteredPrompts.map((prompt) => {
              const isExpanded = expandedPrompts.has(prompt.name);
              const promptVersions = versions[prompt.name] || [];
              
              return (
                <div key={prompt.name} className="flex flex-col">
                  {/* Base Prompt Header */}
                  <div
                    onClick={() => toggleExpand(prompt.name)}
                    className="flex items-center gap-3 py-3 px-3 rounded-lg hover:bg-surface-secondary/50 transition-colors cursor-pointer"
                  >
                    {isExpanded ? (
                      <ChevronDown className="w-4 h-4 text-content-tertiary flex-shrink-0" />
                    ) : (
                      <ChevronRight className="w-4 h-4 text-content-tertiary flex-shrink-0" />
                    )}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-content-primary truncate">
                          {prompt.name}
                        </span>
                        <StatusBadge status={prompt.status as 'draft' | 'published' | 'archived'} />
                      </div>
                      <div className="flex items-center gap-2 text-body-xs text-content-tertiary">
                        <span>{prompt.prompt_type}</span>
                        <span>·</span>
                        <span>v{prompt.latest_version}</span>
                        <span>·</span>
                        <span>{promptVersions.length} version{promptVersions.length !== 1 ? 's' : ''}</span>
                      </div>
                    </div>
                  </div>
                  
                  {/* Versions List (when expanded) */}
                  {isExpanded && (
                    <div className="ml-7 flex flex-col gap-1 border-l-2 border-line pl-4">
                      {promptVersions.length === 0 && (
                        <div className="py-2 text-body-xs text-content-tertiary">
                          Loading versions...
                        </div>
                      )}
                      {promptVersions.map((version) => (
                        <div
                          key={version.id}
                          onClick={() => openVersionModal(version)}
                          className="flex items-center gap-2 py-2 px-3 rounded-lg hover:bg-accent/5 transition-colors cursor-pointer"
                        >
                          <Badge variant="default" size="sm">v{version.version}</Badge>
                          <span className="text-body-sm text-content-secondary">
                            {new Date(version.created_at).toLocaleDateString()}
                          </span>
                          <StatusBadge status={version.status as 'draft' | 'published' | 'archived'} />
                        </div>
                      ))}
                      <Button
                        variant="ghost"
                        size="sm"
                        icon={<Plus className="w-3 h-3" />}
                        onClick={(e) => {
                          e.stopPropagation();
                          openCreateVersionModal(prompt.name);
                        }}
                        className="mt-1 justify-start"
                      >
                        Add Version
                      </Button>
                    </div>
                  )}
                </div>
              );
            })}
            {filteredPrompts.length === 0 && (
              <div className="py-8 text-center text-body-sm text-content-tertiary">
                No prompts found
              </div>
            )}
          </div>
        </Card>

        {/* Prompt Details / Empty State */}
        <Card className="lg:col-span-2 flex flex-col">
          {!selectedVersion ? (
            <div className="flex-1 flex items-center justify-center py-16">
              <div className="text-center">
                <FileText className="w-12 h-12 text-content-tertiary mx-auto mb-4" />
                <p className="text-body-md font-medium text-content-secondary mb-2">
                  Select a version to view details
                </p>
                <p className="text-body-sm text-content-tertiary max-w-xs">
                  Click on a base prompt to expand it, then click on a version to see the template
                </p>
              </div>
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-display text-display-xs text-content-primary mb-1">
                    {selectedVersion.name}
                  </h3>
                  <div className="flex items-center gap-3 text-body-sm text-content-secondary">
                    <Badge variant="default">v{selectedVersion.version}</Badge>
                    <StatusBadge status={selectedVersion.status as 'draft' | 'published' | 'archived'} />
                    <span>{selectedVersion.prompt_type}</span>
                  </div>
                </div>
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => setSelectedVersion(null)}
                >
                  Close
                </Button>
              </div>

              {/* Variables Section */}
              {extractVariables(selectedVersion.template).length > 0 && (
                <div className="p-3 rounded-lg bg-surface-secondary/50 border border-line">
                  <h4 className="text-body-sm font-medium text-content-secondary mb-2 flex items-center gap-2">
                    <Code className="w-4 h-4" />
                    Required Variables ({extractVariables(selectedVersion.template).length})
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {extractVariables(selectedVersion.template).map((variable) => (
                      <Badge
                        key={variable}
                        variant="accent"
                        size="sm"
                        className="font-mono"
                      >
                        {`{{${variable}}}`}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* Template Section */}
              <div className="flex-1 flex flex-col gap-2">
                <h4 className="text-body-sm font-medium text-content-secondary">Template</h4>
                <div className="p-4 rounded-lg bg-surface-secondary/50 border border-line overflow-auto max-h-[60vh]">
                  <TemplateWithHighlights template={selectedVersion.template} />
                </div>
              </div>

              {/* Variables Schema (if available) */}
              {selectedVersion.variables_schema && Object.keys(selectedVersion.variables_schema.properties || {}).length > 0 && (
                <div className="p-3 rounded-lg bg-surface-secondary/50 border border-line">
                  <h4 className="text-body-sm font-medium text-content-secondary mb-2">Variables Schema</h4>
                  <pre className="text-body-xs text-content-tertiary overflow-auto">
                    {JSON.stringify(selectedVersion.variables_schema, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </Card>
      </div>

      {/* Create Base Prompt Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-md flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h3 className="font-display text-display-xs text-content-primary">New Base Prompt</h3>
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
                  <option value="quick_practice">Quick Practice</option>
                  <option value="interview">Interview</option>
                  <option value="scenario">Scenario</option>
                </select>
              </div>
              <div>
                <label className="text-body-sm text-content-secondary mb-1 block">Description</label>
                <input
                  type="text"
                  value={newPrompt.description}
                  onChange={(e) => setNewPrompt({ ...newPrompt, description: e.target.value })}
                  placeholder="Brief description of this prompt's purpose"
                  className="w-full px-3 py-2 rounded-lg border border-line bg-surface-primary text-content-primary placeholder:text-content-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50"
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

      {/* Create Version Modal */}
      {showCreateVersionModal && selectedPromptName && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-2xl flex flex-col gap-4 max-h-[80vh] overflow-hidden">
            <div className="flex items-center justify-between">
              <h3 className="font-display text-display-xs text-content-primary">
                New Version: {selectedPromptName}
              </h3>
              <button 
                onClick={() => setShowCreateVersionModal(false)} 
                className="p-1 rounded hover:bg-surface-secondary"
              >
                <X className="w-5 h-5 text-content-tertiary" />
              </button>
            </div>

            {/* Required Variables Alert */}
            {requiredVariables.length > 0 && (
              <div className="p-3 rounded-lg bg-accent/5 border border-accent/20">
                <div className="flex items-center gap-2 mb-2">
                  <AlertCircle className="w-4 h-4 text-accent" />
                  <span className="text-body-sm font-medium text-content-primary">
                    Required Variables
                  </span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {requiredVariables.map((variable) => (
                    <Badge
                      key={variable}
                      variant="accent"
                      size="sm"
                      className="font-mono"
                    >
                      {`{{${variable}}}`}
                    </Badge>
                  ))}
                </div>
                <p className="text-body-xs text-content-secondary mt-2">
                  These variables are detected in your template and will be highlighted
                </p>
              </div>
            )}

            {/* Template Editor */}
            <div className="flex flex-col gap-2 flex-1 overflow-hidden">
              <label className="text-body-sm text-content-secondary">Template</label>
              <textarea
                value={newVersion.template}
                onChange={(e) => setNewVersion({ ...newVersion, template: e.target.value })}
                placeholder="Enter prompt template with {{variable}} placeholders..."
                rows={12}
                className="w-full px-3 py-2 rounded-lg border border-line bg-surface-primary text-content-primary placeholder:text-content-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50 resize-none font-mono text-body-sm flex-1"
              />
            </div>

            {/* Live Preview of Variables */}
            {newVersion.template && (
              <div className="p-3 rounded-lg bg-surface-secondary/50 border border-line">
                <h4 className="text-body-sm font-medium text-content-secondary mb-2">
                  Variable Preview
                </h4>
                <div className="flex flex-wrap gap-2">
                  {requiredVariables.length === 0 ? (
                    <span className="text-body-xs text-content-tertiary">
                      No variables detected. Add variables using {'{{'}variable_name{'}}'} syntax.
                    </span>
                  ) : (
                    requiredVariables.map((variable) => (
                      <div key={variable} className="flex items-center gap-2">
                        <Badge
                          variant="accent"
                          size="sm"
                          className="font-mono"
                        >
                          {`{{${variable}}}`}
                        </Badge>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}

            <div className="flex justify-end gap-2 pt-2 border-t border-line">
              <Button variant="secondary" onClick={() => setShowCreateVersionModal(false)}>
                Cancel
              </Button>
              <Button 
                onClick={handleCreateVersion} 
                loading={actionLoading} 
                icon={<Check className="w-4 h-4" />}
              >
                Create Version
              </Button>
            </div>
          </Card>
        </div>
      )}

      {/* Version Detail Modal */}
      {showVersionModal && selectedVersion && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <Card className="w-full max-w-3xl max-h-[85vh] flex flex-col gap-4 overflow-hidden">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-display text-display-xs text-content-primary">{selectedVersion.name}</h3>
                <p className="text-body-sm text-content-tertiary">Version {selectedVersion.version}</p>
              </div>
              <button 
                onClick={() => { setShowVersionModal(false); setSelectedVersion(null); }} 
                className="p-1 rounded hover:bg-surface-secondary"
              >
                <X className="w-5 h-5 text-content-tertiary" />
              </button>
            </div>
            <div className="flex items-center gap-2">
              <StatusBadge status={selectedVersion.status as 'draft' | 'published' | 'archived'} />
              <span className="text-body-xs text-content-tertiary">
                Created {new Date(selectedVersion.created_at).toLocaleString()}
              </span>
            </div>

            {/* Variables */}
            {extractVariables(selectedVersion.template).length > 0 && (
              <div className="p-3 rounded-lg bg-accent/5 border border-accent/20">
                <h4 className="text-body-sm font-medium text-content-secondary mb-2 flex items-center gap-2">
                  <Code className="w-4 h-4" />
                  Variables ({extractVariables(selectedVersion.template).length})
                </h4>
                <div className="flex flex-wrap gap-2">
                  {extractVariables(selectedVersion.template).map((variable) => (
                    <Badge
                      key={variable}
                      variant="accent"
                      size="sm"
                      className="font-mono"
                    >
                      {`{{${variable}}}`}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {/* Template */}
            <div className="flex flex-col gap-2 overflow-y-auto flex-1">
              <h4 className="text-body-sm font-medium text-content-secondary">Template</h4>
              <div className="p-4 rounded-lg bg-surface-secondary/50 border border-line">
                <TemplateWithHighlights template={selectedVersion.template} />
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-line">
              <Button variant="secondary" onClick={() => { setShowVersionModal(false); setSelectedVersion(null); }}>
                Close
              </Button>
            </div>
          </Card>
        </div>
      )}
    </AdminPageShell>
  );
}
