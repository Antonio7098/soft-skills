import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, MessageSquare, Settings2, Zap, Target, Briefcase, FileText, Wand2, CheckCircle2, XCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { PageShell } from '@/design-system/patterns/PageShell';
import { Card } from '@/design-system/primitives/Card';
import { Button } from '@/design-system/primitives/Button';
import { Input } from '@/design-system/primitives/Input';
import { Textarea } from '@/design-system/primitives/Textarea';
import { Badge } from '@/design-system/primitives/Badge';
import { SectionHeader } from '@/design-system/patterns/SectionHeader';
import { useData, type Difficulty, type GenerationCounts, type TaxonomySnapshot } from '@/data';
import { useGenerationStream } from '@/hooks/useGenerationStream';
import { GenerationStreamPanel } from '@/features/generation';
import { cn } from '@/lib/cn';

type GenerationMode = 'structured' | 'chat';

const DIFFICULTY_OPTIONS: { value: Difficulty; label: string }[] = [
  { value: 'introductory', label: 'Beginner' },
  { value: 'intermediate', label: 'Intermediate' },
  { value: 'advanced', label: 'Advanced' },
];

interface CountConfigProps {
  label: string;
  description: string;
  value: number;
  min: number;
  max: number;
  onChange: (value: number) => void;
  icon: React.ReactNode;
  color: string;
}

function CountConfig({ label, description, value, min, max, onChange, icon, color }: CountConfigProps) {
  return (
    <div className="flex flex-col gap-3 p-4 rounded-card bg-surface-secondary/50 border border-line">
      <div className="flex items-center gap-3">
        <div className={cn('w-10 h-10 rounded-lg flex items-center justify-center', color)}>
          {icon}
        </div>
        <div className="flex flex-col gap-0.5">
          <span className="text-body-sm font-medium text-content-primary">{label}</span>
          <span className="text-body-xs text-content-secondary">{description}</span>
        </div>
      </div>
      <div className="flex items-center gap-3">
        <input
          type="range"
          min={min}
          max={max}
          value={value}
          onChange={(e) => onChange(parseInt(e.target.value, 10))}
          className="flex-1 accent-accent"
        />
        <div className="w-12 h-9 rounded-input bg-surface-elevated border border-line flex items-center justify-center">
          <span className="text-body-sm font-semibold text-content-primary">{value}</span>
        </div>
      </div>
    </div>
  );
}

function GenerationSuccessPage({ mode, collectionTitle }: { mode: GenerationMode; collectionTitle: string }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4 }}
      className="flex flex-col items-center justify-center min-h-[60vh] gap-6"
    >
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
        className="w-20 h-20 rounded-full bg-status-success/10 flex items-center justify-center"
      >
        <CheckCircle2 className="w-10 h-10 text-status-success" />
      </motion.div>
      <div className="flex flex-col items-center gap-2 text-center">
        <h2 className="font-display text-display-md text-content-primary">Collection Created!</h2>
        <p className="text-body-md text-content-secondary max-w-md">
          <span className="font-medium text-content-primary">"{collectionTitle}"</span> is ready with all requested content items.
        </p>
      </div>
      <Badge variant="success" size="md">
        {mode === 'structured' ? 'Structured' : 'Chat'} Generation Complete
      </Badge>
    </motion.div>
  );
}

function GenerationErrorPage({ error, onRetry }: { error: string | null; onRetry: () => void }) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.4 }}
      className="flex flex-col items-center justify-center min-h-[60vh] gap-6"
    >
      <motion.div
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        transition={{ delay: 0.2, type: 'spring', stiffness: 200 }}
        className="w-20 h-20 rounded-full bg-status-error/10 flex items-center justify-center"
      >
        <XCircle className="w-10 h-10 text-status-error" />
      </motion.div>
      <div className="flex flex-col items-center gap-2 text-center">
        <h2 className="font-display text-display-md text-content-primary">Generation Failed</h2>
        <p className="text-body-md text-content-secondary max-w-md">
          {error || 'Something went wrong while generating your collection.'}
        </p>
      </div>
      <div className="flex gap-3">
        <Badge variant="error" size="md">Generation Failed</Badge>
      </div>
      <Button variant="primary" size="md" onClick={onRetry}>
        Try Again
      </Button>
    </motion.div>
  );
}

export function Generate() {
  const navigate = useNavigate();
  const data = useData();
  const {
    state,
    startGeneration,
    cancelGeneration,
    reset,
    stageLabels,
  } = useGenerationStream({
    onComplete: (collection) => {
      if (collection) {
        setTimeout(() => {
          navigate(`/collections/${collection.id}`);
        }, 4000);
      }
    },
  });

  const [mode, setMode] = useState<GenerationMode>('structured');
  const [collectionTitle, setCollectionTitle] = useState<string>('');
  const [taxonomy, setTaxonomy] = useState<TaxonomySnapshot | null>(null);
  const [taxonomyError, setTaxonomyError] = useState<string | null>(null);
  const [isTaxonomyLoading, setIsTaxonomyLoading] = useState(true);

  const [structuredForm, setStructuredForm] = useState({
    title_hint: '',
    target_audience: 'Professionals looking to improve their consultancy skills',
    difficulty: 'intermediate' as Difficulty,
    domain: '',
    workplace_context: '',
    scenario_theme: '',
    realism_notes: '',
  });

  const [counts, setCounts] = useState<GenerationCounts>({
    quick_practice_prompt_count: 2,
    interview_prompt_count: 1,
    scenario_count: 1,
    scenario_artifact_count: 2,
  });

  const [chatForm, setChatForm] = useState({
    prompt: '',
    target_audience: 'Professionals looking to improve their consultancy skills',
    difficulty: 'intermediate' as Difficulty,
  });

  const isGenerationActive = state.status !== 'idle' && state.status !== 'failed';

  useEffect(() => {
    let cancelled = false;
    setIsTaxonomyLoading(true);
    data.getTaxonomy()
      .then((snapshot) => {
        if (cancelled) return;
        setTaxonomy(snapshot);
        setTaxonomyError(null);
      })
      .catch((err) => {
        if (cancelled) return;
        setTaxonomy(null);
        setTaxonomyError(err instanceof Error ? err.message : 'Failed to load skills catalog.');
      })
      .finally(() => {
        if (!cancelled) {
          setIsTaxonomyLoading(false);
        }
      });
    return () => {
      cancelled = true;
    };
  }, [data]);

  const buildGenerationDefaults = (): {
    target_skill_slugs: string[];
    target_competency_slugs: string[];
    rubric_ids: string[];
  } => {
    if (!taxonomy) {
      throw new Error('Skills catalog has not loaded yet.');
    }

    const competencies = taxonomy.competencies.filter((item) => item.skill_slugs.length > 0);
    if (competencies.length === 0) {
      throw new Error('No competencies are available for generation. Seed the taxonomy catalog first.');
    }

    const selectedCompetencies = competencies.slice(0, 2);
    const selectedSkills = Array.from(
      new Set(selectedCompetencies.flatMap((item) => item.skill_slugs))
    ).slice(0, 3);
    if (selectedSkills.length === 0) {
      throw new Error('No skills are mapped to the available competencies. Fix the taxonomy mappings before generating.');
    }

    const requiredRubricTypes = ['quick_practice_prompt', 'interview_prompt', 'scenario_step'];
    const rubricIds = requiredRubricTypes.map((contentType) => {
      const rubric = taxonomy.rubrics.find((item) => item.content_type === contentType);
      if (!rubric) {
        throw new Error(`No rubric is available for ${contentType}. Seed the taxonomy catalog first.`);
      }
      return rubric.rubric_id;
    });

    return {
      target_skill_slugs: selectedSkills,
      target_competency_slugs: selectedCompetencies.map((item) => item.slug),
      rubric_ids: rubricIds,
    };
  };

  const taxonomyStatusMessage = (() => {
    if (taxonomyError) return taxonomyError;
    if (!taxonomy) return null;
    if (taxonomy.skills.length === 0 || taxonomy.competencies.length === 0 || taxonomy.rubrics.length === 0) {
      return 'Generation is unavailable because the taxonomy catalog is empty. Seed skills, competencies, and rubrics first.';
    }
    const rubricTypes = new Set(taxonomy.rubrics.map((item) => item.content_type));
    if (!rubricTypes.has('quick_practice_prompt') || !rubricTypes.has('interview_prompt') || !rubricTypes.has('scenario_step')) {
      return 'Generation is unavailable because the rubric catalog does not cover quick practice, interview, and scenario content.';
    }
    return null;
  })();

  const handleStructuredGenerate = async () => {
    const defaults = buildGenerationDefaults();
    setCollectionTitle(structuredForm.title_hint || 'Generated Collection');
    await startGeneration({
      title_hint: structuredForm.title_hint || null,
      target_audience: structuredForm.target_audience,
      difficulty: structuredForm.difficulty,
      content_format_mix: ['quick_practice_prompt', 'interview_prompt', 'scenario_step'],
      target_skill_slugs: defaults.target_skill_slugs,
      target_competency_slugs: defaults.target_competency_slugs,
      rubric_ids: defaults.rubric_ids,
      domain: structuredForm.domain || 'Business Consulting',
      workplace_context: structuredForm.workplace_context || 'Corporate environment',
      scenario_theme: structuredForm.scenario_theme || 'Client engagement',
      realism_notes: structuredForm.realism_notes ? [structuredForm.realism_notes] : [],
      counts,
    });
  };

  const handleChatGenerate = async () => {
    const defaults = buildGenerationDefaults();
    setCollectionTitle('Generated from prompt');
    await startGeneration({
      prompt: chatForm.prompt,
      target_audience: chatForm.target_audience,
      difficulty: chatForm.difficulty,
      content_format_mix: ['quick_practice_prompt', 'interview_prompt', 'scenario_step'],
      target_skill_slugs: defaults.target_skill_slugs,
      target_competency_slugs: defaults.target_competency_slugs,
      rubric_ids: defaults.rubric_ids,
      counts,
    });
  };

  const modeTabs: { id: GenerationMode; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
    { id: 'structured', label: 'Structured', icon: Settings2 },
    { id: 'chat', label: 'Chat', icon: MessageSquare },
  ];

  if (state.status === 'failed') {
    return (
      <PageShell
        title="Generate Collection"
        subtitle="Generation could not be completed"
      >
        <GenerationErrorPage error={state.error} onRetry={reset} />
      </PageShell>
    );
  }

  if (isGenerationActive) {
    return (
      <PageShell
        title="Generate Collection"
        subtitle={state.status === 'completed' ? 'Your collection is ready' : 'Live generation progress'}
      >
        <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1.35fr)_420px] gap-6 items-start">
          <GenerationStreamPanel
            currentStage={state.current_stage}
            stagesCompleted={state.stages_completed}
            progress={state.progress_percent}
            status={state.status}
            stageLabels={stageLabels}
            blueprint={state.blueprint}
            promptItems={state.prompt_items}
            activity={state.activity}
            onCancel={cancelGeneration}
            error={state.error}
          />

          <Card variant="outlined" padding="lg" className="flex flex-col gap-4 min-h-[420px]">
            <SectionHeader
              title={state.status === 'completed' ? 'Collection Ready' : 'Generation Details'}
              subtitle={state.status === 'completed' ? 'Redirecting to the collection shortly' : 'Parameters being used for this collection'}
            />
            <div className="flex flex-col gap-3">
              <div className="flex items-center justify-between py-2 border-b border-line">
                <span className="text-body-sm text-content-secondary">Mode</span>
                <Badge variant="accent" size="sm">{mode}</Badge>
              </div>
              <div className="flex items-center justify-between py-2 border-b border-line">
                <span className="text-body-sm text-content-secondary">Difficulty</span>
                <span className="text-body-sm font-medium text-content-primary">
                  {mode === 'structured' ? structuredForm.difficulty : chatForm.difficulty}
                </span>
              </div>
              <div className="flex items-center justify-between py-2 border-b border-line">
                <span className="text-body-sm text-content-secondary">Quick Practice</span>
                <span className="text-body-sm font-medium text-content-primary">
                  {counts.quick_practice_prompt_count} items
                </span>
              </div>
              <div className="flex items-center justify-between py-2 border-b border-line">
                <span className="text-body-sm text-content-secondary">Interview Questions</span>
                <span className="text-body-sm font-medium text-content-primary">
                  {counts.interview_prompt_count} items
                </span>
              </div>
              <div className="flex items-center justify-between py-2">
                <span className="text-body-sm text-content-secondary">Scenarios</span>
                <span className="text-body-sm font-medium text-content-primary">
                  {counts.scenario_count} items
                </span>
              </div>
            </div>
            <div className="mt-auto pt-4">
              {state.status === 'completed' ? (
                <div className="rounded-xl border border-status-success/20 bg-status-success/5 p-4">
                  <GenerationSuccessPage mode={mode} collectionTitle={collectionTitle} />
                </div>
              ) : (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={reset}
                  className="w-full"
                >
                  Cancel Generation
                </Button>
              )}
            </div>
          </Card>
        </div>
      </PageShell>
    );
  }

  return (
    <PageShell
      title="Generate Collection"
      subtitle="Create AI-powered practice collections with targeted scenarios and questions."
      actions={
        <div className="flex items-center gap-2">
          <Badge variant="accent" size="md">
            <Sparkles className="w-3 h-3" />
            One-Shot Generation
          </Badge>
        </div>
      }
    >
      <AnimatePresence mode="wait">
        {(
          <motion.div
            key="form"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col gap-8"
          >
            <div className="flex items-center gap-2 border-b border-line pb-px">
              {modeTabs.map((tab) => {
                const Icon = tab.icon;
                const isActive = mode === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setMode(tab.id)}
                    className={cn(
                      'flex items-center gap-2 px-4 py-2.5 text-body-sm font-medium rounded-t-lg transition-all relative whitespace-nowrap',
                      isActive
                        ? 'text-accent'
                        : 'text-content-tertiary hover:text-content-secondary',
                    )}
                  >
                    <Icon className="w-4 h-4" />
                    {tab.label}
                    {isActive && (
                      <motion.div
                        layoutId="generate-tab-indicator"
                        className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent rounded-full"
                        transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                      />
                    )}
                  </button>
                );
              })}
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card variant="default" padding="lg" className="flex flex-col gap-6">
                <SectionHeader
                  title={mode === 'structured' ? 'Structured Parameters' : 'Describe Your Collection'}
                  subtitle={mode === 'structured' ? 'Fine-tune generation with specific parameters' : 'Tell us what kind of practice content you need'}
                />

                {mode === 'structured' ? (
                  <div className="flex flex-col gap-5">
                    <Input
                      label="Title Hint (optional)"
                      placeholder="e.g., Client Communication Mastery"
                      value={structuredForm.title_hint}
                      onChange={(e) => setStructuredForm({ ...structuredForm, title_hint: e.target.value })}
                    />
                    <Input
                      label="Domain"
                      placeholder="e.g., Management Consulting, Healthcare, Finance"
                      value={structuredForm.domain}
                      onChange={(e) => setStructuredForm({ ...structuredForm, domain: e.target.value })}
                    />
                    <Input
                      label="Workplace Context"
                      placeholder="e.g., Cross-functional team meetings, Client presentations"
                      value={structuredForm.workplace_context}
                      onChange={(e) => setStructuredForm({ ...structuredForm, workplace_context: e.target.value })}
                    />
                    <Input
                      label="Scenario Theme"
                      placeholder="e.g., Managing difficult conversations, Influencing stakeholders"
                      value={structuredForm.scenario_theme}
                      onChange={(e) => setStructuredForm({ ...structuredForm, scenario_theme: e.target.value })}
                    />
                    <Textarea
                      label="Realism Notes (optional)"
                      placeholder="Any specific context or constraints to make scenarios more realistic..."
                      value={structuredForm.realism_notes}
                      onChange={(e) => setStructuredForm({ ...structuredForm, realism_notes: e.target.value })}
                    />
                    <div className="flex flex-col gap-1.5">
                      <label className="text-body-sm font-medium text-content-primary">Difficulty</label>
                      <div className="flex gap-2">
                        {DIFFICULTY_OPTIONS.map((opt) => (
                          <button
                            key={opt.value}
                            onClick={() => setStructuredForm({ ...structuredForm, difficulty: opt.value })}
                            className={cn(
                              'flex-1 px-3 py-2 rounded-input text-body-sm font-medium transition-all border',
                              structuredForm.difficulty === opt.value
                                ? 'bg-accent-muted text-accent-text border-accent/30'
                                : 'bg-surface-secondary text-content-secondary border-line hover:border-line-hover',
                            )}
                          >
                            {opt.label}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col gap-5">
                    <Textarea
                      label="Describe your collection"
                      placeholder="e.g., I want practice scenarios for handling difficult conversations with stakeholders in a consulting context. Include interview-style questions and quick practice exercises..."
                      value={chatForm.prompt}
                      onChange={(e) => setChatForm({ ...chatForm, prompt: e.target.value })}
                      className="min-h-[200px]"
                    />
                    <div className="flex flex-col gap-1.5">
                      <label className="text-body-sm font-medium text-content-primary">Difficulty</label>
                      <div className="flex gap-2">
                        {DIFFICULTY_OPTIONS.map((opt) => (
                          <button
                            key={opt.value}
                            onClick={() => setChatForm({ ...chatForm, difficulty: opt.value })}
                            className={cn(
                              'flex-1 px-3 py-2 rounded-input text-body-sm font-medium transition-all border',
                              chatForm.difficulty === opt.value
                                ? 'bg-accent-muted text-accent-text border-accent/30'
                                : 'bg-surface-secondary text-content-secondary border-line hover:border-line-hover',
                            )}
                          >
                            {opt.label}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                )}

                <Card variant="outlined" padding="md" className="flex flex-col gap-2 bg-surface-secondary/40">
                  <div className="flex items-center justify-between gap-3">
                    <span className="text-body-sm font-medium text-content-primary">Catalog Readiness</span>
                    <Badge variant={taxonomyStatusMessage ? 'error' : 'success'} size="sm">
                      {isTaxonomyLoading ? 'Loading' : taxonomyStatusMessage ? 'Blocked' : 'Ready'}
                    </Badge>
                  </div>
                  <p className="text-body-sm text-content-secondary">
                    {isTaxonomyLoading
                      ? 'Loading skills, competencies, and rubrics.'
                      : taxonomyStatusMessage
                        ? taxonomyStatusMessage
                        : `Using ${taxonomy?.skills.length ?? 0} skills, ${taxonomy?.competencies.length ?? 0} competencies, and ${taxonomy?.rubrics.length ?? 0} rubrics from the live catalog.`}
                  </p>
                </Card>

                <Button
                  variant="primary"
                  size="lg"
                  icon={<Wand2 className="w-4 h-4" />}
                  onClick={mode === 'structured' ? handleStructuredGenerate : handleChatGenerate}
                  disabled={isTaxonomyLoading || Boolean(taxonomyStatusMessage) || (mode === 'chat' && !chatForm.prompt.trim())}
                  className="w-full mt-2"
                >
                  Generate Collection
                </Button>
              </Card>

              <div className="flex flex-col gap-6">
                <SectionHeader
                  title="Generation Counts"
                  subtitle="Specify how many of each content type to generate"
                />

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <CountConfig
                    label="Quick Practice"
                    description="Rapid skill exercises"
                    value={counts.quick_practice_prompt_count}
                    min={0}
                    max={3}
                    onChange={(v) => setCounts({ ...counts, quick_practice_prompt_count: v })}
                    icon={<Zap className="w-5 h-5 text-status-success" />}
                    color="bg-status-success/10"
                  />
                  <CountConfig
                    label="Interview Questions"
                    description="In-depth interview scenarios"
                    value={counts.interview_prompt_count}
                    min={0}
                    max={3}
                    onChange={(v) => setCounts({ ...counts, interview_prompt_count: v })}
                    icon={<Briefcase className="w-5 h-5 text-accent" />}
                    color="bg-accent/10"
                  />
                  <CountConfig
                    label="Scenarios"
                    description="Multi-step situational exercises"
                    value={counts.scenario_count}
                    min={0}
                    max={2}
                    onChange={(v) => setCounts({ ...counts, scenario_count: v })}
                    icon={<Target className="w-5 h-5 text-status-info" />}
                    color="bg-status-info/10"
                  />
                  <CountConfig
                    label="Artifacts"
                    description="Supporting materials per scenario"
                    value={counts.scenario_artifact_count}
                    min={0}
                    max={3}
                    onChange={(v) => setCounts({ ...counts, scenario_artifact_count: v })}
                    icon={<FileText className="w-5 h-5 text-status-warning" />}
                    color="bg-status-warning/10"
                  />
                </div>

                <Card variant="outlined" padding="md" className="flex flex-col gap-3">
                  <div className="flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-accent" />
                    <span className="text-body-sm font-medium text-content-primary">Total Items</span>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-display-md font-display text-accent">
                      {counts.quick_practice_prompt_count + counts.interview_prompt_count + counts.scenario_count}
                    </span>
                    <span className="text-body-sm text-content-secondary">
                      content items in a single LLM call
                    </span>
                  </div>
                </Card>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </PageShell>
  );
}
