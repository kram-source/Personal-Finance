const { PrismaClient } = require('@prisma/client');

const prisma = new PrismaClient();
const categories = [
  ['Food', 'EXPENSE'],
  ['Transport', 'EXPENSE'],
  ['Shopping', 'EXPENSE'],
  ['Bills', 'EXPENSE'],
  ['Entertainment', 'EXPENSE'],
  ['Healthcare', 'EXPENSE'],
  ['Salary', 'INCOME'],
  ['Freelance', 'INCOME'],
  ['Other', 'EXPENSE'],
  ['Other', 'INCOME'],
];

async function seed() {
  for (const [name, type] of categories) {
    const existing = await prisma.category.findFirst({
      where: { name, type, userId: null },
      select: { id: true },
    });
    if (!existing) {
      await prisma.category.create({ data: { name, type } });
    }
  }
}

seed()
  .catch((error) => {
    console.error('Category seed failed:', error);
    process.exitCode = 1;
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
