export interface Task {
    id: number;
    title: string;
    description?: string;
    status: TaskStatus;
    priority: TaskPriority;
    userId: number;
    createdAt: Date;
    updatedAt: Date;
    startDate?: Date;
    endDate?: Date;
    tags?: string[];
    metadata?: Record<string, any>;
}

export enum TaskStatus {
    DRAFT = 'DRAFT',
    IN_PROGRESS = 'IN_PROGRESS', 
    COMPLETED = 'COMPLETED',
    CANCELLED = 'CANCELLED'
}

export enum TaskPriority {
    LOW = 'LOW',
    MEDIUM = 'MEDIUM',
    HIGH = 'HIGH',
    URGENT = 'URGENT'
}

export interface TaskCreateDto {
    title: string;
    description?: string;
    status?: TaskStatus;
    priority?: TaskPriority;
    userId: number;
    startDate?: Date;
    endDate?: Date;
    tags?: string[];
    metadata?: Record<string, any>;
}

export interface TaskUpdateDto {
    title?: string;
    description?: string;
    status?: TaskStatus;
    priority?: TaskPriority;
    startDate?: Date;
    endDate?: Date;
    tags?: string[];
    metadata?: Record<string, any>;
}

export default Task;