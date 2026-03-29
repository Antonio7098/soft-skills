import { useEffect, useState, useRef } from 'react';
import { 
  UserPlus, 
  MoreHorizontal,
  Mail,
  Shield,
  Ban,
  X,
  Check,
  Edit,
  UserX,
  UserCheck,
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

  // Modal states
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [showBulkRoleModal, setShowBulkRoleModal] = useState(false);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('learner');
  const [bulkRole, setBulkRole] = useState('learner');
  const [selectedUsers, setSelectedUsers] = useState<string[]>([]);
  const [actionLoading, setActionLoading] = useState(false);
  const [openDropdown, setOpenDropdown] = useState<string | null>(null);
  const [showUserModal, setShowUserModal] = useState(false);
  const [editingUser, setEditingUser] = useState<AdminUserView | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  const refreshUsers = () => {
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
  };

  useEffect(() => {
    refreshUsers();
  }, [dataProvider, page, search, roleFilter, statusFilter]);

  const handleInviteUser = async () => {
    if (!inviteEmail) return;
    setActionLoading(true);
    try {
      await dataProvider.createAdminUser({ email: inviteEmail, role: inviteRole });
      setShowInviteModal(false);
      setInviteEmail('');
      setInviteRole('learner');
      refreshUsers();
    } catch (error) {
      console.error('Failed to invite user:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const handleBulkRoleChange = async () => {
    if (selectedUsers.length === 0) return;
    setActionLoading(true);
    try {
      await dataProvider.bulkAdminUserOperation({
        user_ids: selectedUsers,
        operation: 'change_role',
        payload: { role: bulkRole },
      });
      setShowBulkRoleModal(false);
      setSelectedUsers([]);
      refreshUsers();
    } catch (error) {
      console.error('Failed to change roles:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const handleBulkSuspend = async () => {
    if (selectedUsers.length === 0) return;
    setActionLoading(true);
    try {
      await dataProvider.bulkAdminUserOperation({
        user_ids: selectedUsers,
        operation: 'suspend',
      });
      setSelectedUsers([]);
      refreshUsers();
    } catch (error) {
      console.error('Failed to suspend users:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const toggleUserSelection = (userId: string) => {
    setSelectedUsers((prev) =>
      prev.includes(userId) ? prev.filter((id) => id !== userId) : [...prev, userId]
    );
  };

  const toggleAllUsers = () => {
    if (selectedUsers.length === (users?.users.length || 0)) {
      setSelectedUsers([]);
    } else {
      setSelectedUsers(users?.users.map((u) => u.user_id) || []);
    }
  };

  const handleEditUser = (user: AdminUserView) => {
    setEditingUser(user);
    setShowUserModal(true);
    setOpenDropdown(null);
  };

  const handleToggleUserStatus = async (user: AdminUserView) => {
    setOpenDropdown(null);
    try {
      await dataProvider.updateAdminUserStatus(user.user_id, !user.is_active);
      refreshUsers();
    } catch (error) {
      console.error('Failed to update user status:', error);
    }
  };

  const handleSaveUser = async () => {
    if (!editingUser) return;
    setActionLoading(true);
    try {
      await dataProvider.updateAdminUserRole(editingUser.user_id, editingUser.organisation_role || 'learner');
      setShowUserModal(false);
      setEditingUser(null);
      refreshUsers();
    } catch (error) {
      console.error('Failed to update user:', error);
    } finally {
      setActionLoading(false);
    }
  };

  const columns = [
    {
      key: 'select',
      header: (
        <input
          type="checkbox"
          checked={selectedUsers.length === (users?.users.length || 0) && selectedUsers.length > 0}
          onChange={toggleAllUsers}
          className="w-4 h-4 rounded border-line"
        />
      ),
      width: '40px',
      render: (user: AdminUserView) => (
        <input
          type="checkbox"
          checked={selectedUsers.includes(user.user_id)}
          onChange={() => toggleUserSelection(user.user_id)}
          className="w-4 h-4 rounded border-line"
        />
      ),
    },
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
      render: (user: AdminUserView) => (
        <div className="relative" ref={dropdownRef}>
          <button 
            onClick={(e) => { e.stopPropagation(); setOpenDropdown(openDropdown === user.user_id ? null : user.user_id); }}
            className="p-1.5 rounded-md hover:bg-surface-secondary transition-colors"
          >
            <MoreHorizontal className="w-4 h-4 text-content-tertiary" />
          </button>
          {openDropdown === user.user_id && (
            <div className="absolute right-0 top-full mt-1 w-40 bg-surface-primary border border-line rounded-lg shadow-lg z-50">
              <button
                onClick={() => handleEditUser(user)}
                className="w-full flex items-center gap-2 px-3 py-2 text-body-sm text-content-primary hover:bg-surface-secondary transition-colors"
              >
                <Edit className="w-4 h-4" /> Edit User
              </button>
              <button
                onClick={() => handleToggleUserStatus(user)}
                className="w-full flex items-center gap-2 px-3 py-2 text-body-sm text-content-primary hover:bg-surface-secondary transition-colors"
              >
                {user.is_active ? <UserX className="w-4 h-4" /> : <UserCheck className="w-4 h-4" />}
                {user.is_active ? 'Suspend' : 'Activate'}
              </button>
            </div>
          )}
        </div>
      ),
    },
  ];

  const totalPages = users ? Math.ceil(users.total / pageSize) : 1;

  return (
    <AdminPageShell
      title="Users"
      subtitle="Manage user accounts, roles, and permissions"
      actions={
        <Button icon={<UserPlus className="w-4 h-4" />} onClick={() => setShowInviteModal(true)}>
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
        <Card 
          interactive 
          onClick={() => setShowInviteModal(true)}
          className="flex items-center gap-4 cursor-pointer"
        >
          <div className="w-10 h-10 rounded-lg bg-accent/10 flex items-center justify-center">
            <Mail className="w-5 h-5 text-accent" />
          </div>
          <div>
            <p className="text-body-sm font-medium text-content-primary">Bulk Invite</p>
            <p className="text-body-xs text-content-tertiary">Import users from CSV</p>
          </div>
        </Card>
        <Card 
          interactive 
          onClick={() => setShowBulkRoleModal(true)}
          className="flex items-center gap-4 cursor-pointer"
        >
          <div className="w-10 h-10 rounded-lg bg-status-warning/10 flex items-center justify-center">
            <Shield className="w-5 h-5 text-status-warning" />
          </div>
          <div>
            <p className="text-body-sm font-medium text-content-primary">Bulk Role Change</p>
            <p className="text-body-xs text-content-tertiary">Update multiple users</p>
          </div>
        </Card>
        <Card 
          interactive 
          onClick={handleBulkSuspend}
          className="flex items-center gap-4 cursor-pointer"
        >
          <div className="w-10 h-10 rounded-lg bg-status-error/10 flex items-center justify-center">
            <Ban className="w-5 h-5 text-status-error" />
          </div>
          <div>
            <p className="text-body-sm font-medium text-content-primary">Bulk Suspend</p>
            <p className="text-body-xs text-content-tertiary">Suspend selected users ({selectedUsers.length})</p>
          </div>
        </Card>
      </div>

      {/* Invite User Modal */}
      {showInviteModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-md flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h3 className="font-display text-display-xs text-content-primary">Invite User</h3>
              <button onClick={() => setShowInviteModal(false)} className="p-1 rounded hover:bg-surface-secondary">
                <X className="w-5 h-5 text-content-tertiary" />
              </button>
            </div>
            <div className="flex flex-col gap-3">
              <div>
                <label className="text-body-sm text-content-secondary mb-1 block">Email</label>
                <input
                  type="email"
                  value={inviteEmail}
                  onChange={(e) => setInviteEmail(e.target.value)}
                  placeholder="user@example.com"
                  className="w-full px-3 py-2 rounded-lg border border-line bg-surface-primary text-content-primary placeholder:text-content-tertiary focus:outline-none focus:ring-2 focus:ring-accent/50"
                />
              </div>
              <div>
                <label className="text-body-sm text-content-secondary mb-1 block">Role</label>
                <select
                  value={inviteRole}
                  onChange={(e) => setInviteRole(e.target.value)}
                  className="w-full px-3 py-2 rounded-lg border border-line bg-surface-primary text-content-primary focus:outline-none focus:ring-2 focus:ring-accent/50"
                >
                  {ROLE_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="secondary" onClick={() => setShowInviteModal(false)}>Cancel</Button>
              <Button onClick={handleInviteUser} loading={actionLoading} icon={<Check className="w-4 h-4" />}>
                Invite
              </Button>
            </div>
          </Card>
        </div>
      )}

      {/* Bulk Role Change Modal */}
      {showBulkRoleModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-md flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h3 className="font-display text-display-xs text-content-primary">Bulk Role Change</h3>
              <button onClick={() => setShowBulkRoleModal(false)} className="p-1 rounded hover:bg-surface-secondary">
                <X className="w-5 h-5 text-content-tertiary" />
              </button>
            </div>
            <p className="text-body-sm text-content-secondary">
              Change role for {selectedUsers.length} selected user(s)
            </p>
            <div>
              <label className="text-body-sm text-content-secondary mb-1 block">New Role</label>
              <select
                value={bulkRole}
                onChange={(e) => setBulkRole(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-line bg-surface-primary text-content-primary focus:outline-none focus:ring-2 focus:ring-accent/50"
              >
                {ROLE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="secondary" onClick={() => setShowBulkRoleModal(false)}>Cancel</Button>
              <Button onClick={handleBulkRoleChange} loading={actionLoading} icon={<Check className="w-4 h-4" />}>
                Apply
              </Button>
            </div>
          </Card>
        </div>
      )}

      {/* Edit User Modal */}
      {showUserModal && editingUser && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-md flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h3 className="font-display text-display-xs text-content-primary">Edit User</h3>
              <button onClick={() => { setShowUserModal(false); setEditingUser(null); }} className="p-1 rounded hover:bg-surface-secondary">
                <X className="w-5 h-5 text-content-tertiary" />
              </button>
            </div>
            <div className="flex flex-col gap-3">
              <div>
                <label className="text-body-sm text-content-secondary mb-1 block">Email</label>
                <input
                  type="email"
                  value={editingUser.email}
                  disabled
                  className="w-full px-3 py-2 rounded-lg border border-line bg-surface-secondary text-content-tertiary"
                />
              </div>
              <div>
                <label className="text-body-sm text-content-secondary mb-1 block">Display Name</label>
                <input
                  type="text"
                  value={editingUser.display_name || ''}
                  disabled
                  className="w-full px-3 py-2 rounded-lg border border-line bg-surface-secondary text-content-tertiary"
                />
              </div>
              <div>
                <label className="text-body-sm text-content-secondary mb-1 block">Role</label>
                <select
                  value={editingUser.organisation_role || 'learner'}
                  onChange={(e) => setEditingUser({ ...editingUser, organisation_role: e.target.value })}
                  className="w-full px-3 py-2 rounded-lg border border-line bg-surface-primary text-content-primary focus:outline-none focus:ring-2 focus:ring-accent/50"
                >
                  {ROLE_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="secondary" onClick={() => { setShowUserModal(false); setEditingUser(null); }}>Cancel</Button>
              <Button onClick={handleSaveUser} loading={actionLoading} icon={<Check className="w-4 h-4" />}>
                Save
              </Button>
            </div>
          </Card>
        </div>
      )}
    </AdminPageShell>
  );
}
