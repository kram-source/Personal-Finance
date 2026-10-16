import { ApiProperty } from '@nestjs/swagger';
import { TransactionType } from '@prisma/client';
import { IsEnum, IsString, Matches, MaxLength } from 'class-validator';

export class CreateCategoryDto {
  @ApiProperty({
    description: 'A name for your custom category.',
    example: 'Groceries',
    maxLength: 100,
  })
  @IsString()
  @Matches(/\S/)
  @MaxLength(100)
  name!: string;

  @ApiProperty({
    description: 'Whether this category is for income or expenses.',
    enum: TransactionType,
    example: TransactionType.EXPENSE,
  })
  @IsEnum(TransactionType)
  type!: TransactionType;
}
