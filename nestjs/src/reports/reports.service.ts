import { Injectable } from '@nestjs/common';
import { Prisma, TransactionType } from '@prisma/client';
import { PrismaService } from '../prisma/prisma.service';

interface MonthlyTotalRow {
  month: Date;
  type: TransactionType;
  total: Prisma.Decimal;
  count: bigint;
}

@Injectable()
export class ReportsService {
  constructor(private readonly prisma: PrismaService) {}

  async monthly(userId: string, year: number, month: number) {
    const start = new Date(Date.UTC(year, month - 1, 1));
    const end = new Date(Date.UTC(year, month, 1));
    const where = { userId, date: { gte: start, lt: end } };

    const [totals, categoryTotals] = await Promise.all([
      this.prisma.transaction.groupBy({
        by: ['type'],
        where,
        _sum: { amount: true },
        _count: { id: true },
      }),
      this.prisma.transaction.groupBy({
        by: ['categoryId'],
        where: { ...where, type: TransactionType.EXPENSE },
        _sum: { amount: true },
        orderBy: { _sum: { amount: 'desc' } },
      }),
    ]);

    const categoryIds = categoryTotals.map((item) => item.categoryId);
    const categories = await this.prisma.category.findMany({
      where: { id: { in: categoryIds } },
      select: { id: true, name: true },
    });
    const categoryNames = new Map(categories.map((category) => [category.id, category.name]));
    const incomeRow = totals.find((row) => row.type === TransactionType.INCOME);
    const expenseRow = totals.find((row) => row.type === TransactionType.EXPENSE);
    const income = Number(incomeRow?._sum.amount ?? 0);
    const expenses = Number(expenseRow?._sum.amount ?? 0);

    return {
      year,
      month,
      income: Number(income.toFixed(2)),
      expenses: Number(expenses.toFixed(2)),
      net: Number((income - expenses).toFixed(2)),
      transactionCount: totals.reduce((sum, row) => sum + row._count.id, 0),
      spendingByCategory: categoryTotals.map((row) => ({
        categoryId: row.categoryId,
        category: categoryNames.get(row.categoryId) ?? 'Unknown',
        amount: Number((row._sum.amount ?? 0).toFixed(2)),
      })),
    };
  }

  async trends(userId: string, months: number) {
    const current = new Date();
    const end = new Date(Date.UTC(current.getUTCFullYear(), current.getUTCMonth() + 1, 1));
    const start = new Date(Date.UTC(current.getUTCFullYear(), current.getUTCMonth() - months + 1, 1));
    const grouped = await this.prisma.$queryRaw<MonthlyTotalRow[]>`
      SELECT date_trunc('month', "date") AS month,
             "type" AS type,
             SUM(amount) AS total,
             COUNT(*) AS count
      FROM "Transaction"
      WHERE CAST("userId" AS TEXT) = ${userId}
        AND "date" >= ${start}
        AND "date" < ${end}
      GROUP BY date_trunc('month', "date"), "type"
      ORDER BY month
    `;
    const totalsByMonth = new Map<string, { income: number; expenses: number; count: number }>();
    for (const row of grouped) {
      const key = monthKey(row.month);
      const value = totalsByMonth.get(key) ?? { income: 0, expenses: 0, count: 0 };
      if (row.type === TransactionType.INCOME) {
        value.income = Number(row.total);
      } else {
        value.expenses = Number(row.total);
      }
      value.count += Number(row.count);
      totalsByMonth.set(key, value);
    }

    const series = Array.from({ length: months }, (_, index) => {
      const date = new Date(Date.UTC(start.getUTCFullYear(), start.getUTCMonth() + index, 1));
      const totals = totalsByMonth.get(monthKey(date)) ?? { income: 0, expenses: 0, count: 0 };
      return {
        year: date.getUTCFullYear(),
        month: date.getUTCMonth() + 1,
        income: Number(totals.income.toFixed(2)),
        expenses: Number(totals.expenses.toFixed(2)),
        net: Number((totals.income - totals.expenses).toFixed(2)),
        transactionCount: totals.count,
      };
    });
    return { months, series };
  }
}

function monthKey(date: Date): string {
  return `${date.getUTCFullYear()}-${String(date.getUTCMonth() + 1).padStart(2, '0')}`;
}
