type Props = {
  label: string;
  value: string;
  sub?: string;
};

export function StatCard({ label, value, sub }: Props) {
  return (
    <div className="border rounded-lg p-4 bg-white">
      <div className="text-xs uppercase tracking-wide text-gray-500">{label}</div>
      <div className="text-2xl font-semibold mt-1">{value}</div>
      {sub && <div className="text-xs text-gray-500 mt-1">{sub}</div>}
    </div>
  );
}
