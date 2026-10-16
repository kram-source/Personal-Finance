import { ApiProperty } from '@nestjs/swagger';
import { IsEmail, IsString, Matches, MaxLength, MinLength } from 'class-validator';

export class RegisterDto {
  @ApiProperty({ description: 'Name to display on the account.', example: 'Alex Morgan' })
  @IsString()
  @MinLength(1)
  @Matches(/\S/)
  @MaxLength(100)
  name!: string;

  @ApiProperty({ description: 'Email address used to sign in.', example: 'alex@example.com' })
  @IsEmail()
  @MaxLength(254)
  email!: string;

  @ApiProperty({
    description: 'Password for this account; must be 8–72 characters.',
    example: 'FinancePass123',
    minLength: 8,
    maxLength: 72,
  })
  @IsString()
  @MinLength(8)
  @MaxLength(72)
  password!: string;
}
