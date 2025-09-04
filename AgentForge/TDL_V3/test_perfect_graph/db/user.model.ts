export interface User {
    id: number;
    title: string;
    description?: string;
    status: UserStatus;
    priority: UserPriority;
    userId: number;
    createdAt: Date;
    updatedAt: Date;
    startDate?: Date;
    endDate?: Date;
    tags?: string[];
    metadata?: Record<string, any>;
}

export enum UserStatus {
    DRAFT = 'DRAFT',
    IN_PROGRESS = 'IN_PROGRESS', 
    COMPLETED = 'COMPLETED',
    CANCELLED = 'CANCELLED'
}

export enum UserPriority {
    LOW = 'LOW',
    MEDIUM = 'MEDIUM',
    HIGH = 'HIGH',
    URGENT = 'URGENT'
}

export interface UserCreateDto {
    title: string;
    description?: string;
    status?: UserStatus;
    priority?: UserPriority;
    userId: number;
    startDate?: Date;
    endDate?: Date;
    tags?: string[];
    metadata?: Record<string, any>;
}

export interface UserUpdateDto {
    title?: string;
    description?: string;
    status?: UserStatus;
    priority?: UserPriority;
    startDate?: Date;
    endDate?: Date;
    tags?: string[];
    metadata?: Record<string, any>;
}

export default User;