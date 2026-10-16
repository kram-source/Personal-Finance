import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { IsIn, IsOptional, IsString, MaxLength } from 'class-validator';

export class CategorizeDto {
  @ApiProperty({
    description: 'Transaction description to categorize.',
    example: 'Uber ride to airport',
  })
  @IsString()
  @MaxLength(500)
  description!: string;

  @ApiPropertyOptional({
    description: 'Transaction type; defaults to EXPENSE.',
    enum: ['EXPENSE', 'INCOME'],
    default: 'EXPENSE',
    example: 'EXPENSE',
  })
  @IsOptional()
  @IsIn(['EXPENSE', 'INCOME'])
  type?: 'EXPENSE' | 'INCOME';
}
