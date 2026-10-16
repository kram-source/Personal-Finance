import { HttpService } from '@nestjs/axios';
import {
  BadGatewayException,
  Injectable,
  Logger,
  NotFoundException,
  ServiceUnavailableException,
} from '@nestjs/common';
import { AxiosError, AxiosResponse } from 'axios';
import { firstValueFrom, Observable } from 'rxjs';

interface CategorizeInput {
  description: string;
  type: 'EXPENSE' | 'INCOME';
  userId: string;
}

@Injectable()
export class AiService {
  private readonly logger = new Logger(AiService.name);

  constructor(private readonly http: HttpService) {}

  categorizeTransaction(input: CategorizeInput) {
    return this.request(
      this.http.post('/ai/categorize-transaction', input),
    );
  }

  detectAnomaly(userId: string, multiplier = 2) {
    return this.request(
      this.http.post('/ai/detect-anomaly', { userId, multiplier }),
    );
  }

  predictSpending(userId: string, months = 3, asOf?: string) {
    return this.request(
      this.http.post('/ai/predict-spending', { userId, months, asOf }),
    );
  }

  private async request<T>(response: Observable<AxiosResponse<T>>): Promise<T> {
    try {
      return (await firstValueFrom(response)).data;
    } catch (error) {
      if (error instanceof AxiosError) {
        const requestContext = {
          url: error.config?.url,
          method: error.config?.method,
        };

        if (error.response) {
          const status = error.response.status;
          this.logger.error(
            'FastAPI returned an error response',
            JSON.stringify({ ...requestContext, status }),
          );

          if (status === 404) {
            throw new NotFoundException(
              'FastAPI could not find the requested user',
            );
          }
          if (status === 401 || status === 403) {
            throw new ServiceUnavailableException(
              'FastAPI integration authentication failed. Check the internal API key.',
            );
          }
          if (status === 400 || status === 422) {
            throw new BadGatewayException(
              'FastAPI rejected the analytics request.',
            );
          }
          throw new BadGatewayException(
            `FastAPI returned HTTP ${status}`,
          );
        }

        this.logger.error(
          'FastAPI connection failed',
          JSON.stringify({
            ...requestContext,
            code: error.code,
            message: error.message,
          }),
        );
        throw new ServiceUnavailableException('FastAPI service is unavailable');
      }
      throw error;
    }
  }
}
