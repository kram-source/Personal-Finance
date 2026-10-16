import { Logger, ValidationPipe } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import { NestFactory } from '@nestjs/core';
import { NestExpressApplication } from '@nestjs/platform-express';
import { DocumentBuilder, SwaggerModule } from '@nestjs/swagger';
import { join } from 'node:path';
import { AppModule } from './app.module';

async function bootstrap(): Promise<void> {
  const app = await NestFactory.create<NestExpressApplication>(AppModule);
  app.useStaticAssets(join(__dirname, 'public'));
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      forbidNonWhitelisted: true,
      transform: true,
    }),
  );

  const swaggerConfig = new DocumentBuilder()
    .setTitle('Personal Finance API')
    .setDescription('Finance management API with FastAPI-powered analytics.')
    .setVersion('1.0')
    .addBearerAuth()
    .addTag('Authentication')
    .addTag('Users')
    .addTag('Categories')
    .addTag('Transactions')
    .addTag('Budgets')
    .addTag('Reports')
    .addTag('AI')
    .build();
  SwaggerModule.setup('docs', app, SwaggerModule.createDocument(app, swaggerConfig), {
    customCss: `
      .swagger-ui .topbar { display: none; }
      .swagger-ui .responses-wrapper > .opblock-section-header h4 {
        font-size: 0;
      }
      .swagger-ui .responses-wrapper > .opblock-section-header h4::after {
        content: "Example responses";
        font-size: 14px;
      }
      .swagger-ui table.live-responses-table {
        background: rgba(0, 0, 0, 0.18);
        border: 1px solid #6b8790;
        border-radius: 4px;
        margin-bottom: 32px;
        outline: 1px solid rgba(107, 135, 144, 0.35);
        outline-offset: 4px;
      }
      .swagger-ui .responses-wrapper {
        border: 1px solid #3b6570;
        border-top: 3px solid #3b9ca7;
        border-radius: 4px;
        margin-top: 24px;
        padding: 12px;
      }
    `,
  });

  const config = app.get(ConfigService);
  const port = Number(config.get<string>('PORT') ?? '3000');
  if (!Number.isInteger(port) || port < 1 || port > 65535) {
    throw new Error('PORT must be an integer between 1 and 65535');
  }
  await app.listen(port);
  Logger.log(`Swagger UI available at http://localhost:${port}/docs`, 'Bootstrap');
}

void bootstrap();
