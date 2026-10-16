import {
  BadRequestException,
  Body,
  Controller,
  Delete,
  Get,
  Header,
  Param,
  ParseUUIDPipe,
  Patch,
  Post,
  Query,
  UploadedFile,
  UseGuards,
  UseInterceptors,
} from '@nestjs/common';
import {
  ApiBadGatewayResponse,
  ApiBadRequestResponse,
  ApiBearerAuth,
  ApiBody,
  ApiConsumes,
  ApiCreatedResponse,
  ApiNotFoundResponse,
  ApiOkResponse,
  ApiOperation,
  ApiParam,
  ApiServiceUnavailableResponse,
  ApiTags,
  ApiUnauthorizedResponse,
} from '@nestjs/swagger';
import { AuthGuard } from '@nestjs/passport';
import { FileInterceptor } from '@nestjs/platform-express';
import { AuthenticatedUser, CurrentUser } from '../common/decorators/current-user.decorator';
import { CreateTransactionDto } from './dto/create-transaction.dto';
import { ListTransactionsDto } from './dto/list-transactions.dto';
import { UpdateTransactionDto } from './dto/update-transaction.dto';
import { TransactionsService } from './transactions.service';

@ApiTags('Transactions')
@ApiBearerAuth()
@UseGuards(AuthGuard('jwt'))
@Controller('transactions')
export class TransactionsController {
  constructor(private readonly transactions: TransactionsService) {}

  @Get('import/template')
  @Header('Content-Type', 'text/csv; charset=utf-8')
  @Header('Content-Disposition', 'attachment; filename="transactions-template.csv"')
  @ApiOperation({ summary: 'Download a CSV template for importing transactions' })
  @ApiOkResponse({
    description: 'CSV template. Date, description, amount, and type are required; category is optional.',
    schema: {
      type: 'string',
      example:
        'date,description,amount,type,category\n2026-10-12,Supermarket purchase,85.40,EXPENSE,Food\n2026-10-13,Monthly salary,4200.00,INCOME,',
    },
  })
  @ApiUnauthorizedResponse({ description: 'A valid bearer token is required.' })
  downloadImportTemplate(): string {
    return [
      'date,description,amount,type,category',
      '2026-10-12,Supermarket purchase,85.40,EXPENSE,Food',
      '2026-10-13,Monthly salary,4200.00,INCOME,',
      '',
    ].join('\n');
  }

  @Post('import')
  @UseInterceptors(FileInterceptor('file', { limits: { fileSize: 5 * 1024 * 1024 } }))
  @ApiConsumes('multipart/form-data')
  @ApiBody({
    schema: {
      type: 'object',
      required: ['file'],
      properties: { file: { type: 'string', format: 'binary' } },
    },
  })
  @ApiOperation({
    summary: 'Import transactions from a CSV file',
    description:
      'Upload a CSV using the downloadable template. Required columns are date, description, amount, and type; category is optional. The complete file is validated before any transactions are saved.',
  })
  @ApiCreatedResponse({
    description: 'All valid CSV rows were imported.',
    schema: { example: { imported: 2 } },
  })
  @ApiBadRequestResponse({
    description: 'The file is missing, too large, malformed, or contains invalid columns or rows. No rows are imported.',
  })
  @ApiBadGatewayResponse({ description: 'FastAPI rejected or failed category suggestions.' })
  @ApiServiceUnavailableResponse({ description: 'FastAPI is unavailable while suggesting categories.' })
  @ApiUnauthorizedResponse({ description: 'A valid bearer token is required.' })
  importCsv(
    @CurrentUser() user: AuthenticatedUser,
    @UploadedFile()
    file?: { originalname: string; buffer: Buffer },
  ) {
    if (!file) {
      throw new BadRequestException('Upload a CSV file in the "file" field');
    }
    if (!file.originalname.toLowerCase().endsWith('.csv')) {
      throw new BadRequestException('The uploaded file must have a .csv extension');
    }
    return this.transactions.importCsv(user.id, file.buffer);
  }

  @Post()
  @ApiOperation({ summary: 'Create a transaction' })
  @ApiCreatedResponse({
    description: 'The created transaction, including its category.',
    schema: {
      example: {
        id: '8ba7b810-9dad-41d1-80b4-00c04fd430c8',
        userId: '550e8400-e29b-41d4-a716-446655440000',
        amount: '42.50',
        type: 'EXPENSE',
        description: 'Groceries',
        date: '2026-10-08T00:00:00.000Z',
        categoryId: '6ba7b810-9dad-41d1-80b4-00c04fd430c8',
        source: 'NestJS',
        createdAt: '2026-10-09T04:30:00.000Z',
        updatedAt: '2026-10-09T04:30:00.000Z',
        category: {
          id: '6ba7b810-9dad-41d1-80b4-00c04fd430c8',
          name: 'Groceries',
          type: 'EXPENSE',
        },
      },
    },
  })
  @ApiBadRequestResponse({
    description: 'The transaction fields or category are invalid, or no category suggestion was available.',
  })
  @ApiBadGatewayResponse({ description: 'FastAPI rejected or failed the categorization request.' })
  @ApiServiceUnavailableResponse({ description: 'FastAPI is unavailable while suggesting a category.' })
  @ApiUnauthorizedResponse({ description: 'A valid Bearer access token is required.' })
  create(@CurrentUser() user: AuthenticatedUser, @Body() body: CreateTransactionDto) {
    return this.transactions.create(user.id, body);
  }

  @Get()
  @ApiOperation({ summary: 'List your transactions with optional filters' })
  @ApiOkResponse({
    description: 'A page of transactions and pagination details.',
    schema: {
      example: {
        items: [
          {
            id: '8ba7b810-9dad-41d1-80b4-00c04fd430c8',
            userId: '550e8400-e29b-41d4-a716-446655440000',
            amount: '42.50',
            type: 'EXPENSE',
            description: 'Groceries',
            date: '2026-10-08T00:00:00.000Z',
            categoryId: '6ba7b810-9dad-41d1-80b4-00c04fd430c8',
            source: 'NestJS',
            createdAt: '2026-10-09T04:30:00.000Z',
            updatedAt: '2026-10-09T04:30:00.000Z',
            category: {
              id: '6ba7b810-9dad-41d1-80b4-00c04fd430c8',
              name: 'Groceries',
              type: 'EXPENSE',
            },
          },
        ],
        page: 1,
        limit: 20,
        total: 1,
      },
    },
  })
  @ApiBadRequestResponse({ description: 'One or more transaction filters are invalid.' })
  @ApiUnauthorizedResponse({ description: 'A valid Bearer access token is required.' })
  list(@CurrentUser() user: AuthenticatedUser, @Query() query: ListTransactionsDto) {
    return this.transactions.list(user.id, query);
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get one of your transactions by ID' })
  @ApiParam({
    name: 'id',
    description: 'UUID of your transaction; copy it from GET /transactions.',
    example: '8ba7b810-9dad-41d1-80b4-00c04fd430c8',
  })
  @ApiOkResponse({
    description: 'The requested transaction, including its category.',
    schema: {
      example: {
        id: '8ba7b810-9dad-41d1-80b4-00c04fd430c8',
        userId: '550e8400-e29b-41d4-a716-446655440000',
        amount: '42.50',
        type: 'EXPENSE',
        description: 'Groceries',
        date: '2026-10-08T00:00:00.000Z',
        categoryId: '6ba7b810-9dad-41d1-80b4-00c04fd430c8',
        source: 'NestJS',
        createdAt: '2026-10-09T04:30:00.000Z',
        updatedAt: '2026-10-09T04:30:00.000Z',
        category: {
          id: '6ba7b810-9dad-41d1-80b4-00c04fd430c8',
          name: 'Groceries',
          type: 'EXPENSE',
        },
      },
    },
  })
  @ApiBadRequestResponse({ description: 'The transaction ID must be a valid UUID.' })
  @ApiNotFoundResponse({ description: 'The transaction does not exist or does not belong to you.' })
  @ApiUnauthorizedResponse({ description: 'A valid Bearer access token is required.' })
  get(@CurrentUser() user: AuthenticatedUser, @Param('id', ParseUUIDPipe) id: string) {
    return this.transactions.get(user.id, id);
  }

  @Patch(':id')
  @ApiOperation({ summary: 'Update one of your transactions' })
  @ApiParam({
    name: 'id',
    description: 'UUID of your transaction; copy it from GET /transactions.',
    example: '8ba7b810-9dad-41d1-80b4-00c04fd430c8',
  })
  @ApiOkResponse({
    description: 'The updated transaction, including its category.',
    schema: {
      example: {
        id: '8ba7b810-9dad-41d1-80b4-00c04fd430c8',
        userId: '550e8400-e29b-41d4-a716-446655440000',
        amount: '45.00',
        type: 'EXPENSE',
        description: 'Weekly groceries',
        date: '2026-10-08T00:00:00.000Z',
        categoryId: '6ba7b810-9dad-41d1-80b4-00c04fd430c8',
        source: 'NestJS',
        createdAt: '2026-10-09T04:30:00.000Z',
        updatedAt: '2026-10-09T05:00:00.000Z',
        category: {
          id: '6ba7b810-9dad-41d1-80b4-00c04fd430c8',
          name: 'Groceries',
          type: 'EXPENSE',
        },
      },
    },
  })
  @ApiBadRequestResponse({
    description: 'The transaction ID, update fields, or category/type combination is invalid.',
  })
  @ApiNotFoundResponse({ description: 'The transaction does not exist or does not belong to you.' })
  @ApiUnauthorizedResponse({ description: 'A valid Bearer access token is required.' })
  update(
    @CurrentUser() user: AuthenticatedUser,
    @Param('id', ParseUUIDPipe) id: string,
    @Body() body: UpdateTransactionDto,
  ) {
    return this.transactions.update(user.id, id, body);
  }

  @Delete(':id')
  @ApiOperation({ summary: 'Delete one of your transactions' })
  @ApiParam({
    name: 'id',
    description: 'UUID of your transaction; copy it from GET /transactions.',
    example: '8ba7b810-9dad-41d1-80b4-00c04fd430c8',
  })
  @ApiOkResponse({
    description: 'Confirmation that the transaction was deleted.',
    schema: { example: { deleted: true } },
  })
  @ApiBadRequestResponse({ description: 'The transaction ID must be a valid UUID.' })
  @ApiNotFoundResponse({ description: 'The transaction does not exist or does not belong to you.' })
  @ApiUnauthorizedResponse({ description: 'A valid Bearer access token is required.' })
  remove(@CurrentUser() user: AuthenticatedUser, @Param('id', ParseUUIDPipe) id: string) {
    return this.transactions.remove(user.id, id);
  }
}
