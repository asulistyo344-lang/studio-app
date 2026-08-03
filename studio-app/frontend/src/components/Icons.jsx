function IconBase({ children, ...props }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      {children}
    </svg>
  );
}

export function IconHome(props) {
  return (
    <IconBase {...props}>
      <path d="M3 11.5 12 4l9 7.5" />
      <path d="M5.5 9.5V20h13V9.5" />
      <path d="M9.5 20v-6h5v6" />
    </IconBase>
  );
}

export function IconBuilding(props) {
  return (
    <IconBase {...props}>
      <rect x="5" y="3" width="14" height="18" rx="1" />
      <path d="M9 8h1M14 8h1M9 12h1M14 12h1M9 16h1M14 16h1" />
      <path d="M10 21v-3h4v3" />
    </IconBase>
  );
}

export function IconShirt(props) {
  return (
    <IconBase {...props}>
      <path d="M8 4 4 7l2 3 2-1.5V20h8V8.5L18 10l2-3-4-3-2 1.5h-4L8 4Z" />
    </IconBase>
  );
}

export function IconCube(props) {
  return (
    <IconBase {...props}>
      <path d="M12 3 4 7v10l8 4 8-4V7l-8-4Z" />
      <path d="M4 7l8 4 8-4" />
      <path d="M12 11v10" />
    </IconBase>
  );
}

export function IconBolt(props) {
  return (
    <IconBase {...props}>
      <path d="M13 3 4 14h6l-1 7 9-11h-6l1-7Z" />
    </IconBase>
  );
}

export function IconSparkle(props) {
  return (
    <IconBase {...props}>
      <path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5 18 18M18 6l-2.5 2.5M8.5 15.5 6 18" />
      <circle cx="12" cy="12" r="3" />
    </IconBase>
  );
}

export function IconRun(props) {
  return (
    <IconBase {...props}>
      <circle cx="14.5" cy="4.5" r="1.5" />
      <path d="M9 20l2.5-4 2-2-1-4-3 1-2 4M13.5 14l3 1 2.5 4M11.5 10l2-2.5 3 1" />
    </IconBase>
  );
}

export function IconClose(props) {
  return (
    <IconBase {...props}>
      <path d="M6 6l12 12M18 6 6 18" />
    </IconBase>
  );
}
