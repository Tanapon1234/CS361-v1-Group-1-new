export default function ManageLoading() {
  return (
    <div className="space-y-4" aria-busy="true" aria-label="กำลังโหลด">
      <div className="h-8 w-64 animate-pulse rounded bg-line/50" />
      <div className="h-40 animate-pulse rounded-xl bg-line/30" />
      <div className="h-40 animate-pulse rounded-xl bg-line/30" />
    </div>
  );
}
