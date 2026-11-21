import { Link } from '@tanstack/react-router'
export default function NotFound() {
  return <div className="py-16 text-center"><h1 className="text-xl font-semibold">Nie znaleziono strony</h1>
    <Link to="/" className="mt-3 inline-block text-brand hover:underline">Wróć do pulpitu</Link></div>
}
