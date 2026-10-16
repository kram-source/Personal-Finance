import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { TransactionType } from '@prisma/client';
import { IsDateString, IsEnum, IsNotEmpty, IsNumber, IsOptional, IsString, IsUUID, Matches, Max, MaxLength, Min } from 'class-validator';

export class CreateTransactionDto {
  @ApiProperty({
    description: 'Transaction amount, in the account currency.',
    minimum: 0.01,
    example: 42.5,
  })
  @IsNumber({ maxDecimalPlaces: 2 })
  @Min(0.01)
  @Max(1000000000)
  amount!: number;

  @ApiProperty({
    description: 'Choose INCOME for money received or EXPENSE for money spent.',
    enum: TransactionType,
    example: TransactionType.EXPENSE,
  })
  @IsEnum(TransactionType)
  type!: TransactionType;

  @ApiProperty({
    description: 'Short description of the transaction.',
    example: 'Weekly groceries',
    maxLength: 500,
  })
  @IsString()
  @IsNotEmpty()
  @Matches(/\S/)
  @MaxLength(500)
  description!: string;

  @ApiProperty({
    description: 'Transaction date in ISO 8601 format.',
    example: '2026-10-08',
  })
  @IsDateString()
  date!: string;

  @ApiPropertyOptional({
    description:
      'UUID of an available category matching the transaction type. Copy an ID from GET /categories. If omitted, FastAPI suggests a category.',
    example: '6ba7b810-9dad-41d1-80b4-00c04fd430c8',
  })
  @IsOptional()
  @IsUUID()
  categoryId?: string;
}
