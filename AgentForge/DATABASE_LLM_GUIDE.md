#!/usr/bin/env python3
"""
DatabaseAgent LLM vs Fallback Trigger Guide
============================================

This guide shows you EXACTLY when the LLM is called vs when fallback happens
"""

## 🤖 WHEN LLM IS CALLED:

### ✅ DatabaseAgent ALWAYS tries LLM first with this prompt:
```
Analyze this project request and design an appropriate database schema: "{prompt}"

Tech stack: {names}
Database: {db}
{rag_context}

CRITICAL ANALYSIS REQUIRED:
1. What type of project is this? (blog, ecommerce, social, task management, etc.)
2. What are the core entities that ACTUALLY make sense for THIS specific project?
3. Don't default to generic User/Product - think about what THIS project really needs!

Examples of project-specific entities:
- Blog: User, Post, Comment, Category, Tag
- Task Manager: User, Project, Task, TaskStatus, Team
- Social Platform: User, Post, Like, Follow, Message
- Learning Platform: User, Course, Lesson, Enrollment, Progress
- Inventory System: Item, Warehouse, Stock, Supplier, Order
- Restaurant: Menu, Item, Order, Table, Customer
- Library: Book, Author, Member, Loan, Reservation

ONLY create tables that make sense for the actual project described!

Return JSON:
{
    "schema_sql": "Complete CREATE TABLE statements with proper constraints, indexes, and relationships",
    "models": ["EntityName1", "EntityName2", ...],
    "relationships": ["Entity1 has many Entity2", "Entity2 belongs to Entity1", ...],
    "reasoning": "Why these specific entities were chosen for this project type"
}

Generate project-appropriate database design, not generic templates!
```

### 🛡️ WHEN FALLBACK HAPPENS:

The LLM is called but returns None/empty, so intelligent fallback analyzes your prompt:

**Fallback Project Type Detection:**
- **Blog keywords**: 'blog', 'cms', 'content', 'article', 'post' → User, Post, Comment, Category
- **Task keywords**: 'task', 'todo', 'project', 'manage' → User, Project, Task, TaskStatus  
- **E-commerce keywords**: 'ecommerce', 'shop', 'store', 'cart', 'product' → User, Product, Category, Order, OrderItem, Cart
- **Social keywords**: 'social', 'follow', 'like', 'friend' → User, Post, Like, Follow, Message
- **Learning keywords**: 'course', 'lesson', 'learn', 'education' → User, Course, Lesson, Enrollment, Progress

## 🎯 HOW TO TRIGGER LLM SUCCESS IN UI:

### ✅ Use these SPECIFIC prompts to get LLM database design:

1. **Advanced E-commerce**: 
   "Create a comprehensive e-commerce platform with product variants, inventory tracking across multiple warehouses, customer loyalty programs, promotional campaigns, order fulfillment workflows, supplier management, and financial reporting. Need PostgreSQL with advanced indexing."

2. **Complex Task Management**:
   "Build a collaborative project management system with team workspaces, project hierarchies, task dependencies, time tracking, milestone management, reporting dashboards, and custom workflows. Use PostgreSQL with full-text search."

3. **Learning Management System**:
   "Create an online learning platform with structured courses, interactive lessons, quizzes with multiple question types, student progress tracking, certificates, instructor management, and analytics. Need MySQL with performance optimization."

4. **Inventory Management**:
   "Build an inventory management system with suppliers, warehouses, products with variants and bundles, stock tracking with batch numbers, purchase orders with approval workflows, sales orders, and reporting. Use PostgreSQL with audit trails."

5. **Social Media Platform**:
   "Create a social media platform with user profiles, posts with media attachments, comments and replies, likes and reactions, follow/follower relationships, direct messaging, notifications, and content moderation. Need PostgreSQL with real-time features."

### 🔧 Technical Requirements That Trigger LLM:
- Mention specific database features: "with indexing", "audit trails", "full-text search"
- List custom entities: "need ProductVariant, StockMovement, LoyaltyProgram tables"  
- Describe complex relationships: "hierarchical projects", "many-to-many relationships"
- Specify database technology: "PostgreSQL", "MySQL", "MongoDB"

### ⚠️ Simple Prompts That Use Fallback:
- "Create a blog" (too simple, fallback: User, Post, Comment, Category)
- "Build a shop" (too simple, fallback: User, Product, Order, Cart)
- "Make a task app" (too simple, fallback: User, Task, Project)

## 🚀 TO TEST IN UI:

1. **Start Flask UI v2**
2. **Use one of the complex prompts above**
3. **Watch the terminal output** for:
   - `🤖 Calling LLM for...` followed by `✅ LLM response:` with actual content (LLM SUCCESS)
   - `🤖 Calling LLM for...` followed by `⚠️ LLM returned empty, using fallback` (FALLBACK)

The more detailed and complex your requirements, the better the LLM will perform!
