import { ApiPropertyOptional } from '@nestjs/swagger';
import { TransactionType } from '@prisma/client';
import { IsEnum, IsString, Matches, MaxLength, ValidateIf } from 'class-validator';

export class UpdateCategoryDto {
  @ApiPropertyOptional({
    description: 'New category name.',
    example: 'Food and groceries',
    maxLength: 100,
  })
  @ValidateIf((_object, value) => value !== undefined)
  @IsString()
  @Matches(/\S/)
  @MaxLength(100)
  name?: string;

  @ApiPropertyOptional({
    description: 'New category type. Changing type may be blocked by existing records.',
    enum: TransactionType,
    example: TransactionType.EXPENSE,
  })
  @ValidateIf((_object, value) => value !== undefined)
  @IsEnum(TransactionType)
  type?: TransactionType;
}
