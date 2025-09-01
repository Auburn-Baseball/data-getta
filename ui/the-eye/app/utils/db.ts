/*
* Initiates Prisma client to be used for the app.
* 
* author: Braden Mosley
* lastEdit: 04-15-2024
*/

import { PrismaClient } from '@prisma/client'

// Creates a single connection to the database to fix the Next.js dev server reload issue
const globalForPrisma = global as unknown as {
  prisma: PrismaClient | undefined
}

export const prisma =
  globalForPrisma.prisma ??
  new PrismaClient({
    log: ["query"],
  })

if (process.env.NODE_ENV !== "production") globalForPrisma.prisma = prisma