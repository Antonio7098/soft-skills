import { useEffect, useRef } from 'react';
import type { ReactNode } from 'react';
import { X, Clock } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Button } from '@/design-system/primitives/Button';
import { StepIndicator } from '@/design-system/patterns/StepIndicator';
import { cn } from '@/lib/cn';

interface SessionShellProps {
  readonly title: string;
  readonly timer: string;
  readonly currentStep: number;
  readonly totalSteps: number;
  readonly stepLabel?: string;
  readonly children: ReactNode;
  readonly sidebar?: ReactNode;
  readonly secondarySidebar?: ReactNode;
  readonly secondarySidebarPosition?: 'before-main' | 'after-main';
  readonly contentKey?: string | number;
  readonly onEnd?: () => void;
  readonly className?: string;
  readonly wide?: boolean;
}

const shellVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.3, staggerChildren: 0.08 } },
};

const childVariants = {
  hidden: { opacity: 0, y: 12 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.3, ease: [0.25, 0.1, 0.25, 1] } },
};

export { childVariants as sessionChildVariants };

export function SessionShell({
  title,
  timer,
  currentStep,
  totalSteps,
  stepLabel,
  children,
  sidebar,
  secondarySidebar,
  secondarySidebarPosition = 'after-main',
  contentKey,
  onEnd,
  className,
  wide = false,
}: SessionShellProps) {
  const navigate = useNavigate();
  const mainRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    const node = mainRef.current;
    if (!node) {
      return;
    }
    node.scrollTo({ top: 0, behavior: 'auto' });
  }, [contentKey]);

  function handleEnd() {
    if (onEnd) {
      onEnd();
    } else {
      navigate('/practice');
    }
  }

  return (
    <motion.div
      variants={shellVariants}
      initial="hidden"
      animate="visible"
      className="flex flex-col min-h-screen bg-surface-primary"
    >
      <header className="h-16 border-b border-line bg-surface-primary/90 backdrop-blur-md flex items-center justify-between px-6 shrink-0 sticky top-0 z-10">
        <div className="flex items-center gap-4">
          <div className="w-8 h-8 rounded-lg bg-accent flex items-center justify-center">
            <span className="font-display text-body-sm text-surface-primary font-bold">S</span>
          </div>
          <h2 className="font-display text-display-sm text-content-primary truncate max-w-md">{title}</h2>
        </div>

        <div className="flex items-center gap-5">
          <StepIndicator current={currentStep} total={totalSteps} label={stepLabel} />
          <div className="flex items-center gap-1.5 text-body-sm font-medium text-content-secondary">
            <Clock className="w-4 h-4" />
            <span className="tabular-nums">{timer}</span>
          </div>
          <div className="w-px h-6 bg-line" />
          <Button variant="ghost" size="sm" icon={<X className="w-4 h-4" />} onClick={handleEnd}>
            End
          </Button>
        </div>
      </header>

      <div className={cn('flex flex-1 overflow-hidden', className)}>
        {sidebar && (
          <motion.aside variants={childVariants} className="w-[380px] border-r border-line overflow-y-auto p-6 shrink-0 hidden lg:block">
            {sidebar}
          </motion.aside>
        )}
        {secondarySidebar && secondarySidebarPosition === 'before-main' && (
          <motion.aside variants={childVariants} className="w-[380px] border-r border-line overflow-y-auto p-6 shrink-0 hidden xl:block">
            {secondarySidebar}
          </motion.aside>
        )}
        <motion.main ref={mainRef} variants={childVariants} className="flex-1 overflow-y-auto p-6 md:p-10">
          <div className={cn('flex flex-col gap-8', wide ? 'w-full' : 'max-w-2xl mx-auto')}>
            {children}
          </div>
        </motion.main>
        {secondarySidebar && secondarySidebarPosition === 'after-main' && (
          <motion.aside variants={childVariants} className="w-[380px] border-l border-line overflow-y-auto p-6 shrink-0 hidden xl:block">
            {secondarySidebar}
          </motion.aside>
        )}
      </div>
    </motion.div>
  );
}
