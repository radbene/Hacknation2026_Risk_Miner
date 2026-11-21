import { createRootRoute, createRoute, createRouter } from '@tanstack/react-router'
import { Layout } from '@/components/Layout'
import Analyses from '@/pages/Analyses'
import AnalysisDetail from '@/pages/AnalysisDetail'
import HowToTest from '@/pages/HowToTest'
import Knowledge from '@/pages/Knowledge'
import NewInvestment from '@/pages/NewInvestment'
import Ops from '@/pages/Ops'
import ProjectCard from '@/pages/ProjectCard'
import Projects from '@/pages/Projects'
import ReviewQueue from '@/pages/ReviewQueue'
import Start from '@/pages/Start'

const root = createRootRoute({ component: Layout })

const routeTree = root.addChildren([
  createRoute({ getParentRoute: () => root, path: '/', component: Start }),
  createRoute({ getParentRoute: () => root, path: '/jak-testowac', component: HowToTest }),
  createRoute({ getParentRoute: () => root, path: '/projekty', component: Projects }),
  createRoute({ getParentRoute: () => root, path: '/projekty/$projectId', component: ProjectCard }),
  createRoute({ getParentRoute: () => root, path: '/kolejka', component: ReviewQueue }),
  createRoute({ getParentRoute: () => root, path: '/wiedza', component: Knowledge }),
  createRoute({ getParentRoute: () => root, path: '/nowa-inwestycja', component: NewInvestment }),
  createRoute({ getParentRoute: () => root, path: '/analizy', component: Analyses }),
  createRoute({ getParentRoute: () => root, path: '/analizy/$analysisId', component: AnalysisDetail }),
  createRoute({ getParentRoute: () => root, path: '/zrodla', component: Ops }),
])

export const router = createRouter({ routeTree })

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router
  }
}
