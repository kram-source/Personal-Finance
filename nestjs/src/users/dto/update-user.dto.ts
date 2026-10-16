import { ApiPropertyOptional } from '@nestjs/swagger';
import { IsEmail, IsString, Matches, MaxLength, ValidateIf } from 'class-validator';

export class UpdateUserDto {
  @ApiPropertyOptional({
    description: 'New display name. Send this field, email, or both.',
    example: 'Alex Morgan',
    maxLength: 100,
  })
  @ValidateIf((_object, value) => value !== undefined)
  @IsString()
  @Matches(/\S/)
  @MaxLength(100)
  name?: string;

  @ApiPropertyOptional({
    description: 'New sign-in email address. Send this field, name, or both.',
    example: 'alex@example.com',
    maxLength: 254,
  })
  @ValidateIf((_object, value) => value !== undefined)
  @IsEmail()
  @MaxLength(254)
  email?: string;
}
