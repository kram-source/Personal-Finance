import { ConflictException, Injectable, UnauthorizedException } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { compare, hash } from 'bcryptjs';
import { Prisma } from '@prisma/client';
import { PrismaService } from '../prisma/prisma.service';
import { LoginDto } from './dto/login.dto';
import { RegisterDto } from './dto/register.dto';

@Injectable()
export class AuthService {
  constructor(
    private readonly prisma: PrismaService,
    private readonly jwt: JwtService,
  ) {}

  async register(input: RegisterDto) {
    const email = input.email.trim().toLowerCase();
    const password = await hash(input.password, 12);

    try {
      const user = await this.prisma.user.create({
        data: { name: input.name.trim(), email, password },
        select: { id: true, name: true, email: true, createdAt: true },
      });
      return { user, accessToken: await this.tokenFor(user.id, user.email) };
    } catch (error) {
      if (
        error instanceof Prisma.PrismaClientKnownRequestError &&
        error.code === 'P2002'
      ) {
        throw new ConflictException('An account with this email already exists');
      }
      throw error;
    }
  }

  async login(input: LoginDto) {
    const user = await this.prisma.user.findUnique({
      where: { email: input.email.trim().toLowerCase() },
    });
    if (!user || !(await compare(input.password, user.password))) {
      throw new UnauthorizedException('Invalid email or password');
    }
    return {
      user: { id: user.id, name: user.name, email: user.email },
      accessToken: await this.tokenFor(user.id, user.email),
    };
  }

  private tokenFor(id: string, email: string): Promise<string> {
    return this.jwt.signAsync({ sub: id, email });
  }
}
