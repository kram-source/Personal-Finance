import { ApiProperty } from '@nestjs/swagger';
import { IsEmail, IsString, MaxLength, MinLength } from 'class-validator';

export class LoginDto {
  @ApiProperty({
    description: 'Email address used when registering the account.',
    example: 'alex@example.com',
  })
  @IsEmail()
  @MaxLength(254)
  email!: string;

  @ApiProperty({
    description: 'The account password (8–72 characters).',
    example: 'FinancePass123',
    minLength: 8,
    maxLength: 72,
  })
  @IsString()
  @MinLength(1)
  @MaxLength(72)
  password!: string;
}
