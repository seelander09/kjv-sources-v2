# NBCOT StudyPack Clone

A Next.js 15 application that reimagines the NBCOT StudyPack experience for OT and OTA candidates. The product roadmap includes a marketing site, authenticated learner dashboard, full-length practice exams, mini tests, flashcards, knowledge-match drills, analytics, and adaptive study planning.

## Tech stack

- Next.js 15 (App Router) with React 19 and TypeScript
- Tailwind CSS v4 for styling
- Google Fonts (Plus Jakarta Sans, Source Sans 3)
- Planned integrations: Prisma + PostgreSQL, Stripe Checkout, vector-powered question retrieval, NextAuth

## Getting started

`ash
npm install
npm run dev
`

The app runs at [http://localhost:3000](http://localhost:3000).

## Project structure

`
src/
  app/           # Next.js App Router entrypoints, layouts, and pages
  data/          # Static data powering the marketing site content
public/           # Static assets
`

## Current marketing MVP

The landing page (src/app/page.tsx) now mirrors the StudyPack positioning with:
- Hero CTA highlighting the  practice exam
- Feature grid covering practice exam, mini tests, flashcards, knowledge match, and study plan
- Value proposition section tied to the NBCOT blueprint
- Highlight panel describing the adaptive exam experience
- Testimonials and FAQ accordions
- Closing call-to-action block

## Next steps

1. Flesh out routing for /signup, /tour, /platform, and /contact flows.
2. Introduce authentication, protected dashboards, and question data models.
3. Wire the practice exam engine to the existing NBCOT vector store.
4. Add Stripe Checkout and webhook handling for paid access.

