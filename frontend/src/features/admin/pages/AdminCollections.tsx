import { useEffect, useState } from 'react';
import { 
  FolderCheck,
  CheckCircle,
  XCircle,
  Clock,
  Star,
  Eye,
  X,
  FileText,
  MessageSquare,
} from 'lucide-react';
import { Card } from '@/design-system/primitives/Card';
import { Button } from '@/design-system/primitives/Button';
import { Badge } from '@/design-system/primitives/Badge';
import { LoadingState } from '@/design-system/patterns/LoadingState';
import { useData } from '@/data';
import { AdminPageShell, MetricCard, DataTable, SearchInput, FilterSelect, StatusBadge } from '../components';
import type { CollectionVerificationQueueItemView, CollectionView } from '@/data/types';

const STATE_OPTIONS = [
  { value: 'pending', label: 'Pending' },
  { value: 'verified', label: 'Verified' },
  { value: 'rejected', label: 'Rejected' },
];

export function AdminCollections() {
  const dataProvider = useData();
  const [queue, setQueue] = useState<CollectionVerificationQueueItemView[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [stateFilter, setStateFilter] = useState('');
  const [selectedCollection, setSelectedCollection] = useState<CollectionVerificationQueueItemView | null>(null);
  const [fullCollection, setFullCollection] = useState<CollectionView | null>(null);
  const [showReviewModal, setShowReviewModal] = useState(false);
  const [selectedCollections, setSelectedCollections] = useState<string[]>([]);
  const [actionLoading, setActionLoading] = useState(false);
  const [reviewLoading, setReviewLoading] = useState(false);

  const refreshQueue = () => {
    setLoading(true);
    dataProvider.getVerificationQueue()
      .then(setQueue)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    refreshQueue();
  }, [dataProvider]);

  const handleReview = async (item: CollectionVerificationQueueItemView) => {
    setSelectedCollection(item);
    setShowReviewModal(true);
    setReviewLoading(true);
    try {
      const collection = await dataProvider.getCollection(item.collection_id);
      setFullCollection(collection);
    } catch (error) {
      console.error('Failed to load collection:', error);
    } finally {
      setReviewLoading(false);
    }
  };

  const handleVerify = async (state: 'verified' | 'rejected', note?: string) => {
    if (!selectedCollection) return;
    setActionLoading(true);
    try {
      await dataProvider.updateCollectionVerification(selectedCollection.collection_id, {
        verification_state: state,
        note,
      });
      setShowReviewModal(false);
      setSelectedCollection(null);
      refreshQueue();
    } catch (error) {
      console.error('Failed to update verification:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const handleBulkApprove = async () => {
    if (selectedCollections.length === 0) return;
    setActionLoading(true);
    try {
      for (const collectionId of selectedCollections) {
        await dataProvider.updateCollectionVerification(collectionId, {
          verification_state: 'verified',
        });
      }
      setSelectedCollections([]);
      refreshQueue();
    } catch (error) {
      console.error('Failed to bulk approve:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const handleFeature = async (collectionId: string) => {
    setActionLoading(true);
    try {
      await dataProvider.updateCollectionFeature(collectionId, true);
      refreshQueue();
    } catch (error) {
      console.error('Failed to feature collection:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const toggleCollectionSelection = (collectionId: string) => {
    setSelectedCollections((prev) =>
      prev.includes(collectionId) ? prev.filter((id) => id !== collectionId) : [...prev, collectionId]
    );
  };

  const filteredQueue = queue.filter((item) => {
    if (search && !item.title.toLowerCase().includes(search.toLowerCase())) return false;
    if (stateFilter && item.verification_state !== stateFilter) return false;
    return true;
  });

  const pendingCount = queue.filter((q) => q.verification_state === 'pending').length;
  const verifiedCount = queue.filter((q) => q.verification_state === 'verified').length;
  const rejectedCount = queue.filter((q) => q.verification_state === 'rejected').length;

  const columns = [
    {
      key: 'title',
      header: 'Collection',
      render: (item: CollectionVerificationQueueItemView) => (
        <div className="flex flex-col gap-0.5">
          <span className="font-medium">{item.title}</span>
          <span className="text-body-xs text-content-tertiary">
            {item.prompt_item_count} prompts · {item.scenario_count} scenarios
          </span>
        </div>
      ),
    },
    {
      key: 'source_type',
      header: 'Source',
      width: '100px',
      render: (item: CollectionVerificationQueueItemView) => (
        <Badge variant="default" size="sm">{item.source_type}</Badge>
      ),
    },
    {
      key: 'verification_state',
      header: 'Status',
      width: '100px',
      render: (item: CollectionVerificationQueueItemView) => (
        <StatusBadge status={item.verification_state as 'verified' | 'pending' | 'rejected'} />
      ),
    },
    {
      key: 'discovery_tier',
      header: 'Tier',
      width: '100px',
      render: (item: CollectionVerificationQueueItemView) => (
        <span className="text-content-secondary">{item.discovery_tier}</span>
      ),
    },
    {
      key: 'updated_at',
      header: 'Updated',
      width: '120px',
      render: (item: CollectionVerificationQueueItemView) => (
        <span className="text-content-secondary">
          {new Date(item.updated_at).toLocaleDateString()}
        </span>
      ),
    },
    {
      key: 'select',
      header: '',
      width: '40px',
      render: (item: CollectionVerificationQueueItemView) => (
        <input
          type="checkbox"
          checked={selectedCollections.includes(item.collection_id)}
          onChange={() => toggleCollectionSelection(item.collection_id)}
          className="w-4 h-4 rounded border-line"
        />
      ),
    },
    {
      key: 'actions',
      header: '',
      width: '80px',
      render: (item: CollectionVerificationQueueItemView) => (
        <Button variant="ghost" size="sm" icon={<Eye className="w-4 h-4" />} onClick={() => handleReview(item)}>
          Review
        </Button>
      ),
    },
  ];

  if (loading) {
    return (
      <AdminPageShell title="Collections" subtitle="Content verification and quality control">
        <LoadingState message="Loading verification queue..." />
      </AdminPageShell>
    );
  }

  return (
    <AdminPageShell
      title="Collections"
      subtitle="Review and verify user-generated content for quality and compliance"
    >
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Total in Queue"
          value={queue.length}
          icon={<FolderCheck className="w-4 h-4" />}
        />
        <MetricCard
          label="Pending Review"
          value={pendingCount}
          icon={<Clock className="w-4 h-4" />}
          trend={pendingCount > 10 ? 'negative' : 'neutral'}
        />
        <MetricCard
          label="Verified"
          value={verifiedCount}
          icon={<CheckCircle className="w-4 h-4" />}
          trend="positive"
        />
        <MetricCard
          label="Rejected"
          value={rejectedCount}
          icon={<XCircle className="w-4 h-4" />}
        />
      </div>

      <Card className="flex flex-col gap-4">
        <div className="flex items-center gap-3">
          <SearchInput
            value={search}
            onChange={setSearch}
            placeholder="Search collections..."
            className="w-64"
          />
          <FilterSelect
            value={stateFilter}
            onChange={setStateFilter}
            options={STATE_OPTIONS}
            placeholder="All states"
            className="w-40"
          />
          <div className="flex-1" />
          <span className="text-body-xs text-content-tertiary">
            {filteredQueue.length} collections
          </span>
        </div>
      </Card>

      <DataTable
        columns={columns}
        data={filteredQueue}
        keyExtractor={(item) => item.collection_id}
        emptyMessage="No collections in verification queue"
      />

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-status-success/10 flex items-center justify-center">
            <CheckCircle className="w-5 h-5 text-status-success" />
          </div>
          <div className="flex-1">
            <p className="text-body-sm font-medium text-content-primary">Bulk Approve</p>
            <p className="text-body-xs text-content-tertiary">
              {selectedCollections.length > 0 
                ? `Approve ${selectedCollections.length} selected` 
                : 'Select collections first'}
            </p>
          </div>
          <Button 
            variant="secondary" 
            size="sm" 
            onClick={handleBulkApprove}
            disabled={selectedCollections.length === 0}
            loading={actionLoading}
          >
            Approve
          </Button>
        </Card>
        <Card className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center">
            <Star className="w-5 h-5 text-accent" />
          </div>
          <div className="flex-1">
            <p className="text-body-sm font-medium text-content-primary">Feature Collection</p>
            <p className="text-body-xs text-content-tertiary">
              {selectedCollections.length === 1 
                ? 'Feature selected collection' 
                : 'Select one collection'}
            </p>
          </div>
          <Button 
            variant="secondary" 
            size="sm" 
            onClick={() => selectedCollections[0] && handleFeature(selectedCollections[0])}
            disabled={selectedCollections.length !== 1}
            loading={actionLoading}
          >
            Feature
          </Button>
        </Card>
      </div>

      {/* Review Modal */}
      {showReviewModal && selectedCollection && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <Card className="w-full max-w-3xl max-h-[90vh] flex flex-col gap-4 overflow-hidden">
            <div className="flex items-center justify-between">
              <h3 className="font-display text-display-xs text-content-primary">Review Collection</h3>
              <button onClick={() => { setShowReviewModal(false); setFullCollection(null); }} className="p-1 rounded hover:bg-surface-secondary">
                <X className="w-5 h-5 text-content-tertiary" />
              </button>
            </div>
            
            {reviewLoading ? (
              <div className="py-8">
                <LoadingState message="Loading collection details..." />
              </div>
            ) : fullCollection ? (
              <div className="flex flex-col gap-4 overflow-y-auto max-h-[60vh]">
                <div className="flex flex-col gap-2">
                  <p className="text-body-lg font-semibold text-content-primary">{fullCollection.title}</p>
                  <p className="text-body-sm text-content-secondary">{fullCollection.summary}</p>
                  <div className="flex gap-2 flex-wrap">
                    <Badge variant="default" size="sm">{selectedCollection.source_type}</Badge>
                    <Badge variant="default" size="sm">{selectedCollection.discovery_tier}</Badge>
                    {fullCollection.target_skill_slugs?.map((slug) => (
                      <Badge key={slug} variant="accent" size="sm">{slug}</Badge>
                    ))}
                  </div>
                </div>

                {fullCollection.prompt_items && fullCollection.prompt_items.length > 0 && (
                  <div className="flex flex-col gap-2">
                    <h4 className="text-body-sm font-medium text-content-secondary flex items-center gap-2">
                      <FileText className="w-4 h-4" /> Prompts ({fullCollection.prompt_items.length})
                    </h4>
                    <div className="flex flex-col gap-2">
                      {fullCollection.prompt_items.slice(0, 5).map((item, idx) => (
                        <div key={item.id} className="p-3 rounded-lg bg-surface-secondary/50 border border-line">
                          <div className="flex items-start gap-2">
                            <span className="w-5 h-5 rounded-full bg-accent/10 flex items-center justify-center text-body-xs font-medium text-accent shrink-0">
                              {idx + 1}
                            </span>
                            <p className="text-body-sm text-content-primary">{item.prompt_text}</p>
                          </div>
                        </div>
                      ))}
                      {fullCollection.prompt_items.length > 5 && (
                        <p className="text-body-xs text-content-tertiary text-center">+ {fullCollection.prompt_items.length - 5} more prompts</p>
                      )}
                    </div>
                  </div>
                )}

                {fullCollection.scenarios && fullCollection.scenarios.length > 0 && (
                  <div className="flex flex-col gap-2">
                    <h4 className="text-body-sm font-medium text-content-secondary flex items-center gap-2">
                      <MessageSquare className="w-4 h-4" /> Scenarios ({fullCollection.scenarios.length})
                    </h4>
                    <div className="flex flex-col gap-2">
                      {fullCollection.scenarios.slice(0, 3).map((scenario, idx) => (
                        <div key={scenario.id} className="p-3 rounded-lg bg-surface-secondary/50 border border-line">
                          <div className="flex items-start gap-2">
                            <span className="w-5 h-5 rounded-full bg-status-warning/10 flex items-center justify-center text-body-xs font-medium text-status-warning shrink-0">
                              {idx + 1}
                            </span>
                            <div>
                              <p className="text-body-sm font-medium text-content-primary">{scenario.title}</p>
                              <p className="text-body-xs text-content-secondary mt-1">{scenario.business_context}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                      {fullCollection.scenarios.length > 3 && (
                        <p className="text-body-xs text-content-tertiary text-center">+ {fullCollection.scenarios.length - 3} more scenarios</p>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="flex flex-col gap-2">
                <p className="text-body-md font-medium text-content-primary">{selectedCollection.title}</p>
                <div className="flex gap-2">
                  <Badge variant="default" size="sm">{selectedCollection.source_type}</Badge>
                  <Badge variant="default" size="sm">{selectedCollection.discovery_tier}</Badge>
                </div>
                <p className="text-body-sm text-content-secondary">
                  {selectedCollection.prompt_item_count} prompts · {selectedCollection.scenario_count} scenarios
                </p>
              </div>
            )}

            <div className="flex justify-end gap-2 pt-2 border-t border-line">
              <Button variant="secondary" onClick={() => { setShowReviewModal(false); setFullCollection(null); }}>Cancel</Button>
              <Button 
                variant="secondary" 
                onClick={() => handleVerify('rejected')} 
                loading={actionLoading}
                icon={<XCircle className="w-4 h-4" />}
              >
                Reject
              </Button>
              <Button 
                onClick={() => handleVerify('verified')} 
                loading={actionLoading}
                icon={<CheckCircle className="w-4 h-4" />}
              >
                Verify & Approve
              </Button>
            </div>
          </Card>
        </div>
      )}
    </AdminPageShell>
  );
}
