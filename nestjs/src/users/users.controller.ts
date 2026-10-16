import { Body, Controller, Get, Patch, UseGuards } from '@nestjs/common';
import {
  ApiBadRequestResponse,
  ApiBearerAuth,
  ApiConflictResponse,
  ApiOkResponse,
  ApiOperation,
  ApiUnauthorizedResponse,
  ApiTags,
} from '@nestjs/swagger';
import { AuthGuard } from '@nestjs/passport';
import { AuthenticatedUser, CurrentUser } from '../common/decorators/current-user.decorator';
import { UpdateUserDto } from './dto/update-user.dto';
import { UsersService } from './users.service';

@ApiTags('Users')
@ApiBearerAuth()
@UseGuards(AuthGuard('jwt'))
@Controller('users')
export class UsersController {
  constructor(private readonly users: UsersService) {}

  @Get('profile')
  @ApiOperation({ summary: 'Get your user profile' })
  @ApiOkResponse({
    description: 'The authenticated user profile.',
    schema: {
      example: {
        id: '550e8400-e29b-41d4-a716-446655440000',
        name: 'Alex Morgan',
        email: 'alex@example.com',
        createdAt: '2026-10-09T04:30:00.000Z',
      },
    },
  })
  @ApiUnauthorizedResponse({ description: 'The access token is missing, invalid, or the account is unavailable.' })
  getMe(@CurrentUser() user: AuthenticatedUser) {
    return this.users.getMe(user.id);
  }

  @Patch('profile')
  @ApiOperation({ summary: 'Update your user profile' })
  @ApiOkResponse({
    description: 'The updated user profile.',
    schema: {
      example: {
        id: '550e8400-e29b-41d4-a716-446655440000',
        name: 'Alex Morgan',
        email: 'alex@example.com',
        createdAt: '2026-10-09T04:30:00.000Z',
      },
    },
  })
  @ApiBadRequestResponse({ description: 'The profile fields are invalid or no fields were provided.' })
  @ApiConflictResponse({ description: 'The email address is already used by another account.' })
  @ApiUnauthorizedResponse({ description: 'The access token is missing, invalid, or the account is unavailable.' })
  updateMe(@CurrentUser() user: AuthenticatedUser, @Body() body: UpdateUserDto) {
    return this.users.updateMe(user.id, body);
  }
}
