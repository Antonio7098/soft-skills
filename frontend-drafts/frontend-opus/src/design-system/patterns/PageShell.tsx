import type { ReactNode } from 'react';
import { motion } from 'framer-motion';
import { cn } from '@/lib/cn';

interface PageShellProps {
  readonly title: string;
  readonly subtitle?: string;
  readonly actions?: ReactNode;
  readonly children: ReactNode;
  readonly className?: string;
}

const pageVariants = {
  hidden: { opacity: 0, y: 12 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.35, ease: [0.25, 0.1, 0.25, 1], staggerChildren: 0.06 },
  },
};

const childVariants = {
  hidden: { opacity: 0, y: 8 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.3, ease: [0.25, 0.1, 0.25, 1] } },
};

export function PageShell({ title, subtitle, actions, children, className }: PageShellProps) {
  return (
    <motion.div
      variants={pageVariants}
      initial="hidden"
      animate="visible"
      className={cn('flex flex-col gap-8', className)}
    >
      <motion.header variants={childVariants} className="flex items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <h1 className="font-display text-display-lg text-content-primary">{title}</h1>
          {subtitle && (
            <p className="text-body-md text-content-secondary max-w-xl">{subtitle}</p>
          )}
        </div>
        {actions && <div className="flex items-center gap-3 shrink-0">{actions}</div>}
      </motion.header>
      <motion.div variants={childVariants} className="flex flex-col gap-6">
        {children}
      </motion.div>
    </motion.div>
  );
}
