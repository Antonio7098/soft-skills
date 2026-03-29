import { useEffect, useState } from 'react';
import { 
  FolderCheck,
  CheckCircle,
  XCircle,
  Clock,
  Star,
  Eye,
} from 'lucide-react';
import { Card } from '@/design-system/primitives/Card';
import { Button } from '@/design-system/primitives/Button';
import { Badge } from '@/design-system/primitives/Badge';
import { LoadingState } from '@/design-system/patterns/LoadingState';
import { useData } from '@/data';
import { AdminPageShell, MetricCard, DataTable, SearchInput, FilterSelect, StatusBadge } from '../components';
import type { CollectionVerificationQueueItemView } from '@/data/types';

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

  useEffect(() => {
    setLoading(true);
    dataProvider.getVerificationQueue()
      .then(setQueue)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [dataProvider]);

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
      key: 'actions',
      header: '',
      width: '80px',
      render: () => (
        <Button variant="ghost" size="sm" icon={<Eye className="w-4 h-4" />}>
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
            <p className="text-body-xs text-content-tertiary">Approve multiple collections at once</p>
          </div>
          <Button variant="secondary" size="sm">Select</Button>
        </Card>
        <Card className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center">
            <Star className="w-5 h-5 text-accent" />
          </div>
          <div className="flex-1">
            <p className="text-body-sm font-medium text-content-primary">Feature Collection</p>
            <p className="text-body-xs text-content-tertiary">Highlight top content</p>
          </div>
          <Button variant="secondary" size="sm">Select</Button>
        </Card>
      </div>
    </AdminPageShell>
  );
}
