import { forwardRef } from 'react';
import { motion } from 'framer-motion';
import { Bot } from 'lucide-react';
import { Avatar } from '@/design-system/primitives/Avatar';
import { cn } from '@/lib/cn';

interface MessageBubbleProps {
  readonly role: 'user' | 'assistant';
  readonly content: string;
  readonly timestamp?: string;
  readonly isOptimistic?: boolean;
}

const bubbleVariants = {
  hidden: { opacity: 0, y: 6 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.18, ease: 'easeOut' },
  },
};

const userBubbleVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { duration: 0.14, ease: 'easeOut' },
  },
};

export const MessageBubble = forwardRef<HTMLDivElement, MessageBubbleProps>(
  function MessageBubble({ role, content, timestamp, isOptimistic }, ref) {
    const isUser = role === 'user';
    const variants = isUser ? userBubbleVariants : bubbleVariants;

  return (
    <motion.div
      ref={ref}
      variants={variants}
      initial="hidden"
      animate="visible"
      className={cn('flex gap-3 max-w-[85%]', isUser ? 'ml-auto flex-row-reverse' : 'mr-auto')}
    >
      {/* Avatar */}
      <div className="shrink-0 mt-1">
        {isUser ? (
          <Avatar fallback="You" size="sm" />
        ) : (
          <div className="w-8 h-8 rounded-full bg-accent/10 flex items-center justify-center ring-2 ring-accent/20">
            <Bot className="w-4 h-4 text-accent" />
          </div>
        )}
      </div>

      {/* Bubble */}
      <div
        className={cn(
          'rounded-2xl px-4 py-3 text-body-md leading-relaxed',
          'transition-colors duration-200',
          isUser
            ? 'bg-accent text-surface-primary rounded-br-md'
            : 'bg-surface-elevated border border-line shadow-card rounded-bl-md text-content-primary',
          isOptimistic && 'opacity-70',
        )}
      >
        {/* Content with simple markdown-like rendering */}
        <div className="whitespace-pre-wrap break-words">{content}</div>

        {/* Timestamp */}
        {timestamp && (
          <p
            className={cn(
              'mt-1.5 text-body-xs',
              isUser ? 'text-surface-primary/60' : 'text-content-tertiary',
            )}
          >
            {new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </p>
        )}
      </div>
    </motion.div>
  );
}
);
