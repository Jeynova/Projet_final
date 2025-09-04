// Complete implementation with imports, functions, exports
import { Module } from '@nestjs/common';
import { AppController } from './app.controller';
import { AppService } from './app.service';
@Module(
  {
    imports: [MongooseModule.forRoot('mongodb://localhost/blog'),
      DatabaseModule,
    ],
    controllers: [AppController],
    providers: [AppService],
  },
)
export class AppModule {}
