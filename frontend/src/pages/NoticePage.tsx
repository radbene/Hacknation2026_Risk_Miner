import { NoticeView } from '@/components/evidence/NoticeView'
import { PageHeader } from '@/components/PageHeader'
import { noticeRoute } from '@/router'

export default function NoticePage() {
  const { noticeId } = noticeRoute.useParams()
  const { section, quote } = noticeRoute.useSearch()
  return (
    <div className="mx-auto max-w-5xl">
      <PageHeader title="Ogłoszenie BZP" back description={section ? `Wskazana sekcja: ${section}` : 'Treść ogłoszenia w numerowanych sekcjach'} />
      <NoticeView noticeId={noticeId} section={section} quote={quote} />
    </div>
  )
}
