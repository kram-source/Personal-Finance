import { Body, Controller, Post } from '@nestjs/common';
import {
  ApiBadRequestResponse,
  ApiCreatedResponse,
  ApiConflictResponse,
  ApiOperation,
  ApiUnauthorizedResponse,
  ApiTags,
} from '@nestjs/swagger';
import { AuthService } from './auth.service';
import { LoginDto } from './dto/login.dto';
import { RegisterDto } from './dto/register.dto';

@ApiTags('Authentication')
@Controller('auth')
export class AuthController {
  constructor(private readonly auth: AuthService) {}

  @Post('register')
  @ApiOperation({
    summary: 'Create a user account and receive an access token',
    description:
      'Creates an account and returns a JWT access token. Use the token as a Bearer token when calling protected endpoints.',
  })
  @ApiBadRequestResponse({ description: 'The account details failed validation.' })
  @ApiConflictResponse({ description: 'An account with this email already exists.' })
  @ApiCreatedResponse({
    description: 'Account created successfully. The access token can be used immediately.',
    schema: {
      example: {
        user: {
          id: '550e8400-e29b-41d4-a716-446655440000',
          name: 'Alex Morgan',
          email: 'alex@example.com',
          createdAt: '2026-10-09T04:30:00.000Z',
        },
        accessToken: '<JWT access token>',
      },
    },
  })
  register(@Body() body: RegisterDto) {
    return this.auth.register(body);
  }

  @Post('login')
  @ApiOperation({ summary: 'Sign in and receive an access token' })
  @ApiBadRequestResponse({ description: 'The email or password format failed validation.' })
  @ApiUnauthorizedResponse({ description: 'The email or password is incorrect.' })
  @ApiCreatedResponse({
    description: 'Signed in successfully.',
    schema: {
      example: {
        user: {
          id: '550e8400-e29b-41d4-a716-446655440000',
          name: 'Alex Morgan',
          email: 'alex@example.com',
        },
        accessToken: '<JWT access token>',
      },
    },
  })
  login(@Body() body: LoginDto) {
    return this.auth.login(body);
  }

}
