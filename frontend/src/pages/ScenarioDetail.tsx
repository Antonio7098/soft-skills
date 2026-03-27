import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Building2,
  Target,
  AlertTriangle,
  Zap,
  Play,
  Briefcase,
  Globe,
} from 'lucide-react';
import { useData } from '@/data';
import type { CollectionView, ScenarioView } from '@/data';
import { Card } from '@/design-system/primitives/Card';
import { Badge } from '@/design-system/primitives/Badge';
import { Button } from '@/design-system/primitives/Button';
import { Avatar } from '@/design-system/primitives/Avatar';
import { LoadingState } from '@/design-system/patterns/LoadingState';
import { ErrorState } from '@/design-system/patterns/ErrorState';
import { SectionHeader } from '@/design-system/patterns/SectionHeader';

const fadeUp = {
  hidden: { opacity: 0, y: 12 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { duration: 0.35, delay: i * 0.07, ease: [0.25, 0.1, 0.25, 1] },
  }),
};

export function ScenarioDetail() {
  const { collectionId, scenarioId } = useParams<{ collectionId: string; scenarioId: string }>();
  const navigate = useNavigate();
  const data = useData();

  const [collection, setCollection] = useState<CollectionView | null>(null);
  const [scenario, setScenario] = useState<ScenarioView | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!collectionId || !scenarioId) {
      setError('Missing IDs');
      setLoading(false);
      return;
    }
    data.getCollection(collectionId)
      .then((col) => {
        setCollection(col);
        const sc = col.scenarios.find((s) => s.id === scenarioId);
        if (!sc) throw new Error('Scenario not found in this collection');
        setScenario(sc);
        setLoading(false);
      })
      .catch((e) => {
        setError(e.message);
        setLoading(false);
      });
  }, [collectionId, scenarioId, data]);

  if (loading) return <LoadingState message="Loading scenario details..." />;
  if (error || !scenario || !collection) {
    return <ErrorState message={error || 'Scenario not found'} onRetry={() => navigate('/collections')} />;
  }

  return (
    <div className="flex flex-col gap-8 max-w-5xl mx-auto">
      {/* Breadcrumb */}
      <motion.div variants={fadeUp} initial="hidden" animate="visible" custom={0}>
        <div className="flex items-center gap-2 text-body-sm text-content-tertiary">
          <button onClick={() => navigate('/collections')} className="hover:text-content-primary transition-colors">Collections</button>
          <span>/</span>
          <button onClick={() => navigate(`/collections/${collectionId}`)} className="hover:text-content-primary transition-colors">{collection.title}</button>
          <span>/</span>
          <span className="text-content-primary font-medium">{scenario.title}</span>
        </div>
      </motion.div>

      {/* Hero */}
      <motion.div variants={fadeUp} initial="hidden" animate="visible" custom={1}>
        <Card variant="elevated" padding="lg" className="relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-accent/5 rounded-full -translate-y-1/3 translate-x-1/3 blur-3xl" />
          <div className="relative flex flex-col gap-5">
            <div className="flex items-start justify-between gap-4">
              <div className="flex flex-col gap-3">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-2xl bg-status-info/10 flex items-center justify-center">
                    <Target className="w-6 h-6 text-status-info" />
                  </div>
                  <div>
                    <h1 className="font-display text-display-lg text-content-primary">{scenario.title}</h1>
                    <p className="text-body-sm text-content-tertiary mt-0.5">Scenario Practice</p>
                  </div>
                </div>
              </div>
              <Button
                variant="primary"
                size="md"
                icon={<Play className="w-4 h-4" />}
                onClick={() => navigate(`/session/scenario/${scenario.id}`)}
              >
                Start Scenario
              </Button>
            </div>

            <p className="text-body-md text-content-secondary leading-relaxed max-w-3xl">
              {scenario.learner_objective}
            </p>

            <div className="flex flex-wrap gap-2">
              {scenario.target_skill_slugs.map((slug) => (
                <Badge key={slug} variant="accent" size="sm">
                  {slug.replace(/-/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())}
                </Badge>
              ))}
            </div>
          </div>
        </Card>
      </motion.div>

      {/* Business Context + Company */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <motion.div variants={fadeUp} initial="hidden" animate="visible" custom={2} className="lg:col-span-2">
          <Card padding="lg" className="flex flex-col gap-4 h-full">
            <div className="flex items-center gap-2">
              <Briefcase className="w-4.5 h-4.5 text-accent" />
              <h2 className="font-display text-display-sm text-content-primary">Business Context</h2>
            </div>
            <p className="text-body-md text-content-primary leading-relaxed">
              {scenario.business_context}
            </p>
            <div className="border-t border-line pt-4">
              <div className="flex items-start gap-3">
                <Target className="w-4 h-4 text-status-info mt-0.5 shrink-0" />
                <div>
                  <span className="text-body-xs font-medium text-content-secondary uppercase tracking-wider">Your Objective</span>
                  <p className="text-body-sm text-content-primary leading-relaxed mt-1">{scenario.learner_objective}</p>
                </div>
              </div>
            </div>
          </Card>
        </motion.div>

        {scenario.mock_company && (
          <motion.div variants={fadeUp} initial="hidden" animate="visible" custom={3}>
            <Card padding="lg" className="flex flex-col gap-4 h-full">
              <div className="flex items-center gap-2">
                <Building2 className="w-4.5 h-4.5 text-status-warning" />
                <h2 className="font-display text-display-sm text-content-primary">Company</h2>
              </div>
              <div className="flex flex-col gap-3">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-status-warning/10 flex items-center justify-center">
                    <Building2 className="w-6 h-6 text-status-warning" />
                  </div>
                  <div>
                    <h3 className="text-body-md font-semibold text-content-primary">{scenario.mock_company.name}</h3>
                    <Badge variant="warning" size="sm">{scenario.mock_company.industry}</Badge>
                  </div>
                </div>
                <div className="flex items-start gap-2 pt-1">
                  <Globe className="w-3.5 h-3.5 text-content-tertiary mt-0.5 shrink-0" />
                  <p className="text-body-xs text-content-secondary leading-relaxed">
                    {scenario.mock_company.operating_context}
                  </p>
                </div>
              </div>
            </Card>
          </motion.div>
        )}
      </div>

      {/* Stakeholders */}
      {scenario.mock_people.length > 0 && (
        <motion.div variants={fadeUp} initial="hidden" animate="visible" custom={4} className="flex flex-col gap-4">
          <SectionHeader
            title="Key Stakeholders"
            subtitle={`${scenario.mock_people.length} people you'll interact with in this scenario`}
          />
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {scenario.mock_people.map((person, i) => (
              <motion.div key={person.id} variants={fadeUp} initial="hidden" animate="visible" custom={4 + i * 0.5}>
                <Card padding="lg" className="flex flex-col gap-4 h-full">
                  <div className="flex items-center gap-4">
                    <Avatar fallback={person.name} size="md" />
                    <div className="flex flex-col gap-0.5">
                      <h4 className="text-body-md font-semibold text-content-primary">{person.name}</h4>
                      <span className="text-body-sm text-accent-text">{person.role}</span>
                    </div>
                  </div>

                  <p className="text-body-sm text-content-secondary italic leading-relaxed border-l-2 border-accent/30 pl-3">
                    {person.relationship_to_scenario}
                  </p>

                  <div className="flex flex-col gap-2">
                    <div className="flex flex-col gap-1">
                      <span className="text-body-xs font-medium text-content-tertiary uppercase tracking-wider">Communication Style</span>
                      <p className="text-body-sm text-content-primary">{person.communication_style}</p>
                    </div>
                  </div>

                  {person.goals.length > 0 && (
                    <div className="flex flex-col gap-2 border-t border-line pt-3">
                      <span className="text-body-xs font-medium text-content-tertiary uppercase tracking-wider">Goals</span>
                      <div className="flex flex-col gap-1.5">
                        {person.goals.map((goal, gi) => (
                          <div key={gi} className="flex items-start gap-2">
                            <div className="w-1.5 h-1.5 rounded-full bg-accent mt-1.5 shrink-0" />
                            <span className="text-body-sm text-content-primary">{goal}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </Card>
              </motion.div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Constraints & Tensions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {scenario.constraints.length > 0 && (
          <motion.div variants={fadeUp} initial="hidden" animate="visible" custom={6} className="flex flex-col gap-4">
            <SectionHeader title="Constraints" subtitle="Rules you cannot break" />
            <div className="flex flex-col gap-3">
              {scenario.constraints.map((constraint, i) => (
                <Card key={i} variant="outlined" padding="md" className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-status-error/10 flex items-center justify-center shrink-0">
                    <AlertTriangle className="w-4 h-4 text-status-error" />
                  </div>
                  <p className="text-body-sm text-content-primary leading-relaxed pt-1">{constraint}</p>
                </Card>
              ))}
            </div>
          </motion.div>
        )}

        {scenario.stakeholder_tensions.length > 0 && (
          <motion.div variants={fadeUp} initial="hidden" animate="visible" custom={7} className="flex flex-col gap-4">
            <SectionHeader title="Stakeholder Tensions" subtitle="Conflicting interests to navigate" />
            <div className="flex flex-col gap-3">
              {scenario.stakeholder_tensions.map((tension, i) => (
                <Card key={i} variant="outlined" padding="md" className="flex items-start gap-3">
                  <div className="w-8 h-8 rounded-lg bg-status-warning/10 flex items-center justify-center shrink-0">
                    <Zap className="w-4 h-4 text-status-warning" />
                  </div>
                  <p className="text-body-sm text-content-primary leading-relaxed pt-1">{tension}</p>
                </Card>
              ))}
            </div>
          </motion.div>
        )}
      </div>

      {/* Start CTA */}
      <motion.div variants={fadeUp} initial="hidden" animate="visible" custom={8}>
        <Card variant="elevated" padding="lg" className="flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex flex-col gap-1 text-center sm:text-left">
            <h3 className="font-display text-display-sm text-content-primary">Ready to begin?</h3>
            <p className="text-body-sm text-content-secondary">
              You'll navigate {scenario.mock_people.length > 0 ? scenario.mock_people.length : 'multiple'} stakeholder{scenario.mock_people.length !== 1 ? 's' : ''} across multiple steps.
            </p>
          </div>
          <Button
            variant="primary"
            size="md"
            icon={<Play className="w-4 h-4" />}
            onClick={() => navigate(`/session/scenario/${scenario.id}`)}
          >
            Start Scenario
          </Button>
        </Card>
      </motion.div>
    </div>
  );
}
