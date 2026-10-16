import { ApiPropertyOptional } from '@nestjs/swagger';
import { Type } from 'class-transformer';
import { IsInt, IsOptional, Max, Min } from 'class-validator';

export class BudgetPeriodDto {
  @ApiPropertyOptional({
    description: 'Calendar year. Defaults to the current year.',
    minimum: 2000,
    maximum: 2200,
    example: 2026,
  })
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(2000)
  @Max(2200)
  year?: number;

  @ApiPropertyOptional({
    description: 'Calendar month (1 = January, 12 = December). Defaults to the current month.',
    minimum: 1,
    maximum: 12,
    example: 10,
  })
  @IsOptional()
  @Type(() => Number)
  @IsInt()
  @Min(1)
  @Max(12)
  month?: number;
}
