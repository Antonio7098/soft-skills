import { motion } from 'framer-motion';
import { Brain } from 'lucide-react';

interface AssessingOverlayProps {
  readonly message?: string;
}

export function AssessingOverlay({ message = 'Evaluating your response...' }: AssessingOverlayProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="flex flex-col items-center justify-center gap-6 py-16"
    >
      <div className="relative">
        <div className="w-20 h-20 rounded-full bg-accent-muted flex items-center justify-center">
          <Brain className="w-10 h-10 text-accent" />
        </div>
        <div className="absolute inset-0 w-20 h-20 rounded-full border-2 border-accent/30 border-t-accent animate-spin" />
      </div>
      <div className="flex flex-col items-center gap-2 text-center">
        <h3 className="font-display text-display-sm text-content-primary">{message}</h3>
        <p className="text-body-sm text-content-secondary max-w-xs">
          Our AI is analyzing your response against the rubric criteria. This usually takes a few seconds.
        </p>
      </div>
      <div className="flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-accent animate-skeleton-pulse" />
        <div className="w-2 h-2 rounded-full bg-accent animate-skeleton-pulse [animation-delay:200ms]" />
        <div className="w-2 h-2 rounded-full bg-accent animate-skeleton-pulse [animation-delay:400ms]" />
      </div>
    </motion.div>
  );
}
