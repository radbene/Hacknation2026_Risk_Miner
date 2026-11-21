import { useEvidence, SourcePreview } from '@/components/evidence/EvidencePanel'
import { PageHeader } from '@/components/PageHeader'
import { Empty, Loading } from '@/components/ui'
import { sourceRoute } from '@/router'

/** One source on its own page: the real file, as large as the window allows, with the cited spot marked. */
export default function SourcePage() {
  const { evidenceId } = sourceRoute.useParams()
  const q = useEvidence([evidenceId])
  if (q.isLoading) return <Loading />
  const e = q.data?.[0]
  if (!e) return <Empty>Nie znaleziono źródła.</Empty>
  return (
    <div>
      <PageHeader back title="Źródło" />
      <SourcePreview e={e} full />
    </div>
  )
}
