export function Placeholder({ title, owner, children }: { title: string; owner: string; children?: React.ReactNode }) {
  return (
    <div>
      <h1 className="mb-2 text-2xl font-semibold">{title}</h1>
      <p className="text-sm text-slate-500">W budowie ({owner}).</p>
      {children}
    </div>
  )
}
