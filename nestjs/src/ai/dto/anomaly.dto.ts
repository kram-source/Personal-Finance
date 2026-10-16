import { ApiPropertyOptional } from '@nestjs/swagger';
import { IsNumber, IsOptional, Max, Min } from 'class-validator';

export class AnomalyDto {
  @ApiPropertyOptional({
    description: 'Flag expenses greater than this multiple of their category average.',
    minimum: 1.01,
    maximum: 100,
    default: 2,
    example: 2,
  })
  @IsOptional()
  @IsNumber()
  @Min(1.01)
  @Max(100)
  multiplier = 2;
}
