const STATUS_CLASS_BY_VALUE: Record<string, string> = {
  uploaded: "status-badge pending",
  processing: "status-badge pending",
  completed: "status-badge success",
  failed: "status-badge danger",
  draft: "status-badge neutral",
  approved: "status-badge success",
  sent: "status-badge success",
  dismissed: "status-badge danger",
  open: "status-badge neutral",
  exported: "status-badge success",
};

export function StatusBadge({ value }: { value: string }) {
  const className = STATUS_CLASS_BY_VALUE[value] ?? "status-badge neutral";
  return <span className={className}>{value.replaceAll("_", " ")}</span>;
}
