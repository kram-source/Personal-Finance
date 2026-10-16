import { BadRequestException, Injectable, NotFoundException } from '@nestjs/common';
import { Prisma, TransactionType } from '@prisma/client';
import { parse } from 'csv-parse/sync';
import { AiService } from '../ai/ai.service';
import { PrismaService } from '../prisma/prisma.service';
import { CreateTransactionDto } from './dto/create-transaction.dto';
import { ListTransactionsDto } from './dto/list-transactions.dto';
import { UpdateTransactionDto } from './dto/update-transaction.dto';

interface CategorizeResponse {
  categoryId?: string | null;
}

interface CsvTransaction {
  row: number;
  date: Date;
  description: string;
  amount: string;
  type: TransactionType;
  category?: string;
}

interface CategorizeSuggestion {
  categoryId?: string | null;
}

const REQUIRED_CSV_COLUMNS = ['date', 'description', 'amount', 'type'];
const ALLOWED_CSV_COLUMNS = new Set([...REQUIRED_CSV_COLUMNS, 'category']);
const MAX_CSV_ROWS = 500;

@Injectable()
export class TransactionsService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly ai: AiService,
  ) {}

  async create(userId: string, input: CreateTransactionDto) {
    let categoryId = input.categoryId;
    if (!categoryId) {
      const suggestion = (await this.ai.categorizeTransaction({
        description: input.description,
        type: input.type,
        userId,
      })) as CategorizeResponse;
      categoryId = suggestion.categoryId ?? undefined;
    }
    if (!categoryId) {
      throw new BadRequestException('No matching category exists for this user');
    }

    await this.assertCategory(userId, categoryId, input.type);
    return this.prisma.transaction.create({
      data: {
        userId,
        amount: new Prisma.Decimal(input.amount),
        type: input.type,
        description: input.description.trim(),
        date: new Date(input.date),
        categoryId,
        source: 'NestJS',
      },
      include: { category: { select: { id: true, name: true, type: true } } },
    });
  }

  async importCsv(userId: string, buffer: Buffer): Promise<{ imported: number }> {
    let csvText: string;
    try {
      csvText = new TextDecoder('utf-8', { fatal: true }).decode(buffer);
    } catch {
      throw new BadRequestException('The CSV file must be valid UTF-8 text');
    }
    if (!csvText.trim()) {
      throw new BadRequestException('The CSV file is empty');
    }

    let records: string[][];
    try {
      records = parse(csvText, {
        bom: true,
        skip_empty_lines: true,
        max_record_size: 10_000,
      }) as string[][];
    } catch {
      throw new BadRequestException('The CSV file contains malformed CSV data or inconsistent columns');
    }
    if (records.length < 2) {
      throw new BadRequestException('The CSV must include a header and at least one transaction row');
    }

    const headers = records[0].map((header) => header.trim().toLowerCase());
    if (
      new Set(headers).size !== headers.length ||
      headers.some((header) => !ALLOWED_CSV_COLUMNS.has(header)) ||
      REQUIRED_CSV_COLUMNS.some((column) => !headers.includes(column))
    ) {
      throw new BadRequestException(
        'CSV columns must be date, description, amount, type, and optional category; column names must not repeat',
      );
    }
    if (records.length - 1 > MAX_CSV_ROWS) {
      throw new BadRequestException(`The CSV cannot contain more than ${MAX_CSV_ROWS} transactions`);
    }

    const rowErrors: string[] = [];
    const transactions: CsvTransaction[] = [];
    for (const [index, record] of records.slice(1).entries()) {
      const rowNumber = index + 2;
      const value = (column: string) => record[headers.indexOf(column)]?.trim() ?? '';
      const errors: string[] = [];

      const dateValue = value('date');
      let transactionDate: Date | undefined;
      if (/^\d{4}-\d{2}-\d{2}$/.test(dateValue)) {
        const parsedDate = new Date(`${dateValue}T00:00:00.000Z`);
        if (
          !Number.isNaN(parsedDate.getTime()) &&
          parsedDate.toISOString().slice(0, 10) === dateValue
        ) {
          transactionDate = parsedDate;
        }
      }
      if (!transactionDate) errors.push('date must use YYYY-MM-DD and be a real calendar date');

      const description = value('description');
      if (!description || description.length > 500) {
        errors.push('description is required and must be at most 500 characters');
      }

      const amount = value('amount');
      if (
        !/^\d+(?:\.\d{1,2})?$/.test(amount) ||
        Number(amount) <= 0 ||
        Number(amount) > 1_000_000_000
      ) {
        errors.push('amount must be a positive number with at most 2 decimal places');
      }

      const typeValue = value('type');
      const type =
        typeValue === TransactionType.EXPENSE || typeValue === TransactionType.INCOME
          ? typeValue
          : undefined;
      if (!type) {
        errors.push('type must be EXPENSE or INCOME');
      }

      const category = value('category') || undefined;
      if (category && category.length > 100) errors.push('category must be at most 100 characters');

      if (errors.length > 0 || !transactionDate || !type) {
        rowErrors.push(`row ${rowNumber}: ${errors.join('; ')}`);
        continue;
      }

      transactions.push({
        row: rowNumber,
        date: transactionDate,
        description,
        amount,
        type,
        category,
      });
    }
    if (rowErrors.length > 0) {
      throw new BadRequestException(`Invalid CSV data: ${rowErrors.join(' | ')}`);
    }

    const categories = await this.prisma.category.findMany({
      where: { OR: [{ userId: null }, { userId }] },
      select: { id: true, name: true, type: true, userId: true },
    });
    categories.sort((left, right) => Number(left.userId === null) - Number(right.userId === null));
    const categoryByNameAndType = new Map<string, (typeof categories)[number]>();
    for (const category of categories) {
      const key = `${category.type}:${category.name.toLowerCase()}`;
      if (!categoryByNameAndType.has(key)) categoryByNameAndType.set(key, category);
    }
    const prepared: Prisma.TransactionCreateManyInput[] = [];
    const categoryErrors: string[] = [];

    for (const transaction of transactions) {
      let categoryId: string | undefined;
      if (transaction.category) {
        const category = categoryByNameAndType.get(
          `${transaction.type}:${transaction.category.toLowerCase()}`,
        );
        if (!category) {
          categoryErrors.push(
            `row ${transaction.row}: category "${transaction.category}" is unavailable for ${transaction.type}`,
          );
          continue;
        }
        categoryId = category.id;
      } else {
        const suggestion = (await this.ai.categorizeTransaction({
          description: transaction.description,
          type: transaction.type,
          userId,
        })) as CategorizeSuggestion;
        const category = categories.find(
          (available) => available.id === suggestion.categoryId && available.type === transaction.type,
        );
        if (!category) {
          categoryErrors.push(
            `row ${transaction.row}: FastAPI did not return an available category for ${transaction.type}`,
          );
          continue;
        }
        categoryId = category.id;
      }

      prepared.push({
        userId,
        amount: new Prisma.Decimal(transaction.amount),
        type: transaction.type,
        description: transaction.description,
        date: transaction.date,
        categoryId,
        source: 'CSV import',
      });
    }
    if (categoryErrors.length > 0) {
      throw new BadRequestException(`Invalid CSV categories: ${categoryErrors.join(' | ')}`);
    }

    const result = await this.prisma.transaction.createMany({ data: prepared });
    return { imported: result.count };
  }

  async list(userId: string, query: ListTransactionsDto) {
    const where: Prisma.TransactionWhereInput = {
      userId,
      ...(query.type ? { type: query.type } : {}),
      ...(query.categoryId ? { categoryId: query.categoryId } : {}),
    };
    const from = query.from ? new Date(query.from) : undefined;
    const to = query.to ? dateUpperBound(query.to) : undefined;
    if (from || to) {
      where.date = {
        ...(from ? { gte: from } : {}),
        ...(to ? { lt: to } : {}),
      };
    }

    const [items, total] = await this.prisma.$transaction([
      this.prisma.transaction.findMany({
        where,
        orderBy: [{ date: 'desc' }, { id: 'desc' }],
        skip: (query.page - 1) * query.limit,
        take: query.limit,
        include: { category: { select: { id: true, name: true, type: true } } },
      }),
      this.prisma.transaction.count({ where }),
    ]);
    return { items, page: query.page, limit: query.limit, total };
  }

  async get(userId: string, id: string) {
    const transaction = await this.prisma.transaction.findFirst({
      where: { id, userId },
      include: { category: { select: { id: true, name: true, type: true } } },
    });
    if (!transaction) {
      throw new NotFoundException('Transaction not found');
    }
    return transaction;
  }

  async update(userId: string, id: string, input: UpdateTransactionDto) {
    const existing = await this.prisma.transaction.findFirst({ where: { id, userId } });
    if (!existing) {
      throw new NotFoundException('Transaction not found');
    }
    const type = input.type ?? existing.type;
    const categoryId = input.categoryId ?? existing.categoryId;
    if (input.categoryId || input.type) {
      await this.assertCategory(userId, categoryId, type);
    }

    return this.prisma.transaction.update({
      where: { id },
      data: {
        ...(input.amount !== undefined ? { amount: new Prisma.Decimal(input.amount) } : {}),
        ...(input.type !== undefined ? { type: input.type } : {}),
        ...(input.description !== undefined ? { description: input.description.trim() } : {}),
        ...(input.date !== undefined ? { date: new Date(input.date) } : {}),
        ...(input.categoryId !== undefined ? { categoryId: input.categoryId } : {}),
      },
      include: { category: { select: { id: true, name: true, type: true } } },
    });
  }

  async remove(userId: string, id: string) {
    const result = await this.prisma.transaction.deleteMany({ where: { id, userId } });
    if (result.count === 0) {
      throw new NotFoundException('Transaction not found');
    }
    return { deleted: true };
  }

  private async assertCategory(userId: string, categoryId: string, type: TransactionType) {
    const category = await this.prisma.category.findFirst({
      where: {
        id: categoryId,
        type,
        OR: [{ userId: null }, { userId }],
      },
      select: { id: true },
    });
    if (!category) {
      throw new BadRequestException('Category is unavailable for this transaction type');
    }
  }
}

function dateUpperBound(value: string): Date {
  const result = new Date(value);
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    result.setUTCDate(result.getUTCDate() + 1);
  }
  return result;
}
