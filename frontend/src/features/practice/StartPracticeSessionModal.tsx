import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search,
  CheckCircle2,
  Circle,
  ChevronRight,
  ChevronLeft,
  Layers,
  Brain,
  Target,
  X,
  Play,
  Clock,
  AlertCircle,
} from 'lucide-react';
import { Modal, ModalFooter, ModalSection } from '@/design-system/primitives/Modal';
import { Card } from '@/design-system/primitives/Card';
import { Badge } from '@/design-system/primitives/Badge';
import { Button } from '@/design-system/primitives/Button';
import { useData } from '@/data';
import type { CollectionView, PracticeRunItemType } from '@/data';
import { getDomainDifficultyVariant } from '@/lib/variant-helpers';
import { cn } from '@/lib/cn';

interface StartPracticeSessionModalProps {
  readonly isOpen: boolean;
  readonly onClose: () => void;
}

type Step = 'browse' | 'review' | 'starting';

interface SelectedItem {
  readonly item_id: string;
  readonly item_type: PracticeRunItemType;
  readonly title: string;
  readonly difficulty: string;
  readonly skill_slugs: string[];
  readonly collection_title: string;
  readonly prompt_type?: string;
}

export function StartPracticeSessionModal({ isOpen, onClose }: StartPracticeSessionModalProps) {
  const navigate = useNavigate();
  const data = useData();
  const [step, setStep] = useState<Step>('browse');
  const [collections, setCollections] = useState<CollectionView[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedItems, setSelectedItems] = useState<SelectedItem[]>([]);
  const [runTitle, setRunTitle] = useState('');
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen) {
      setLoading(true);
      data.listCollections({ include_private: true })
        .then((cols) => {
          setCollections(cols);
          setLoading(false);
        })
        .catch(() => setLoading(false));
    }
  }, [isOpen, data]);

  useEffect(() => {
    if (!isOpen) {
      setStep('browse');
      setSelectedItems([]);
      setSearchQuery('');
      setRunTitle('');
      setError('');
      setStarting(false);
    }
  }, [isOpen]);

  const filteredCollections = collections.filter((col) =>
    col.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    col.prompt_items.some((p) => p.title.toLowerCase().includes(searchQuery.toLowerCase())) ||
    col.scenarios.some((s) => s.title.toLowerCase().includes(searchQuery.toLowerCase())),
  );

  const isSelected = (itemId: string) => selectedItems.some((s) => s.item_id === itemId);

  function toggleItem(
    itemId: string,
    itemType: PracticeRunItemType,
    title: string,
    difficulty: string,
    skillSlugs: string[],
    collectionTitle: string,
    promptType?: string,
  ) {
    if (isSelected(itemId)) {
      setSelectedItems((prev) => prev.filter((s) => s.item_id !== itemId));
    } else {
      setSelectedItems((prev) => [
        ...prev,
        { item_id: itemId, item_type: itemType, title, difficulty, skill_slugs: skillSlugs, collection_title: collectionTitle, prompt_type: promptType },
      ]);
    }
  }

  async function handleStartPractice() {
    if (selectedItems.length === 0) return;
    setStarting(true);
    setError('');

    try {
      const title = runTitle.trim() || `Practice Session — ${selectedItems.length} items`;
      const run = await data.createPracticeRun({
        title,
        selected_items: selectedItems.map((s) => ({ item_id: s.item_id, item_type: s.item_type })),
      });

      const sessions = await data.getPracticeSessions(run.run_id);
      if (sessions.length > 0) {
        navigate(`/session/practice-run/${run.run_id}`, { replace: true });
        onClose();
      } else {
        setError('Failed to create practice sessions');
        setStarting(false);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to start practice');
      setStarting(false);
    }
  }

  function handleClose() {
    if (!starting) {
      onClose();
    }
  }

  const getItemIcon = (itemType: PracticeRunItemType) => {
    switch (itemType) {
      case 'prompt_item':
        return <Brain className="w-4 h-4" />;
      case 'scenario':
        return <Target className="w-4 h-4" />;
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Start Practice Session"
      description="Build a custom practice session from your collections"
      size="xl"
      className="w-full"
    >
      <ModalSection>
        {step === 'browse' && (
          <div className="flex flex-col gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-content-tertiary" />
              <input
                type="text"
                placeholder="Search collections, questions, scenarios..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full h-10 pl-10 pr-4 bg-surface-secondary border border-line rounded-button text-body-md text-content-primary placeholder:text-content-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent"
              />
            </div>

            {loading ? (
              <div className="flex items-center justify-center py-12">
                <div className="w-8 h-8 border-2 border-accent border-t-transparent rounded-full animate-spin" />
              </div>
            ) : (
              <div className="flex flex-col gap-4 max-h-[50vh] overflow-y-auto pr-2">
                {filteredCollections.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-12 text-center">
                    <AlertCircle className="w-8 h-8 text-content-tertiary mb-2" />
                    <p className="text-body-md text-content-secondary">No collections found</p>
                  </div>
                ) : (
                  filteredCollections.map((col) => (
                    <CollectionCard
                      key={col.id}
                      collection={col}
                      selectedItems={selectedItems}
                      isSelected={isSelected}
                      onToggleItem={toggleItem}
                      searchQuery={searchQuery}
                    />
                  ))
                )}
              </div>
            )}

            {selectedItems.length > 0 && (
              <div className="flex items-center justify-between p-4 bg-surface-secondary border border-line rounded-card">
                <div className="flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-accent" />
                  <span className="text-body-md text-content-primary">
                    {selectedItems.length} item{selectedItems.length !== 1 ? 's' : ''} selected
                  </span>
                </div>
                <Button size="sm" variant="secondary" onClick={() => setStep('review')}>
                  Review Selection
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
            )}
          </div>
        )}

        {step === 'review' && (
          <div className="flex flex-col gap-4">
            <div className="flex items-center gap-2 text-body-sm text-content-secondary mb-2">
              <Button variant="ghost" size="sm" onClick={() => setStep('browse')}>
                <ChevronLeft className="w-4 h-4" />
                Back to Browse
              </Button>
            </div>

            <div className="flex flex-col gap-2">
              <label className="text-body-sm font-medium text-content-primary">Session Title (optional)</label>
              <input
                type="text"
                placeholder={`Practice Session — ${selectedItems.length} items`}
                value={runTitle}
                onChange={(e) => setRunTitle(e.target.value)}
                className="w-full h-10 px-4 bg-surface-secondary border border-line rounded-button text-body-md text-content-primary placeholder:text-content-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50 focus:border-accent"
              />
            </div>

            <div className="flex flex-col gap-3 max-h-[40vh] overflow-y-auto pr-2">
              {selectedItems.map((item) => (
                <Card key={`${item.item_type}-${item.item_id}`} variant="outlined" padding="sm" className="flex items-center gap-3">
                  <div className={cn(
                    'w-8 h-8 rounded-full flex items-center justify-center shrink-0',
                    item.item_type === 'prompt_item' ? 'bg-accent/10 text-accent' : 'bg-status-info/10 text-status-info',
                  )}>
                    {getItemIcon(item.item_type)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-body-sm font-medium text-content-primary truncate">{item.title}</p>
                    <div className="flex items-center gap-2 mt-0.5">
                      <Badge variant="default" size="sm">{item.collection_title}</Badge>
                      <Badge variant={getDomainDifficultyVariant(item.difficulty)} size="sm">{item.difficulty}</Badge>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => toggleItem(item.item_id, item.item_type, item.title, item.difficulty, item.skill_slugs, item.collection_title)}
                    className="p-1.5 rounded-button text-content-tertiary hover:text-status-error hover:bg-status-error/10 transition-colors"
                    aria-label="Remove item"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </Card>
              ))}
            </div>

            <div className="flex items-center justify-between p-4 bg-accent-muted/30 border border-accent/20 rounded-card">
              <div className="flex items-center gap-2">
                <Layers className="w-5 h-5 text-accent" />
                <span className="text-body-md text-content-primary font-medium">
                  {selectedItems.length} item{selectedItems.length !== 1 ? 's' : ''} ready
                </span>
              </div>
              <div className="flex items-center gap-2 text-body-sm text-content-secondary">
                <Clock className="w-4 h-4" />
                <span>~{selectedItems.length * 8} min</span>
              </div>
            </div>

            {error && (
              <div className="flex items-center gap-2 p-3 bg-status-error/10 border border-status-error/20 rounded-card text-status-error text-body-sm">
                <AlertCircle className="w-4 h-4 shrink-0" />
                {error}
              </div>
            )}
          </div>
        )}
      </ModalSection>

      <ModalFooter>
        <Button variant="ghost" onClick={handleClose} disabled={starting}>
          Cancel
        </Button>
        {step === 'review' && (
          <Button
            variant="primary"
            icon={<Play className="w-4 h-4" />}
            loading={starting}
            onClick={handleStartPractice}
            disabled={selectedItems.length === 0}
          >
            Start Session
          </Button>
        )}
      </ModalFooter>
    </Modal>
  );
}

interface CollectionCardProps {
  readonly collection: CollectionView;
  readonly selectedItems: SelectedItem[];
  readonly isSelected: (itemId: string) => boolean;
  readonly onToggleItem: (
    itemId: string,
    itemType: PracticeRunItemType,
    title: string,
    difficulty: string,
    skillSlugs: string[],
    collectionTitle: string,
    promptType?: string,
  ) => void;
  readonly searchQuery: string;
}

function CollectionCard({ collection, selectedItems, isSelected, onToggleItem, searchQuery }: CollectionCardProps) {
  const [expanded, setExpanded] = useState(false);

  const itemCount = collection.prompt_items.length + collection.scenarios.length;
  const selectedCount = selectedItems.filter((s) =>
    collection.prompt_items.some((p) => p.id === s.item_id) ||
    collection.scenarios.some((sc) => sc.id === s.item_id),
  ).length;

  const matchesSearch = (text: string) =>
    !searchQuery || text.toLowerCase().includes(searchQuery.toLowerCase());

  const promptMatches = collection.prompt_items.filter((p) => matchesSearch(p.title));
  const scenarioMatches = collection.scenarios.filter((s) => matchesSearch(s.title));

  if (searchQuery && promptMatches.length === 0 && scenarioMatches.length === 0) {
    return null;
  }

  return (
    <Card variant="outlined" padding="md" className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <button
          type="button"
          className="flex items-center gap-3 flex-1 text-left"
          onClick={() => setExpanded(!expanded)}
        >
          <div className={cn(
            'w-10 h-10 rounded-full flex items-center justify-center shrink-0',
            selectedCount > 0 ? 'bg-accent text-surface-primary' : 'bg-surface-secondary text-content-secondary',
          )}>
            <Layers className="w-5 h-5" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h4 className="text-body-md font-medium text-content-primary">{collection.title}</h4>
              {selectedCount > 0 && (
                <Badge variant="accent" size="sm">{selectedCount} selected</Badge>
              )}
            </div>
            <div className="flex items-center gap-2 mt-0.5">
              <Badge variant="default" size="sm">{collection.difficulty}</Badge>
              <span className="text-body-xs text-content-tertiary">
                {itemCount} item{itemCount !== 1 ? 's' : ''}
              </span>
            </div>
          </div>
        </button>
        {expanded ? (
          <ChevronLeft className="w-5 h-5 text-content-tertiary transition-transform" />
        ) : (
          <ChevronRight className="w-5 h-5 text-content-tertiary transition-transform" />
        )}
      </div>

      {expanded && (
        <div className="flex flex-col gap-3 pl-13">
          {promptMatches.length > 0 && (
            <div className="flex flex-col gap-2">
              <div className="flex items-center gap-2 text-body-xs text-content-tertiary uppercase tracking-wider">
                <Brain className="w-3.5 h-3.5" />
                Questions
              </div>
              {promptMatches.map((prompt) => (
                <ItemRow
                  key={prompt.id}
                  id={prompt.id}
                  itemType="prompt_item"
                  title={prompt.title}
                  difficulty={prompt.difficulty}
                  skillSlugs={prompt.target_skill_slugs}
                  collectionTitle={collection.title}
                  selected={isSelected(prompt.id)}
                  onToggle={onToggleItem}
                  promptType={prompt.prompt_type}
                />
              ))}
            </div>
          )}

          {scenarioMatches.length > 0 && (
            <div className="flex flex-col gap-2">
              <div className="flex items-center gap-2 text-body-xs text-content-tertiary uppercase tracking-wider">
                <Target className="w-3.5 h-3.5" />
                Scenarios
              </div>
              {scenarioMatches.map((scenario) => (
                <ItemRow
                  key={scenario.id}
                  id={scenario.id}
                  itemType="scenario"
                  title={scenario.title}
                  difficulty="intermediate"
                  skillSlugs={scenario.target_skill_slugs}
                  collectionTitle={collection.title}
                  selected={isSelected(scenario.id)}
                  onToggle={onToggleItem}
                />
              ))}
            </div>
          )}
        </div>
      )}
    </Card>
  );
}

interface ItemRowProps {
  readonly id: string;
  readonly itemType: PracticeRunItemType;
  readonly title: string;
  readonly difficulty: string;
  readonly skillSlugs: string[];
  readonly collectionTitle: string;
  readonly selected: boolean;
  readonly promptType?: string;
  readonly onToggle: (
    id: string,
    itemType: PracticeRunItemType,
    title: string,
    difficulty: string,
    skillSlugs: string[],
    collectionTitle: string,
    promptType?: string,
  ) => void;
}

function ItemRow({ id, itemType, title, difficulty, skillSlugs, collectionTitle, selected, onToggle, promptType }: ItemRowProps) {
  return (
    <button
      type="button"
      onClick={() => onToggle(id, itemType, title, difficulty, skillSlugs, collectionTitle, promptType)}
      className={cn(
        'flex items-center gap-3 p-2 rounded-button text-left transition-colors',
        selected
          ? 'bg-accent/5 border border-accent/20'
          : 'hover:bg-surface-secondary border border-transparent',
      )}
    >
      {selected ? (
        <CheckCircle2 className="w-4 h-4 text-accent shrink-0" />
      ) : (
        <Circle className="w-4 h-4 text-content-tertiary shrink-0" />
      )}
      <div className="flex-1 min-w-0">
        <p className="text-body-sm text-content-primary truncate">{title}</p>
        <div className="flex items-center gap-2 mt-0.5">
          <Badge variant={getDomainDifficultyVariant(difficulty)} size="sm">{difficulty}</Badge>
          <Badge variant="default" size="sm">
            {itemType === 'prompt_item' ? (
              <Brain className="w-3 h-3 mr-1" />
            ) : (
              <Target className="w-3 h-3 mr-1" />
            )}
            {itemType === 'prompt_item' ? 'Question' : 'Scenario'}
          </Badge>
        </div>
      </div>
    </button>
  );
}
