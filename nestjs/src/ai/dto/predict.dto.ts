import { ApiPropertyOptional } from '@nestjs/swagger';
import { IsDateString, IsInt, IsOptional, Max, Min } from 'class-validator';

export class PredictDto {
  @ApiPropertyOptional({
    description: 'Number of completed months used as the prediction basis.',
    minimum: 1,
    maximum: 12,
    default: 3,
    example: 3,
  })
  @IsOptional()
  @IsInt()
  @Min(1)
  @Max(12)
  months = 3;

  @ApiPropertyOptional({
    description: 'Optional date to use as the prediction reference point.',
    example: '2026-10-01',
  })
  @IsOptional()
  @IsDateString()
  asOf?: string;
}
