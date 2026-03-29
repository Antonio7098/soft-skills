import { Badge, type BadgeVariant } from '@/design-system/primitives/Badge';

type StatusType = 
  | 'active' | 'inactive' | 'pending' | 'suspended'
  | 'success' | 'error' | 'warning' | 'info'
  | 'passed' | 'failed' | 'running' | 'completed'
  | 'draft' | 'published' | 'archived'
  | 'verified' | 'unverified' | 'rejected';

const STATUS_CONFIG: Record<StatusType, { variant: BadgeVariant; label: string }> = {
  active: { variant: 'success', label: 'Active' },
  inactive: { variant: 'default', label: 'Inactive' },
  pending: { variant: 'warning', label: 'Pending' },
  suspended: { variant: 'error', label: 'Suspended' },
  success: { variant: 'success', label: 'Success' },
  error: { variant: 'error', label: 'Error' },
  warning: { variant: 'warning', label: 'Warning' },
  info: { variant: 'info', label: 'Info' },
  passed: { variant: 'success', label: 'Passed' },
  failed: { variant: 'error', label: 'Failed' },
  running: { variant: 'info', label: 'Running' },
  completed: { variant: 'success', label: 'Completed' },
  draft: { variant: 'default', label: 'Draft' },
  published: { variant: 'success', label: 'Published' },
  archived: { variant: 'default', label: 'Archived' },
  verified: { variant: 'success', label: 'Verified' },
  unverified: { variant: 'warning', label: 'Unverified' },
  rejected: { variant: 'error', label: 'Rejected' },
};

interface StatusBadgeProps {
  readonly status: StatusType | string;
  readonly className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const config = STATUS_CONFIG[status as StatusType] || { variant: 'default' as BadgeVariant, label: status };
  
  return (
    <Badge variant={config.variant} size="sm" className={className}>
      {config.label}
    </Badge>
  );
}
