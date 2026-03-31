import { useState } from 'react';
import { PageShell } from '@/design-system/patterns/PageShell';
import { Card } from '@/design-system/primitives/Card';
import { ThemeSwitcher } from '@/components/navigation/ThemeSwitcher';
import { ProfileCard, OrganisationModal, OrganisationList } from '@/features/settings';

export function Settings() {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <PageShell
      title="Settings"
      subtitle="Manage your account preferences and application settings."
    >
      <div className="max-w-2xl flex flex-col gap-6">
        <ProfileCard />

        <OrganisationList onCreateClick={() => setIsModalOpen(true)} />

        <Card className="flex flex-col gap-6">
          <div className="flex flex-col gap-1">
            <h3 className="font-display text-display-xs text-content-primary">Appearance</h3>
            <p className="text-body-sm text-content-secondary">Customize the look and feel of the application.</p>
          </div>

          <div className="p-4 rounded-xl bg-surface-secondary/50 border border-line">
            <ThemeSwitcher />
          </div>
        </Card>
      </div>

      <OrganisationModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </PageShell>
  );
}
