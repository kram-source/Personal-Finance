import { Body, Controller, Delete, Get, Param, ParseUUIDPipe, Patch, Post, Query, UseGuards } from '@nestjs/common';
import {
  ApiBadRequestResponse,
  ApiBearerAuth,
  ApiCreatedResponse,
  ApiNotFoundResponse,
  ApiOkResponse,
  ApiOperation,
  ApiParam,
  ApiTags,
  ApiUnauthorizedResponse,
} from '@nestjs/swagger';
import { AuthGuard } from '@nestjs/passport';
import { AuthenticatedUser, CurrentUser } from '../common/decorators/current-user.decorator';
import { BudgetPeriodDto } from './dto/budget-period.dto';
import { CreateBudgetDto } from './dto/create-budget.dto';
import { UpdateBudgetDto } from './dto/update-budget.dto';
import { BudgetsService } from './budgets.service';

@ApiTags('Budgets')
@ApiBearerAuth()
@UseGuards(AuthGuard('jwt'))
@Controller('budgets')
export class BudgetsController {
  constructor(private readonly budgets: BudgetsService) {}

  @Post()
  @ApiOperation({ summary: 'Create or replace a monthly category budget' })
  @ApiCreatedResponse({
    description: 'The created or replaced budget.',
    schema: {
      example: {
        id: '9ba7b810-9dad-41d1-80b4-00c04fd430c8',
        userId: '550e8400-e29b-41d4-a716-446655440000',
        categoryId: '6ba7b810-9dad-41d1-80b4-00c04fd430c8',
        year: 2026,
        month: 10,
        amount: '500.00',
        createdAt: '2026-10-09T04:30:00.000Z',
        updatedAt: '2026-10-09T04:30:00.000Z',
        category: {
          id: '6ba7b810-9dad-41d1-80b4-00c04fd430c8',
          name: 'Groceries',
        },
      },
    },
  })
  @ApiBadRequestResponse({
    description: 'Budget details are invalid or the category is not an available expense category.',
  })
  @ApiUnauthorizedResponse({ description: 'A valid Bearer access token is required.' })
  createOrReplace(@CurrentUser() user: AuthenticatedUser, @Body() body: CreateBudgetDto) {
    return this.budgets.createOrReplace(user.id, body);
  }

  @Get()
  @ApiOperation({ summary: 'List your budgets for a month' })
  @ApiOkResponse({
    description: 'Your budgets for the requested month.',
    schema: {
      example: [
        {
          id: '9ba7b810-9dad-41d1-80b4-00c04fd430c8',
          userId: '550e8400-e29b-41d4-a716-446655440000',
          categoryId: '6ba7b810-9dad-41d1-80b4-00c04fd430c8',
          year: 2026,
          month: 10,
          amount: '500.00',
          createdAt: '2026-10-09T04:30:00.000Z',
          updatedAt: '2026-10-09T04:30:00.000Z',
          category: {
            id: '6ba7b810-9dad-41d1-80b4-00c04fd430c8',
            name: 'Groceries',
          },
        },
      ],
    },
  })
  @ApiBadRequestResponse({ description: 'The year or month query parameter is invalid.' })
  @ApiUnauthorizedResponse({ description: 'A valid Bearer access token is required.' })
  list(@CurrentUser() user: AuthenticatedUser, @Query() period: BudgetPeriodDto) {
    return this.budgets.list(user.id, period);
  }

  @Get('usage')
  @ApiOperation({ summary: 'View spending against your monthly budgets' })
  @ApiOkResponse({
    description: 'Your budgets with spent, remaining, and percentage-used totals.',
    schema: {
      example: [
        {
          id: '9ba7b810-9dad-41d1-80b4-00c04fd430c8',
          userId: '550e8400-e29b-41d4-a716-446655440000',
          categoryId: '6ba7b810-9dad-41d1-80b4-00c04fd430c8',
          year: 2026,
          month: 10,
          amount: '500.00',
          createdAt: '2026-10-09T04:30:00.000Z',
          updatedAt: '2026-10-09T04:30:00.000Z',
          category: {
            id: '6ba7b810-9dad-41d1-80b4-00c04fd430c8',
            name: 'Groceries',
          },
          budgetAmount: 500,
          spent: 185.5,
          remaining: 314.5,
          percentUsed: 37.1,
        },
      ],
    },
  })
  @ApiBadRequestResponse({ description: 'The year or month query parameter is invalid.' })
  @ApiUnauthorizedResponse({ description: 'A valid Bearer access token is required.' })
  usage(@CurrentUser() user: AuthenticatedUser, @Query() period: BudgetPeriodDto) {
    return this.budgets.usage(user.id, period);
  }

  @Patch(':id')
  @ApiOperation({ summary: 'Update one of your budgets' })
  @ApiParam({
    name: 'id',
    description: 'UUID of your budget; copy it from GET /budgets.',
    example: '9ba7b810-9dad-41d1-80b4-00c04fd430c8',
  })
  @ApiOkResponse({
    description: 'The updated budget.',
    schema: {
      example: {
        id: '9ba7b810-9dad-41d1-80b4-00c04fd430c8',
        userId: '550e8400-e29b-41d4-a716-446655440000',
        categoryId: '6ba7b810-9dad-41d1-80b4-00c04fd430c8',
        year: 2026,
        month: 10,
        amount: '600.00',
        createdAt: '2026-10-09T04:30:00.000Z',
        updatedAt: '2026-10-09T05:00:00.000Z',
        category: {
          id: '6ba7b810-9dad-41d1-80b4-00c04fd430c8',
          name: 'Groceries',
        },
      },
    },
  })
  @ApiBadRequestResponse({ description: 'The budget ID or amount is invalid.' })
  @ApiNotFoundResponse({ description: 'The budget does not exist or does not belong to you.' })
  @ApiUnauthorizedResponse({ description: 'A valid Bearer access token is required.' })
  update(
    @CurrentUser() user: AuthenticatedUser,
    @Param('id', ParseUUIDPipe) id: string,
    @Body() body: UpdateBudgetDto,
  ) {
    return this.budgets.update(user.id, id, body);
  }

  @Delete(':id')
  @ApiOperation({ summary: 'Delete one of your budgets' })
  @ApiParam({
    name: 'id',
    description: 'UUID of your budget; copy it from GET /budgets.',
    example: '9ba7b810-9dad-41d1-80b4-00c04fd430c8',
  })
  @ApiOkResponse({
    description: 'Confirmation that the budget was deleted.',
    schema: { example: { deleted: true } },
  })
  @ApiBadRequestResponse({ description: 'The budget ID must be a valid UUID.' })
  @ApiNotFoundResponse({ description: 'The budget does not exist or does not belong to you.' })
  @ApiUnauthorizedResponse({ description: 'A valid Bearer access token is required.' })
  remove(@CurrentUser() user: AuthenticatedUser, @Param('id', ParseUUIDPipe) id: string) {
    return this.budgets.remove(user.id, id);
  }
}
