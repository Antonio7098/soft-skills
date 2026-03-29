import type { ReactNode } from 'react';
import { motion } from 'framer-motion';
import { Building2 } from 'lucide-react';
import { useAdminScope } from '@/auth';
import { cn } from '@/lib/cn';

interface AdminPageShellProps {
  readonly title: string;
  readonly subtitle?: string;
  readonly actions?: ReactNode;
  readonly children: ReactNode;
  readonly className?: string;
  readonly showScope?: boolean;
}

const pageVariants = {
  hidden: { opacity: 0, y: 8 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.3, ease: [0.25, 0.1, 0.25, 1], staggerChildren: 0.05 },
  },
};

const childVariants = {
  hidden: { opacity: 0, y: 6 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.25, ease: [0.25, 0.1, 0.25, 1] } },
};

export function AdminPageShell({ title, subtitle, actions, children, className, showScope = true }: AdminPageShellProps) {
  const { activeOrganisation } = useAdminScope();

  return (
    <motion.div
      variants={pageVariants}
      initial="hidden"
      animate="visible"
      className={cn('flex flex-col gap-6', className)}
    >
      <motion.header variants={childVariants} className="flex items-start justify-between gap-4">
        <div className="flex flex-col gap-1">
          <h1 className="font-display text-display-md text-content-primary">{title}</h1>
          {subtitle && (
            <p className="text-body-sm text-content-secondary max-w-2xl">{subtitle}</p>
          )}
          {showScope && activeOrganisation && (
            <div className="flex items-center gap-2 text-body-xs text-content-tertiary">
              <Building2 className="w-3.5 h-3.5" />
              <span>
                Scoped to {activeOrganisation.organisation_name}
              </span>
            </div>
          )}
        </div>
        {actions && <div className="flex items-center gap-2 shrink-0">{actions}</div>}
      </motion.header>
      <motion.div variants={childVariants} className="flex flex-col gap-5">
        {children}
      </motion.div>
    </motion.div>
  );
}
