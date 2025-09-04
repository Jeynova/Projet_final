export interface Category {
    id: number;
    title: string;
    description?: string;
    status: CategoryStatus;
    priority: CategoryPriority;
    userId: number;
    createdAt: Date;
    updatedAt: Date;
    startDate?: Date;
    endDate?: Date;
    tags?: string[];
    metadata?: Record<string, any>;
}

export enum CategoryStatus {
    DRAFT = 'DRAFT',
    IN_PROGRESS = 'IN_PROGRESS', 
    COMPLETED = 'COMPLETED',
    CANCELLED = 'CANCELLED'
}

export enum CategoryPriority {
    LOW = 'LOW',
    MEDIUM = 'MEDIUM',
    HIGH = 'HIGH',
    URGENT = 'URGENT'
}

export interface CategoryCreateDto {
    title: string;
    description?: string;
    status?: CategoryStatus;
    priority?: CategoryPriority;
    userId: number;
    startDate?: Date;
    endDate?: Date;
    tags?: string[];
    metadata?: Record<string, any>;
}

export interface CategoryUpdateDto {
    title?: string;
    description?: string;
    status?: CategoryStatus;
    priority?: CategoryPriority;
    startDate?: Date;
    endDate?: Date;
    tags?: string[];
    metadata?: Record<string, any>;
}

export default Category;