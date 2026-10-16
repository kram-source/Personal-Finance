import { Body, Controller, Get, HttpCode, HttpStatus, Post, Query, UseGuards } from '@nestjs/common';
import {
  ApiBadGatewayResponse,
  ApiBadRequestResponse,
  ApiBearerAuth,
  ApiCreatedResponse,
  ApiNotFoundResponse,
  ApiOkResponse,
  ApiOperation,
  ApiServiceUnavailableResponse,
  ApiTags,
  ApiUnauthorizedResponse,
} from '@nestjs/swagger';
import { AuthGuard } from '@nestjs/passport';
import { AuthenticatedUser, CurrentUser } from '../common/decorators/current-user.decorator';
import { AiService } from './ai.service';
import { AnomalyDto } from './dto/anomaly.dto';
import { CategorizeDto } from './dto/categorize.dto';
import { PredictDto } from './dto/predict.dto';

@ApiTags('AI')
@ApiBearerAuth()
@UseGuards(AuthGuard('jwt'))
@Controller('ai')
export class AiController {
  constructor(private readonly ai: AiService) {}

  @Post('predict-spending')
  @HttpCode(HttpStatus.OK)
  @ApiOperation({ summary: 'Predict your spending by category' })
  @ApiOkResponse({
    description: 'Predicted spending totals returned by the analytics service.',
    schema: {
      example: {
        userId: '550e8400-e29b-41d4-a716-446655440000',
        year: 2026,
        month: 11,
        totalPredicted: 760,
        basedOn: {
          start: '2026-08-01',
          end: '2026-10-31',
          months: 3,
        },
        predictions: [
          {
            category: 'Food',
            categoryId: '6ba7b810-9dad-41d1-80b4-00c04fd430c8',
            predictedAmount: 450,
          },
          {
            category: 'Transport',
            categoryId: '7ba7b810-9dad-41d1-80b4-00c04fd430c8',
            predictedAmount: 310,
          },
        ],
      },
    },
  })
  @ApiBadRequestResponse({ description: 'The prediction options are invalid.' })
  @ApiNotFoundResponse({ description: 'FastAPI could not find the authenticated user.' })
  @ApiBadGatewayResponse({ description: 'FastAPI rejected or failed the prediction request.' })
  @ApiServiceUnavailableResponse({ description: 'FastAPI is unavailable.' })
  @ApiUnauthorizedResponse({ description: 'A valid Bearer access token is required.' })
  predict(@CurrentUser() user: AuthenticatedUser, @Body() body: PredictDto) {
    return this.ai.predictSpending(user.id, body.months, body.asOf);
  }

  @Post('detect-anomaly')
  @HttpCode(HttpStatus.OK)
  @ApiOperation({ summary: 'Find unusually large expenses in your transactions' })
  @ApiOkResponse({
    description: 'Expenses identified as unusually large compared with their category average.',
    schema: {
      example: {
        userId: '550e8400-e29b-41d4-a716-446655440000',
        multiplier: 2,
        anomalies: [
          {
            transactionId: '8ba7b810-9dad-41d1-80b4-00c04fd430c8',
            description: 'Large grocery purchase',
            category: 'Food',
            categoryId: '6ba7b810-9dad-41d1-80b4-00c04fd430c8',
            amount: 250,
            date: '2026-10-08',
            categoryAverage: 80,
            timesAverage: 3.125,
          },
        ],
      },
    },
  })
  @ApiBadRequestResponse({ description: 'The anomaly multiplier is invalid.' })
  @ApiNotFoundResponse({ description: 'FastAPI could not find the authenticated user.' })
  @ApiBadGatewayResponse({ description: 'FastAPI rejected or failed the anomaly detection request.' })
  @ApiServiceUnavailableResponse({ description: 'FastAPI is unavailable.' })
  @ApiUnauthorizedResponse({ description: 'A valid Bearer access token is required.' })
  detectAnomalies(@CurrentUser() user: AuthenticatedUser, @Body() body: AnomalyDto) {
    return this.ai.detectAnomaly(user.id, body.multiplier);
  }

  @Post('categorize')
  @ApiOperation({ summary: 'Suggest a category for a transaction description' })
  @ApiCreatedResponse({
    description: 'Suggested category for the supplied description and transaction type.',
    schema: {
      example: {
        description: 'Uber ride to airport',
        type: 'EXPENSE',
        category: 'Transport',
        categoryId: '7ba7b810-9dad-41d1-80b4-00c04fd430c8',
        matchedKeyword: 'uber',
      },
    },
  })
  @ApiBadRequestResponse({ description: 'The description or transaction type failed validation.' })
  @ApiBadGatewayResponse({ description: 'FastAPI rejected or failed the categorization request.' })
  @ApiServiceUnavailableResponse({ description: 'FastAPI is unavailable.' })
  @ApiUnauthorizedResponse({ description: 'A valid Bearer access token is required.' })
  categorize(@CurrentUser() user: AuthenticatedUser, @Body() body: CategorizeDto) {
    return this.ai.categorizeTransaction({
      description: body.description,
      type: body.type ?? 'EXPENSE',
      userId: user.id,
    });
  }
}
