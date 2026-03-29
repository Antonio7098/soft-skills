import { forwardRef } from 'react';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { cn } from '@/lib/cn';

interface MessageBubbleProps {
  readonly role: 'user' | 'assistant';
  readonly content: string;
  readonly timestamp?: string;
  readonly isOptimistic?: boolean;
}

const messageVariants = {
  hidden: { opacity: 0, y: 6 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.18, ease: 'easeOut' },
  },
};

export const MessageBubble = forwardRef<HTMLDivElement, MessageBubbleProps>(
  function MessageBubble({ role, content, timestamp, isOptimistic }, ref) {
    const isUser = role === 'user';

  return (
    <motion.div
      ref={ref}
      variants={messageVariants}
      initial="hidden"
      animate="visible"
      className={cn(
        isUser ? 'ml-auto max-w-[80%]' : 'w-full',
        isOptimistic && 'opacity-70',
      )}
    >
      {/* Content */}
      <div className={cn(
        isUser
          ? 'rounded-2xl rounded-br-md px-4 py-3 bg-surface-elevated border border-line text-content-primary'
          : 'prose prose-sm prose-neutral dark:prose-invert max-w-none text-content-primary prose-headings:text-content-primary prose-p:text-content-primary prose-strong:text-content-primary prose-code:text-accent prose-code:bg-surface-secondary prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:before:content-none prose-code:after:content-none prose-pre:bg-surface-secondary prose-pre:border prose-pre:border-line prose-a:text-accent prose-a:no-underline hover:prose-a:underline'
      )}>
        {isUser ? (
          <div className="whitespace-pre-wrap break-words text-body-md">{content}</div>
        ) : (
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
        )}
      </div>

      {/* Timestamp */}
      {timestamp && (
        <p className={cn(
          'mt-1.5 text-body-xs text-content-tertiary',
          isUser && 'text-right'
        )}>
          {new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </p>
      )}
    </motion.div>
  );
}
);
