import { useEffect, useState } from 'react';
import { 
  UserPlus, 
  MoreHorizontal,
  Mail,
  Shield,
  Ban,
} from 'lucide-react';
import { Card } from '@/design-system/primitives/Card';
import { Button } from '@/design-system/primitives/Button';
import { Badge } from '@/design-system/primitives/Badge';
import { LoadingState } from '@/design-system/patterns/LoadingState';
import { useData } from '@/data';
import { AdminPageShell, DataTable, SearchInput, FilterSelect, Pagination, StatusBadge } from '../components';
import type { AdminUserView, AdminUserListView } from '@/data/types';

const ROLE_OPTIONS = [
  { value: 'admin', label: 'Admin' },
  { value: 'instructor', label: 'Instructor' },
  { value: 'learner', label: 'Learner' },
];

const STATUS_OPTIONS = [
  { value: 'true', label: 'Active' },
  { value: 'false', label: 'Inactive' },
];

export function AdminUsers() {
  const dataProvider = useData();
  const [users, setUsers] = useState<AdminUserListView | null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const pageSize = 20;

  useEffect(() => {
    setLoading(true);
    dataProvider.listAdminUsers({
      offset: (page - 1) * pageSize,
      limit: pageSize,
      search: search || undefined,
      role: roleFilter || undefined,
      is_active: statusFilter ? statusFilter === 'true' : undefined,
    })
      .then(setUsers)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [dataProvider, page, search, roleFilter, statusFilter]);

  const columns = [
    {
      key: 'email',
      header: 'User',
      render: (user: AdminUserView) => (
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-accent/10 flex items-center justify-center">
            <span className="text-body-xs font-semibold text-accent">
              {user.display_name?.charAt(0).toUpperCase() || user.email.charAt(0).toUpperCase()}
            </span>
          </div>
          <div className="flex flex-col">
            <span className="font-medium">{user.display_name || 'No name'}</span>
            <span className="text-body-xs text-content-tertiary">{user.email}</span>
          </div>
        </div>
      ),
    },
    {
      key: 'organisation_role',
      header: 'Role',
      width: '120px',
      render: (user: AdminUserView) => (
        <Badge variant="default" size="sm">
          {user.organisation_role || 'learner'}
        </Badge>
      ),
    },
    {
      key: 'auth_provider',
      header: 'Auth',
      width: '100px',
      render: (user: AdminUserView) => (
        <span className="text-content-secondary">{user.auth_provider}</span>
      ),
    },
    {
      key: 'is_active',
      header: 'Status',
      width: '100px',
      render: (user: AdminUserView) => (
        <StatusBadge status={user.is_active ? 'active' : 'inactive'} />
      ),
    },
    {
      key: 'created_at',
      header: 'Joined',
      width: '120px',
      render: (user: AdminUserView) => (
        <span className="text-content-secondary">
          {user.created_at ? new Date(user.created_at).toLocaleDateString() : '—'}
        </span>
      ),
    },
    {
      key: 'actions',
      header: '',
      width: '48px',
      render: () => (
        <button className="p-1.5 rounded-md hover:bg-surface-secondary transition-colors">
          <MoreHorizontal className="w-4 h-4 text-content-tertiary" />
        </button>
      ),
    },
  ];

  const totalPages = users ? Math.ceil(users.total / pageSize) : 1;

  return (
    <AdminPageShell
      title="Users"
      subtitle="Manage user accounts, roles, and permissions"
      actions={
        <Button icon={<UserPlus className="w-4 h-4" />}>
          Invite User
        </Button>
      }
    >
      <Card className="flex flex-col gap-4">
        <div className="flex items-center gap-3">
          <SearchInput
            value={search}
            onChange={setSearch}
            placeholder="Search by email or name..."
            className="w-64"
          />
          <FilterSelect
            value={roleFilter}
            onChange={setRoleFilter}
            options={ROLE_OPTIONS}
            placeholder="All roles"
            className="w-36"
          />
          <FilterSelect
            value={statusFilter}
            onChange={setStatusFilter}
            options={STATUS_OPTIONS}
            placeholder="All status"
            className="w-32"
          />
          <div className="flex-1" />
          <span className="text-body-xs text-content-tertiary">
            {users?.total || 0} users
          </span>
        </div>
      </Card>

      {loading ? (
        <LoadingState message="Loading users..." />
      ) : (
        <>
          <DataTable
            columns={columns}
            data={users?.users || []}
            keyExtractor={(user) => user.user_id}
            emptyMessage="No users found"
          />
          <Pagination
            currentPage={page}
            totalPages={totalPages}
            onPageChange={setPage}
          />
        </>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center">
            <Mail className="w-5 h-5 text-accent" />
          </div>
          <div>
            <p className="text-body-sm font-medium text-content-primary">Bulk Invite</p>
            <p className="text-body-xs text-content-tertiary">Import users from CSV</p>
          </div>
        </Card>
        <Card className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-status-warning/10 flex items-center justify-center">
            <Shield className="w-5 h-5 text-status-warning" />
          </div>
          <div>
            <p className="text-body-sm font-medium text-content-primary">Bulk Role Change</p>
            <p className="text-body-xs text-content-tertiary">Update multiple users</p>
          </div>
        </Card>
        <Card className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-lg bg-status-error/10 flex items-center justify-center">
            <Ban className="w-5 h-5 text-status-error" />
          </div>
          <div>
            <p className="text-body-sm font-medium text-content-primary">Bulk Suspend</p>
            <p className="text-body-xs text-content-tertiary">Suspend selected users</p>
          </div>
        </Card>
      </div>
    </AdminPageShell>
  );
}
