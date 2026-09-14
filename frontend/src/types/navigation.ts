export const APP_ROUTES = [
  '/',
  '/voice',
  '/dashboard',
  '/documents',
  '/schemes',
  '/grievances',
  '/notifications',
  '/profile',
  '/onboarding',
] as const

export type AppRoute = (typeof APP_ROUTES)[number]

export function asAppRoute(pathname: string): AppRoute {
  return (APP_ROUTES as readonly string[]).includes(pathname) ? pathname as AppRoute : '/'
}
