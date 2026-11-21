/** Mock data in the shape of the API contract. S4 fills these while backend routers return 501. */
import type { Schemas } from '@/api/client'

export const mockProjects: Schemas['Page_ProjectListItem_'] = { items: [], total: 0, offset: 0, limit: 50 }
