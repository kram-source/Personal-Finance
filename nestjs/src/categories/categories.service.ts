import { BadRequestException, Injectable, NotFoundException } from '@nestjs/common';
import { TransactionType } from '@prisma/client';
import { PrismaService } from '../prisma/prisma.service';
import { CreateCategoryDto } from './dto/create-category.dto';
import { UpdateCategoryDto } from './dto/update-category.dto';

@Injectable()
export class CategoriesService {
  constructor(private readonly prisma: PrismaService) {}

  create(userId: string, input: CreateCategoryDto) {
    return this.prisma.category.create({
      data: {
        userId,
        name: input.name.trim(),
        type: input.type,
      },
      select: { id: true, name: true, type: true },
    });
  }

  async update(userId: string, id: string, input: UpdateCategoryDto) {
    if (input.name === undefined && input.type === undefined) {
      throw new BadRequestException('Provide a name or type to update');
    }

    const category = await this.prisma.category.findFirst({
      where: { id, userId },
      select: { id: true, type: true },
    });
    if (!category) {
      throw new NotFoundException('Custom category not found');
    }

    if (input.type !== undefined && input.type !== category.type) {
      const [incompatibleTransactions, budgets] = await Promise.all([
        this.prisma.transaction.count({
          where: { categoryId: id, type: { not: input.type } },
        }),
        input.type === TransactionType.INCOME
          ? this.prisma.budget.count({ where: { categoryId: id } })
          : Promise.resolve(0),
      ]);
      if (incompatibleTransactions > 0 || budgets > 0) {
        throw new BadRequestException(
          'Category type cannot be changed while it has incompatible transactions or budgets',
        );
      }
    }

    const result = await this.prisma.category.updateMany({
      where: { id, userId },
      data: {
        ...(input.name !== undefined ? { name: input.name.trim() } : {}),
        ...(input.type !== undefined ? { type: input.type } : {}),
      },
    });
    if (result.count === 0) {
      throw new NotFoundException('Custom category not found');
    }
    return this.prisma.category.findFirstOrThrow({
      where: { id, userId },
      select: { id: true, name: true, type: true },
    });
  }

  async remove(userId: string, id: string) {
    const category = await this.prisma.category.findFirst({
      where: { id, userId },
      select: { id: true },
    });
    if (!category) {
      throw new NotFoundException('Custom category not found');
    }

    const [transactions, budgets] = await Promise.all([
      this.prisma.transaction.count({ where: { categoryId: id } }),
      this.prisma.budget.count({ where: { categoryId: id } }),
    ]);
    if (transactions > 0 || budgets > 0) {
      throw new BadRequestException(
        'Category cannot be deleted while it has transactions or budgets',
      );
    }

    const result = await this.prisma.category.deleteMany({ where: { id, userId } });
    if (result.count === 0) {
      throw new NotFoundException('Custom category not found');
    }
    return { deleted: true };
  }

  list(userId: string) {
    return this.prisma.category.findMany({
      where: { OR: [{ userId: null }, { userId }] },
      orderBy: [{ type: 'asc' }, { name: 'asc' }],
      select: { id: true, name: true, type: true },
    });
  }
}
