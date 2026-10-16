import { Controller, Get, Query, UseGuards } from '@nestjs/common';
import {
  ApiBearerAuth,
  ApiBadRequestResponse,
  ApiOkResponse,
  ApiOperation,
  ApiTags,
  ApiUnauthorizedResponse,
} from '@nestjs/swagger';
import { AuthGuard } from '@nestjs/passport';
import { AuthenticatedUser, CurrentUser } from '../common/decorators/current-user.decorator';
import { MonthlyReportQueryDto, TrendsQueryDto } from './monthly-report-query.dto';
import { ReportsService } from './reports.service';

@ApiTags('Reports')
@ApiBearerAuth()
@UseGuards(AuthGuard('jwt'))
@Controller('reports')
export class ReportsController {
  constructor(private readonly reports: ReportsService) {}

  @Get('monthly')
  @ApiOperation({ summary: 'Get your income and spending report for a month' })
  @ApiOkResponse({
    description: 'Monthly income, expenses, net total, transaction count, and expense totals by category.',
    schema: {
      example: {
        year: 2026,
        month: 10,
        income: 4200,
        expenses: 1250.75,
        net: 2949.25,
        transactionCount: 18,
        spendingByCategory: [
          {
            categoryId: '6ba7b810-9dad-41d1-80b4-00c04fd430c8',
            category: 'Groceries',
            amount: 420.5,
          },
          {
            categoryId: '7ba7b810-9dad-41d1-80b4-00c04fd430c8',
            category: 'Transport',
            amount: 180.25,
          },
        ],
      },
    },
  })
  @ApiBadRequestResponse({ description: 'The year or month query parameter is missing or invalid.' })
  @ApiUnauthorizedResponse({ description: 'A valid Bearer access token is required.' })
  monthly(@CurrentUser() user: AuthenticatedUser, @Query() query: MonthlyReportQueryDto) {
    return this.reports.monthly(user.id, query.year, query.month);
  }

  @Get('trends')
  @ApiOperation({ summary: 'Get your income and spending trends over time' })
  @ApiOkResponse({
    description:
      'Monthly income, expenses, net totals, and transaction counts for the requested range. To view these results as a chart, open [the trends chart](http://localhost:3000/trends.html).',
    schema: {
      example: {
        months: 2,
        series: [
          {
            year: 2026,
            month: 9,
            income: 4200,
            expenses: 1250.75,
            net: 2949.25,
            transactionCount: 18,
          },
          {
            year: 2026,
            month: 10,
            income: 4300,
            expenses: 1320.5,
            net: 2979.5,
            transactionCount: 21,
          },
        ],
      },
    },
  })
  @ApiBadRequestResponse({ description: 'The months query parameter must be between 1 and 36.' })
  @ApiUnauthorizedResponse({ description: 'A valid Bearer access token is required.' })
  trends(@CurrentUser() user: AuthenticatedUser, @Query() query: TrendsQueryDto) {
    return this.reports.trends(user.id, query.months);
  }
}
