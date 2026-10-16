import { ApiProperty } from '@nestjs/swagger';
import { Type } from 'class-transformer';
import { IsInt, IsNumber, IsUUID, Max, Min } from 'class-validator';

export class CreateBudgetDto {
  @ApiProperty({
    description: 'UUID of an available expense category; copy an ID from GET /categories.',
    example: '6ba7b810-9dad-41d1-80b4-00c04fd430c8',
  })
  @IsUUID()
  categoryId!: string;

  @ApiProperty({
    description: 'Monthly budget amount.',
    minimum: 0.01,
    example: 500,
  })
  @Type(() => Number)
  @IsNumber({ maxDecimalPlaces: 2 })
  @Min(0.01)
  @Max(1000000000)
  amount!: number;

  @ApiProperty({
    description: 'Calendar year for this budget.',
    minimum: 2000,
    maximum: 2200,
    example: 2026,
  })
  @Type(() => Number)
  @IsInt()
  @Min(2000)
  @Max(2200)
  year!: number;

  @ApiProperty({
    description: 'Calendar month for this budget (1 = January, 12 = December).',
    minimum: 1,
    maximum: 12,
    example: 10,
  })
  @Type(() => Number)
  @IsInt()
  @Min(1)
  @Max(12)
  month!: number;
}
