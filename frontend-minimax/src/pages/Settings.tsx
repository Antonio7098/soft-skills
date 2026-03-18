import { type JSX } from 'react';
import { useTheme } from '../theme';
import { Header, Page, Section } from '../components/layout';
import {
  Card,
  ThemeSwitcher,
  Button,
  Badge,
  Avatar,
} from '../components';

export function SettingsPage(): JSX.Element {
  const { activeTheme } = useTheme();

  return (
    <Page maxWidth="900px">
      <Section gap="lg">
        <Header
          title="Settings"
          subtitle="Manage your account and preferences"
          actions={<ThemeSwitcher />}
        />

        <Card variant="default" padding="lg">
          <div style={{ marginBottom: activeTheme.spacing.space6 }}>
            <h3
              style={{
                fontFamily: activeTheme.typography.fontDisplay,
                fontSize: activeTheme.typography.sizeLg,
                fontWeight: activeTheme.typography.weightBold,
                color: activeTheme.colors.text,
                marginBottom: activeTheme.spacing.space4,
              }}
            >
              Profile
            </h3>
            <div style={{ display: 'flex', alignItems: 'center', gap: activeTheme.spacing.space6 }}>
              <Avatar name="Alex Chen" size="xl" />
              <div>
                <h4
                  style={{
                    fontFamily: activeTheme.typography.fontBody,
                    fontSize: activeTheme.typography.sizeLg,
                    fontWeight: activeTheme.typography.weightMedium,
                    color: activeTheme.colors.text,
                  }}
                >
                  Alex Chen
                </h4>
                <p
                  style={{
                    fontFamily: activeTheme.typography.fontBody,
                    fontSize: activeTheme.typography.sizeSm,
                    color: activeTheme.colors.textMuted,
                  }}
                >
                  alex.chen@example.com
                </p>
                <div style={{ display: 'flex', gap: activeTheme.spacing.space2, marginTop: activeTheme.spacing.space2 }}>
                  <Badge variant="primary" size="sm">Member since Jan 2026</Badge>
                  <Badge variant="success" size="sm">Pro Plan</Badge>
                </div>
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: activeTheme.spacing.space3 }}>
            <Button variant="secondary" size="sm">Edit Profile</Button>
            <Button variant="ghost" size="sm">Change Password</Button>
          </div>
        </Card>

        <Card variant="default" padding="lg">
          <div style={{ marginBottom: activeTheme.spacing.space6 }}>
            <h3
              style={{
                fontFamily: activeTheme.typography.fontDisplay,
                fontSize: activeTheme.typography.sizeLg,
                fontWeight: activeTheme.typography.weightBold,
                color: activeTheme.colors.text,
                marginBottom: activeTheme.spacing.space2,
              }}
            >
              Theme
            </h3>
            <p
              style={{
                fontFamily: activeTheme.typography.fontBody,
                fontSize: activeTheme.typography.sizeSm,
                color: activeTheme.colors.textMuted,
              }}
            >
              Choose your preferred visual theme
            </p>
          </div>
          <div style={{ display: 'flex', gap: activeTheme.spacing.space3 }}>
            <ThemeSwitcher />
          </div>
        </Card>

        <Card variant="default" padding="lg">
          <div style={{ marginBottom: activeTheme.spacing.space6 }}>
            <h3
              style={{
                fontFamily: activeTheme.typography.fontDisplay,
                fontSize: activeTheme.typography.sizeLg,
                fontWeight: activeTheme.typography.weightBold,
                color: activeTheme.colors.text,
                marginBottom: activeTheme.spacing.space2,
              }}
            >
              Practice Preferences
            </h3>
            <p
              style={{
                fontFamily: activeTheme.typography.fontBody,
                fontSize: activeTheme.typography.sizeSm,
                color: activeTheme.colors.textMuted,
              }}
            >
              Customize your learning experience
            </p>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: activeTheme.spacing.space4 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h4
                  style={{
                    fontFamily: activeTheme.typography.fontBody,
                    fontSize: activeTheme.typography.sizeBase,
                    fontWeight: activeTheme.typography.weightMedium,
                    color: activeTheme.colors.text,
                  }}
                >
                  Target Role
                </h4>
                <p
                  style={{
                    fontFamily: activeTheme.typography.fontBody,
                    fontSize: activeTheme.typography.sizeSm,
                    color: activeTheme.colors.textMuted,
                  }}
                >
                  Your ideal position helps us recommend relevant scenarios
                </p>
              </div>
              <Badge variant="primary">Tech Lead</Badge>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h4
                  style={{
                    fontFamily: activeTheme.typography.fontBody,
                    fontSize: activeTheme.typography.sizeBase,
                    fontWeight: activeTheme.typography.weightMedium,
                    color: activeTheme.colors.text,
                  }}
                >
                  Practice Difficulty
                </h4>
                <p
                  style={{
                    fontFamily: activeTheme.typography.fontBody,
                    fontSize: activeTheme.typography.sizeSm,
                    color: activeTheme.colors.textMuted,
                  }}
                >
                  Set default difficulty for new practice sessions
                </p>
              </div>
              <Badge variant="warning">Intermediate</Badge>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div>
                <h4
                  style={{
                    fontFamily: activeTheme.typography.fontBody,
                    fontSize: activeTheme.typography.sizeBase,
                    fontWeight: activeTheme.typography.weightMedium,
                    color: activeTheme.colors.text,
                  }}
                >
                  Session Length
                </h4>
                <p
                  style={{
                    fontFamily: activeTheme.typography.fontBody,
                    fontSize: activeTheme.typography.sizeSm,
                    color: activeTheme.colors.textMuted,
                  }}
                >
                  Preferred duration for practice sessions
                </p>
              </div>
              <Badge variant="default">15-30 min</Badge>
            </div>
          </div>
          <div style={{ marginTop: activeTheme.spacing.space4 }}>
            <Button variant="secondary" size="sm">Update Preferences</Button>
          </div>
        </Card>

        <Card variant="default" padding="lg">
          <div style={{ marginBottom: activeTheme.spacing.space6 }}>
            <h3
              style={{
                fontFamily: activeTheme.typography.fontDisplay,
                fontSize: activeTheme.typography.sizeLg,
                fontWeight: activeTheme.typography.weightBold,
                color: activeTheme.colors.text,
                marginBottom: activeTheme.spacing.space2,
              }}
            >
              Notifications
            </h3>
            <p
              style={{
                fontFamily: activeTheme.typography.fontBody,
                fontSize: activeTheme.typography.sizeSm,
                color: activeTheme.colors.textMuted,
              }}
            >
              Choose what updates you receive
            </p>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: activeTheme.spacing.space3 }}>
            {[
              { label: 'Practice reminders', enabled: true, description: 'Get reminded to practice daily' },
              { label: 'Progress updates', enabled: true, description: 'Weekly summary of your progress' },
              { label: 'New content alerts', enabled: false, description: 'Notifications for new collections' },
              { label: 'Coach messages', enabled: true, description: 'Updates from your coach or admin' },
            ].map((item, idx) => (
              <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <h4
                    style={{
                      fontFamily: activeTheme.typography.fontBody,
                      fontSize: activeTheme.typography.sizeBase,
                      color: activeTheme.colors.text,
                    }}
                  >
                    {item.label}
                  </h4>
                  <p
                    style={{
                      fontFamily: activeTheme.typography.fontBody,
                      fontSize: activeTheme.typography.sizeXs,
                      color: activeTheme.colors.textMuted,
                    }}
                  >
                    {item.description}
                  </p>
                </div>
                <button
                  style={{
                    width: '48px',
                    height: '24px',
                    borderRadius: '12px',
                    backgroundColor: item.enabled ? activeTheme.colors.primary : activeTheme.colors.surfaceAlt,
                    border: 'none',
                    cursor: 'pointer',
                    position: 'relative',
                    transition: `background-color ${activeTheme.motion.durationNormal} ${activeTheme.motion.easeOut}`,
                  }}
                >
                  <span
                    style={{
                      position: 'absolute',
                      top: '2px',
                      left: item.enabled ? '26px' : '2px',
                      width: '20px',
                      height: '20px',
                      borderRadius: '50%',
                      backgroundColor: activeTheme.colors.textInverse,
                      transition: `left ${activeTheme.motion.durationNormal} ${activeTheme.motion.easeOut}`,
                    }}
                  />
                </button>
              </div>
            ))}
          </div>
        </Card>

        <Card variant="outlined" padding="lg">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div>
              <h3
                style={{
                  fontFamily: activeTheme.typography.fontDisplay,
                  fontSize: activeTheme.typography.sizeLg,
                  fontWeight: activeTheme.typography.weightBold,
                  color: activeTheme.colors.text,
                }}
              >
                Danger Zone
              </h3>
              <p
                style={{
                  fontFamily: activeTheme.typography.fontBody,
                  fontSize: activeTheme.typography.sizeSm,
                  color: activeTheme.colors.textMuted,
                }}
              >
                Irreversible actions
              </p>
            </div>
            <Button variant="danger" size="sm">Delete Account</Button>
          </div>
        </Card>
      </Section>
    </Page>
  );
}
