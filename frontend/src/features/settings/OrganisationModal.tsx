import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Building2, Loader2 } from 'lucide-react';
import { Modal, ModalSection, ModalFooter } from '@/design-system/primitives/Modal';
import { Input } from '@/design-system/primitives/Input';
import { Button } from '@/design-system/primitives/Button';
import { useAuthSession } from '@/auth';
import { useData } from '@/data';
import type { OrganisationView } from '@/data/types';

interface OrganisationModalProps {
  readonly isOpen: boolean;
  readonly onClose: () => void;
  readonly onSuccess?: (org: OrganisationView) => void;
}

function generateSlug(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .trim();
}

export function OrganisationModal({ isOpen, onClose, onSuccess }: OrganisationModalProps) {
  const navigate = useNavigate();
  const { setActiveOrganisation, refreshSession } = useAuthSession();
  const data = useData();
  const [name, setName] = useState('');
  const [slug, setSlug] = useState('');
  const [slugManuallyEdited, setSlugManuallyEdited] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleNameChange = (value: string) => {
    setName(value);
    if (!slugManuallyEdited) {
      setSlug(generateSlug(value));
    }
  };

  const handleSlugChange = (value: string) => {
    setSlugManuallyEdited(true);
    const cleaned = value.toLowerCase().replace(/[^a-z0-9-]/g, '');
    setSlug(cleaned);
  };

  const handleClose = () => {
    setName('');
    setSlug('');
    setSlugManuallyEdited(false);
    setError(null);
    onClose();
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!name.trim()) {
      setError('Organisation name is required');
      return;
    }
    if (!slug.trim()) {
      setError('Organisation slug is required');
      return;
    }

    setIsLoading(true);
    try {
      const org = await data.createOrganisation({ name: name.trim(), slug: slug.trim() });
      await refreshSession();
      await setActiveOrganisation(org.id);
      handleClose();
      if (onSuccess) {
        onSuccess(org);
      }
      navigate('/admin');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create organisation');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={handleClose}
      title="Create Organisation"
      description="Set up a new organisation to collaborate with your team."
      size="md"
    >
      <form onSubmit={handleSubmit}>
        <ModalSection>
          <Input
            label="Organisation Name"
            placeholder="Acme Corporation"
            value={name}
            onChange={(e) => handleNameChange(e.target.value)}
            error={error && !name.trim() ? 'Name is required' : undefined}
            required
          />
          <Input
            label="URL Slug"
            placeholder="acme-corp"
            value={slug}
            onChange={(e) => handleSlugChange(e.target.value)}
            hint="Lowercase letters, numbers, and hyphens only"
            error={error && !slug.trim() ? 'Slug is required' : undefined}
            required
          />
          {error && (
            <p className="text-body-sm text-status-error bg-status-error/10 px-3 py-2 rounded-input">
              {error}
            </p>
          )}
        </ModalSection>
        <ModalFooter>
          <Button type="button" variant="ghost" onClick={handleClose} disabled={isLoading}>
            Cancel
          </Button>
          <Button type="submit" disabled={isLoading} icon={isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Building2 className="w-4 h-4" />}>
            {isLoading ? 'Creating...' : 'Create Organisation'}
          </Button>
        </ModalFooter>
      </form>
    </Modal>
  );
}
