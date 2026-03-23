import type { HTMLAttributes } from "react";

type AvatarSize = "xs" | "sm" | "md" | "lg" | "xl";

interface AvatarProps extends HTMLAttributes<HTMLDivElement> {
  name: string;
  src?: string;
  size?: AvatarSize;
  status?: "online" | "offline" | "away" | "busy";
}

const sizeMap: Record<AvatarSize, number> = {
  xs: 24,
  sm: 32,
  md: 40,
  lg: 56,
  xl: 72,
};

const fontSizeMap: Record<AvatarSize, string> = {
  xs: "var(--font-size-xs)",
  sm: "var(--font-size-sm)",
  md: "var(--font-size-base)",
  lg: "var(--font-size-xl)",
  xl: "var(--font-size-2xl)",
};

const statusColors: Record<string, string> = {
  online: "var(--color-status-success)",
  offline: "var(--color-text-tertiary)",
  away: "var(--color-status-warning)",
  busy: "var(--color-status-error)",
};

function getInitials(name: string): string {
  const parts = name.trim().split(/\s+/);
  if (parts.length === 1) return parts[0].charAt(0).toUpperCase();
  return (parts[0].charAt(0) + parts[parts.length - 1].charAt(0)).toUpperCase();
}

function getColorFromName(name: string): string {
  const colors = [
    "#C87533",
    "#5B9A6F",
    "#5B8EC4",
    "#9B6BC4",
    "#C45B8E",
    "#C4A55B",
    "#6BC4B8",
    "#C4705B",
  ];
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length];
}

export function Avatar({
  name,
  src,
  size = "md",
  status,
  style,
  ...props
}: AvatarProps) {
  const px = sizeMap[size];
  const showStatus = status && size !== "xs";

  return (
    <div
      style={{
        position: "relative",
        display: "inline-flex",
        flexShrink: 0,
        ...style,
      }}
      {...props}
    >
      {src ? (
        <img
          src={src}
          alt={name}
          style={{
            width: px,
            height: px,
            borderRadius: "var(--radius-full)",
            objectFit: "cover",
            border: "2px solid var(--color-border-subtle)",
          }}
        />
      ) : (
        <div
          style={{
            width: px,
            height: px,
            borderRadius: "var(--radius-full)",
            backgroundColor: getColorFromName(name),
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: fontSizeMap[size],
            fontWeight: "var(--font-weight-semibold)",
            color: "#fff",
            fontFamily: "var(--font-body)",
            border: "2px solid var(--color-border-subtle)",
          }}
        >
          {getInitials(name)}
        </div>
      )}
      {showStatus && (
        <span
          style={{
            position: "absolute",
            bottom: 0,
            right: 0,
            width: size === "sm" ? 8 : size === "lg" || size === "xl" ? 14 : 10,
            height: size === "sm" ? 8 : size === "lg" || size === "xl" ? 14 : 10,
            borderRadius: "50%",
            backgroundColor: statusColors[status!],
            border: "2px solid var(--color-bg-primary)",
          }}
        />
      )}
    </div>
  );
}
