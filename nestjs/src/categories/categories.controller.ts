import {
  Body,
  Controller,
  Delete,
  Get,
  Param,
  ParseUUIDPipe,
  Patch,
  Post,
  UseGuards,
} from '@nestjs/common';
import {
  ApiBadRequestResponse,
  ApiBearerAuth,
  ApiCreatedResponse,
  ApiUnauthorizedResponse,
  ApiNotFoundResponse,
  ApiOkResponse,
  ApiOperation,
  ApiParam,
  ApiTags,
} from '@nestjs/swagger';
import { AuthGuard } from '@nestjs/passport';
import { AuthenticatedUser, CurrentUser } from '../common/decorators/current-user.decorator';
import { CreateCategoryDto } from './dto/create-category.dto';
import { UpdateCategoryDto } from './dto/update-category.dto';
import { CategoriesService } from './categories.service';

@ApiTags('Categories')
@ApiBearerAuth()
@UseGuards(AuthGuard('jwt'))
@Controller('categories')
export class CategoriesController {
  constructor(private readonly categories: CategoriesService) {}

  @Post()
  @ApiOperation({ summary: 'Create a custom category' })
  @ApiCreatedResponse({
    description: 'The created category.',
    schema: {
      example: {
        id: '6ba7b810-9dad-41d1-80b4-00c04fd430c8',
        name: 'Groceries',
        type: 'EXPENSE',
      },
    },
  })
  @ApiBadRequestResponse({ description: 'The category name or type is invalid.' })
  @ApiUnauthorizedResponse({ description: 'A valid Bearer access token is required.' })
  create(@CurrentUser() user: AuthenticatedUser, @Body() body: CreateCategoryDto) {
    return this.categories.create(user.id, body);
  }

  @Patch(':id')
  @ApiOperation({ summary: 'Update one of your custom categories' })
  @ApiParam({
    name: 'id',
    description: 'UUID of your custom category; copy it from GET /categories.',
    example: '6ba7b810-9dad-41d1-80b4-00c04fd430c8',
  })
  @ApiOkResponse({
    description: 'The updated category.',
    schema: {
      example: {
        id: '6ba7b810-9dad-41d1-80b4-00c04fd430c8',
        name: 'Food and groceries',
        type: 'EXPENSE',
      },
    },
  })
  @ApiBadRequestResponse({
    description: 'The update is invalid, empty, or would make existing transactions or budgets incompatible.',
  })
  @ApiNotFoundResponse({ description: 'The custom category does not exist or does not belong to you.' })
  @ApiUnauthorizedResponse({ description: 'A valid Bearer access token is required.' })
  update(
    @CurrentUser() user: AuthenticatedUser,
    @Param('id', ParseUUIDPipe) id: string,
    @Body() body: UpdateCategoryDto,
  ) {
    return this.categories.update(user.id, id, body);
  }

  @Delete(':id')
  @ApiOperation({ summary: 'Delete one of your custom categories' })
  @ApiParam({
    name: 'id',
    description: 'UUID of your custom category; copy it from GET /categories.',
    example: '6ba7b810-9dad-41d1-80b4-00c04fd430c8',
  })
  @ApiOkResponse({
    description: 'Confirmation that the category was deleted.',
    schema: { example: { deleted: true } },
  })
  @ApiBadRequestResponse({ description: 'The category is still used by transactions or budgets.' })
  @ApiNotFoundResponse({ description: 'The custom category does not exist or does not belong to you.' })
  @ApiUnauthorizedResponse({ description: 'A valid Bearer access token is required.' })
  remove(@CurrentUser() user: AuthenticatedUser, @Param('id', ParseUUIDPipe) id: string) {
    return this.categories.remove(user.id, id);
  }

  @Get()
  @ApiOperation({ summary: 'List system and your custom categories' })
  @ApiOkResponse({
    description: 'Available system and personal categories.',
    schema: {
      example: [
        { id: '6ba7b810-9dad-41d1-80b4-00c04fd430c8', name: 'Groceries', type: 'EXPENSE' },
        { id: '7ba7b810-9dad-41d1-80b4-00c04fd430c8', name: 'Salary', type: 'INCOME' },
      ],
    },
  })
  @ApiUnauthorizedResponse({ description: 'A valid Bearer access token is required.' })
  list(@CurrentUser() user: AuthenticatedUser) {
    return this.categories.list(user.id);
  }
}
