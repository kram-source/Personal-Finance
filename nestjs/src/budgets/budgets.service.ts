import { BadRequestException, Injectable, NotFoundException } from '@nestjs/common';
import { Prisma, TransactionType } from '@prisma/client';
import { PrismaService } from '../prisma/prisma.service';
import { BudgetPeriodDto } from './dto/budget-period.dto';
import { CreateBudgetDto } from './dto/create-budget.dto';
import { UpdateBudgetDto } from './dto/update-budget.dto';

@Injectable()
export class BudgetsService {
  constructor(private readonly prisma: PrismaService) {}

  async createOrReplace(userId: string, input: CreateBudgetDto) {
    const category = await this.prisma.category.findFirst({
      where: {
        id: input.categoryId,
        type: TransactionType.EXPENSE,
        OR: [{ userId: null }, { userId }],
      },
      select: { id: true },
    });
    if (!category) {
      throw new BadRequestException('Budget category must be an available expense category');
    }

    return this.prisma.budget.upsert({
      where: {
        userId_categoryId_year_month: {
          userId,
          categoryId: input.categoryId,
          year: input.year,
          month: input.month,
        },
      },
      create: {
        userId,
        categoryId: input.categoryId,
        amount: new Prisma.Decimal(input.amount),
        year: input.year,
        month: input.month,
      },
      update: { amount: new Prisma.Decimal(input.amount) },
      include: { category: { select: { id: true, name: true } } },
    });
  }

  async list(userId: string, period: BudgetPeriodDto) {
    const { year, month } = resolvePeriod(period);
    return this.prisma.budget.findMany({
      where: { userId, year, month },
      orderBy: { category: { name: 'asc' } },
      include: { category: { select: { id: true, name: true } } },
    });
  }

  async usage(userId: string, period: BudgetPeriodDto) {
    const { year, month } = resolvePeriod(period);
    const start = new Date(Date.UTC(year, month - 1, 1));
    const end = new Date(Date.UTC(year, month, 1));
    const [budgets, totals] = await Promise.all([
      this.prisma.budget.findMany({
        where: { userId, year, month },
        orderBy: { category: { name: 'asc' } },
        include: { category: { select: { id: true, name: true } } },
      }),
      this.prisma.transaction.groupBy({
        by: ['categoryId'],
        where: {
          userId,
          type: TransactionType.EXPENSE,
          date: { gte: start, lt: end },
        },
        _sum: { amount: true },
      }),
    ]);
    const spentByCategory = new Map(
      totals.map((row) => [row.categoryId, Number(row._sum.amount ?? 0)]),
    );

    return budgets.map((budget) => {
      const amount = Number(budget.amount);
      const spent = spentByCategory.get(budget.categoryId) ?? 0;
      return {
        ...budget,
        budgetAmount: amount,
        spent: Number(spent.toFixed(2)),
        remaining: Number((amount - spent).toFixed(2)),
        percentUsed: Number(((spent / amount) * 100).toFixed(2)),
      };
    });
  }

  async update(userId: string, id: string, input: UpdateBudgetDto) {
    const result = await this.prisma.budget.updateMany({
      where: { id, userId },
      data: { amount: new Prisma.Decimal(input.amount) },
    });
    if (result.count === 0) {
      throw new NotFoundException('Budget not found');
    }
    return this.prisma.budget.findUniqueOrThrow({
      where: { id },
      include: { category: { select: { id: true, name: true } } },
    });
  }

  async remove(userId: string, id: string) {
    const result = await this.prisma.budget.deleteMany({ where: { id, userId } });
    if (result.count === 0) {
      throw new NotFoundException('Budget not found');
    }
    return { deleted: true };
  }
}

function resolvePeriod(period: BudgetPeriodDto): { year: number; month: number } {
  const now = new Date();
  return { year: period.year ?? now.getUTCFullYear(), month: period.month ?? now.getUTCMonth() + 1 };
}
