import { createRootRoute, createRoute, createRouter } from '@tanstack/react-router'
import { Layout } from '@/components/Layout'
import Analyses from '@/pages/Analyses'
import AnalysisDetail from '@/pages/AnalysisDetail'
import DocumentPage from '@/pages/DocumentPage'
import HowToTest from '@/pages/HowToTest'
import Knowledge from '@/pages/Knowledge'
import Models from '@/pages/Models'
import SourcePage from '@/pages/SourcePage'
import NewInvestment from '@/pages/NewInvestment'
import NoticePage from '@/pages/NoticePage'
import NotFound from '@/pages/NotFound'
import Ops from '@/pages/Ops'
import ProjectCard from '@/pages/ProjectCard'
import Projects from '@/pages/Projects'
import ReviewQueue from '@/pages/ReviewQueue'
import Start from '@/pages/Start'

const str = (v: unknown) => (typeof v === 'string' && v !== '' ? v : undefined)
const num = (v: unknown) => (v === undefined || v === '' || v === null ? undefined : Number.isFinite(Number(v)) ? Number(v) : undefined)
const bool = (v: unknown) => (v === true || v === 'true' || v === 1 || v === '1' ? true : undefined)

const root = createRootRoute({ component: Layout, notFoundComponent: NotFound })

export const projectsRoute = createRoute({
  getParentRoute: () => root, path: '/projekty', component: Projects,
  validateSearch: (s: Record<string, unknown>) => ({ q: str(s.q), tier: str(s.tier), subsector: str(s.subsector), link_status: str(s.link_status), pending: bool(s.pending) }),
})
export const projectRoute = createRoute({
  getParentRoute: () => root, path: '/projekty/$projectId', component: ProjectCard,
  validateSearch: (s: Record<string, unknown>) => ({ tab: str(s.tab), notice: str(s.notice), section: str(s.section), quote: str(s.quote), doc: str(s.doc), page: num(s.page) }),
})
export const noticeRoute = createRoute({
  getParentRoute: () => root, path: '/ogloszenia/$noticeId', component: NoticePage,
  validateSearch: (s: Record<string, unknown>) => ({ section: str(s.section), quote: str(s.quote) }),
})
export const documentRoute = createRoute({
  getParentRoute: () => root, path: '/dokumenty/$documentId', component: DocumentPage,
  validateSearch: (s: Record<string, unknown>) => ({ page: num(s.page), quote: str(s.quote) }),
})
export const queueRoute = createRoute({
  getParentRoute: () => root, path: '/kolejka', component: ReviewQueue,
  validateSearch: (s: Record<string, unknown>) => ({ type: str(s.type), project: str(s.project), status: str(s.status), item: str(s.item) }),
})
export const knowledgeRoute = createRoute({
  getParentRoute: () => root, path: '/wiedza', component: Knowledge,
  validateSearch: (s: Record<string, unknown>) => ({ table: str(s.table), view: str(s.view) }),
})
export const analysesRoute = createRoute({
  getParentRoute: () => root, path: '/analizy', component: Analyses,
  validateSearch: (s: Record<string, unknown>) => ({ q: str(s.q), status: str(s.status), subsector: str(s.subsector) }),
})
export const analysisRoute = createRoute({
  getParentRoute: () => root, path: '/analizy/$analysisId', component: AnalysisDetail,
  validateSearch: (s: Record<string, unknown>) => ({ tab: str(s.tab) }),
})
export const opsRoute = createRoute({
  getParentRoute: () => root, path: '/zrodla', component: Ops,
  validateSearch: (s: Record<string, unknown>) => ({ tab: str(s.tab) }),
})

export const sourceRoute = createRoute({ getParentRoute: () => root, path: '/zrodlo/$evidenceId', component: SourcePage })

const routeTree = root.addChildren([
  createRoute({ getParentRoute: () => root, path: '/', component: Start }),
  createRoute({ getParentRoute: () => root, path: '/jak-testowac', component: HowToTest }),
  projectsRoute, projectRoute, noticeRoute, documentRoute, queueRoute, knowledgeRoute,
  createRoute({ getParentRoute: () => root, path: '/nowa-inwestycja', component: NewInvestment }),
  analysesRoute, analysisRoute, opsRoute,
  createRoute({ getParentRoute: () => root, path: '/modele', component: Models }),
  sourceRoute,
])

export const router = createRouter({ routeTree, defaultPreload: 'intent', scrollRestoration: true })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
