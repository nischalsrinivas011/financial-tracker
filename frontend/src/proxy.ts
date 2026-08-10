import { clerkMiddleware } from '@clerk/nextjs/server'

// Next.js 16 renamed the middleware entry point from middleware.ts to
// proxy.ts - verified against Clerk's current docs while building this,
// not assumed from older training data.
export default clerkMiddleware()

export const config = {
  matcher: [
    '/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)',
    '/(api|trpc)(.*)',
  ],
}
