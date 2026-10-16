import {
  BadRequestException,
  ConflictException,
  Injectable,
  UnauthorizedException,
} from '@nestjs/common';
import { Prisma } from '@prisma/client';
import { PrismaService } from '../prisma/prisma.service';
import { UpdateUserDto } from './dto/update-user.dto';

@Injectable()
export class UsersService {
  constructor(private readonly prisma: PrismaService) {}

  async getMe(userId: string) {
    const user = await this.prisma.user.findUnique({
      where: { id: userId },
      select: { id: true, name: true, email: true, createdAt: true },
    });
    if (!user) {
      throw new UnauthorizedException('User account is no longer available');
    }
    return user;
  }

  async updateMe(userId: string, input: UpdateUserDto) {
    const data: Prisma.UserUpdateInput = {};
    if (input.name !== undefined) {
      const name = input.name.trim();
      if (!name) {
        throw new BadRequestException('Name must not be empty');
      }
      data.name = name;
    }
    if (input.email !== undefined) {
      data.email = input.email.trim().toLowerCase();
    }
    if (Object.keys(data).length === 0) {
      throw new BadRequestException('Provide a name or email to update');
    }

    try {
      return await this.prisma.user.update({
        where: { id: userId },
        data,
        select: { id: true, name: true, email: true, createdAt: true },
      });
    } catch (error) {
      if (error instanceof Prisma.PrismaClientKnownRequestError) {
        if (error.code === 'P2002') {
          throw new ConflictException('An account with this email already exists');
        }
        if (error.code === 'P2025') {
          throw new UnauthorizedException('User account is no longer available');
        }
      }
      throw error;
    }
  }
}
