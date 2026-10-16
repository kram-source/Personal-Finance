import { ApiProperty } from '@nestjs/swagger';
import { Type } from 'class-transformer';
import { IsNumber, Max, Min } from 'class-validator';

export class UpdateBudgetDto {
  @ApiProperty({
    description: 'New monthly budget amount.',
    minimum: 0.01,
    example: 600,
  })
  @Type(() => Number)
  @IsNumber({ maxDecimalPlaces: 2 })
  @Min(0.01)
  @Max(1000000000)
  amount!: number;
}
