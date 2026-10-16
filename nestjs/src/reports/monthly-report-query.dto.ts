import { ApiProperty } from '@nestjs/swagger';
import { Type } from 'class-transformer';
import { IsInt, Max, Min } from 'class-validator';

export class MonthlyReportQueryDto {
  @ApiProperty({
    description: 'Calendar year for the report.',
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
    description: 'Calendar month (1 = January, 12 = December).',
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

export class TrendsQueryDto {
  @ApiProperty({
    description: 'Number of recent months to include.',
    minimum: 1,
    maximum: 36,
    default: 6,
    example: 6,
  })
  @Type(() => Number)
  @IsInt()
  @Min(1)
  @Max(36)
  months = 6;
}
