"""
Tasks API Routes
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import or_, and_
from datetime import datetime

from db.database import get_db
from models.database import Task, TaskStatus, TaskPriority, TaskComment, Tag, User
from auth.auth import get_current_active_user

router = APIRouter(prefix="/tasks", tags=["tasks"])


class TaskCreate:
    from pydantic import BaseModel, Field
    
    class TaskCreate(BaseModel):
        title: str
        description: str
        assigned_to: Optional[str] = None
        project_id: Optional[str] = None
        team_id: Optional[str] = None
        status: TaskStatus = TaskStatus.CREATED
        priority: TaskPriority = TaskPriority.MEDIUM
        type: str
        requires_validation: bool = False
        success_criteria: Dict[str, Any] = {}
        max_iterations: int = 5
        progress: int = 0
        due_date: Optional[datetime] = None
        time_estimate: Optional[float] = None
        tags: List[str] = []


class TaskUpdate:
    from pydantic import BaseModel
    
    class TaskUpdate(BaseModel):
        title: Optional[str] = None
        description: Optional[str] = None
        assigned_to: Optional[str] = None
        project_id: Optional[str] = None
        team_id: Optional[str] = None
        status: Optional[TaskStatus] = None
        priority: Optional[TaskPriority] = None
        requires_validation: Optional[bool] = None
        success_criteria: Optional[Dict[str, Any]] = None
        max_iterations: Optional[int] = None
        progress: Optional[int] = None
        due_date: Optional[datetime] = None
        time_estimate: Optional[float] = None
        tags: Optional[List[str]] = None


class TaskResponse:
    from pydantic import BaseModel
    
    class TaskResponse(BaseModel):
        id: str
        title: str
        description: str
        assigned_to: Optional[str] = None
        assignee_name: Optional[str] = None
        assignee_type: Optional[str] = None
        project_id: Optional[str] = None
        team_id: Optional[str] = None
        status: str
        priority: str
        type: str
        requires_validation: bool
        success_criteria: Dict[str, Any] = {}
        max_iterations: int
        iterations: int
        progress: int
        due_date: Optional[datetime] = None
        time_estimate: Optional[float] = None
        tags: List[str] = []
        created_by: str
        created_at: datetime
        updated_at: datetime
        
        class Config:
            orm_mode = True


class CommentCreate:
    from pydantic import BaseModel
    
    class CommentCreate(BaseModel):
        content: str


class CommentResponse:
    from pydantic import BaseModel
    
    class CommentResponse(BaseModel):
        id: str
        task_id: str
        author_id: str
        author_name: str
        author_type: str
        content: str
        created_at: datetime
        updated_at: datetime
        
        class Config:
            orm_mode = True


@router.post("", response_model=TaskResponse.TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task: TaskCreate.TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new task
    """
    # Create the task
    db_task = Task(
        title=task.title,
        description=task.description,
        assigned_to=task.assigned_to,
        project_id=task.project_id,
        team_id=task.team_id,
        status=task.status,
        priority=task.priority,
        type=task.type,
        requires_validation=task.requires_validation,
        success_criteria=task.success_criteria,
        max_iterations=task.max_iterations,
        progress=task.progress,
        due_date=task.due_date,
        time_estimate=task.time_estimate,
        created_by=current_user.id
    )
    
    # Add tags to the task
    if task.tags:
        for tag_name in task.tags:
            # Check if tag exists
            query = select(Tag).where(Tag.name == tag_name)
            result = await db.execute(query)
            tag = result.scalars().first()
            
            # Create tag if it doesn't exist
            if not tag:
                tag = Tag(name=tag_name)
                db.add(tag)
                await db.flush()
            
            db_task.tags.append(tag)
    
    db.add(db_task)
    await db.commit()
    await db.refresh(db_task)
    
    # Get assignee info if assigned
    assignee_name = None
    assignee_type = None
    if db_task.assigned_to:
        query = select(User).where(User.id == db_task.assigned_to)
        result = await db.execute(query)
        assignee = result.scalars().first()
        if assignee:
            assignee_name = assignee.username
            assignee_type = assignee.user_type
    
    # Get tag names
    tag_names = [tag.name for tag in db_task.tags]
    
    return {
        "id": db_task.id,
        "title": db_task.title,
        "description": db_task.description,
        "assigned_to": db_task.assigned_to,
        "assignee_name": assignee_name,
        "assignee_type": assignee_type,
        "project_id": db_task.project_id,
        "team_id": db_task.team_id,
        "status": db_task.status,
        "priority": db_task.priority,
        "type": db_task.type,
        "requires_validation": db_task.requires_validation,
        "success_criteria": db_task.success_criteria,
        "max_iterations": db_task.max_iterations,
        "iterations": db_task.iterations,
        "progress": db_task.progress,
        "due_date": db_task.due_date,
        "time_estimate": db_task.time_estimate,
        "tags": tag_names,
        "created_by": db_task.created_by,
        "created_at": db_task.created_at,
        "updated_at": db_task.updated_at
    }


@router.get("", response_model=List[TaskResponse.TaskResponse])
async def list_tasks(
    team_id: Optional[str] = None,
    project_id: Optional[str] = None,
    status: Optional[TaskStatus] = None,
    assigned_to: Optional[str] = None,
    priority: Optional[TaskPriority] = None,
    tag: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    List tasks with optional filtering
    """
    # Build query with filters
    query = select(Task)
    
    # Apply filters
    filters = []
    if team_id:
        filters.append(Task.team_id == team_id)
    if project_id:
        filters.append(Task.project_id == project_id)
    if status:
        filters.append(Task.status == status)
    if assigned_to:
        filters.append(Task.assigned_to == assigned_to)
    if priority:
        filters.append(Task.priority == priority)
    
    # Apply tag filter if provided
    if tag:
        # Join with Tag model to filter by tag name
        # This would typically be done with a join, but for simplicity
        # we'll load all tasks and filter in memory
        query = query.filter(filters)
        result = await db.execute(query)
        tasks = result.scalars().all()
        
        # Filter tasks by tag
        tasks = [task for task in tasks if any(t.name == tag for t in task.tags)]
    else:
        # Apply all filters directly to query
        if filters:
            query = query.filter(and_(*filters))
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute query
        result = await db.execute(query)
        tasks = result.scalars().all()
    
    # Build response with additional info for each task
    task_responses = []
    for task in tasks:
        # Get assignee info if assigned
        assignee_name = None
        assignee_type = None
        if task.assigned_to:
            query = select(User).where(User.id == task.assigned_to)
            result = await db.execute(query)
            assignee = result.scalars().first()
            if assignee:
                assignee_name = assignee.username
                assignee_type = assignee.user_type
        
        # Get tag names
        tag_names = [tag.name for tag in task.tags]
        
        task_responses.append({
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "assigned_to": task.assigned_to,
            "assignee_name": assignee_name,
            "assignee_type": assignee_type,
            "project_id": task.project_id,
            "team_id": task.team_id,
            "status": task.status,
            "priority": task.priority,
            "type": task.type,
            "requires_validation": task.requires_validation,
            "success_criteria": task.success_criteria,
            "max_iterations": task.max_iterations,
            "iterations": task.iterations,
            "progress": task.progress,
            "due_date": task.due_date,
            "time_estimate": task.time_estimate,
            "tags": tag_names,
            "created_by": task.created_by,
            "created_at": task.created_at,
            "updated_at": task.updated_at
        })
    
    return task_responses


@router.get("/{task_id}", response_model=TaskResponse.TaskResponse)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get task details by ID
    """
    query = select(Task).where(Task.id == task_id)
    result = await db.execute(query)
    task = result.scalars().first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Get assignee info if assigned
    assignee_name = None
    assignee_type = None
    if task.assigned_to:
        query = select(User).where(User.id == task.assigned_to)
        result = await db.execute(query)
        assignee = result.scalars().first()
        if assignee:
            assignee_name = assignee.username
            assignee_type = assignee.user_type
    
    # Get tag names
    tag_names = [tag.name for tag in task.tags]
    
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "assigned_to": task.assigned_to,
        "assignee_name": assignee_name,
        "assignee_type": assignee_type,
        "project_id": task.project_id,
        "team_id": task.team_id,
        "status": task.status,
        "priority": task.priority,
        "type": task.type,
        "requires_validation": task.requires_validation,
        "success_criteria": task.success_criteria,
        "max_iterations": task.max_iterations,
        "iterations": task.iterations,
        "progress": task.progress,
        "due_date": task.due_date,
        "time_estimate": task.time_estimate,
        "tags": tag_names,
        "created_by": task.created_by,
        "created_at": task.created_at,
        "updated_at": task.updated_at
    }


@router.put("/{task_id}", response_model=TaskResponse.TaskResponse)
async def update_task(
    task_id: str,
    task_update: TaskUpdate.TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a task
    """
    query = select(Task).where(Task.id == task_id)
    result = await db.execute(query)
    task = result.scalars().first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update task fields
    update_data = task_update.dict(exclude_unset=True)
    
    # Handle tags separately
    tags = update_data.pop("tags", None)
    
    # Update the task fields
    for key, value in update_data.items():
        setattr(task, key, value)
    
    # Update tags if provided
    if tags is not None:
        # Remove existing tags
        task.tags = []
        
        # Add new tags
        for tag_name in tags:
            # Check if tag exists
            query = select(Tag).where(Tag.name == tag_name)
            result = await db.execute(query)
            tag = result.scalars().first()
            
            # Create tag if it doesn't exist
            if not tag:
                tag = Tag(name=tag_name)
                db.add(tag)
                await db.flush()
            
            task.tags.append(tag)
    
    await db.commit()
    await db.refresh(task)
    
    # Get assignee info if assigned
    assignee_name = None
    assignee_type = None
    if task.assigned_to:
        query = select(User).where(User.id == task.assigned_to)
        result = await db.execute(query)
        assignee = result.scalars().first()
        if assignee:
            assignee_name = assignee.username
            assignee_type = assignee.user_type
    
    # Get tag names
    tag_names = [tag.name for tag in task.tags]
    
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "assigned_to": task.assigned_to,
        "assignee_name": assignee_name,
        "assignee_type": assignee_type,
        "project_id": task.project_id,
        "team_id": task.team_id,
        "status": task.status,
        "priority": task.priority,
        "type": task.type,
        "requires_validation": task.requires_validation,
        "success_criteria": task.success_criteria,
        "max_iterations": task.max_iterations,
        "iterations": task.iterations,
        "progress": task.progress,
        "due_date": task.due_date,
        "time_estimate": task.time_estimate,
        "tags": tag_names,
        "created_by": task.created_by,
        "created_at": task.created_at,
        "updated_at": task.updated_at
    }


@router.put("/{task_id}/status", response_model=TaskResponse.TaskResponse)
async def update_task_status(
    task_id: str,
    status: TaskStatus,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update the status of a task
    """
    query = select(Task).where(Task.id == task_id)
    result = await db.execute(query)
    task = result.scalars().first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Update task status
    task.status = status
    
    # If status is COMPLETED, set progress to 100%
    if status == TaskStatus.COMPLETED:
        task.progress = 100
    
    await db.commit()
    await db.refresh(task)
    
    # Get assignee info if assigned
    assignee_name = None
    assignee_type = None
    if task.assigned_to:
        query = select(User).where(User.id == task.assigned_to)
        result = await db.execute(query)
        assignee = result.scalars().first()
        if assignee:
            assignee_name = assignee.username
            assignee_type = assignee.user_type
    
    # Get tag names
    tag_names = [tag.name for tag in task.tags]
    
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "assigned_to": task.assigned_to,
        "assignee_name": assignee_name,
        "assignee_type": assignee_type,
        "project_id": task.project_id,
        "team_id": task.team_id,
        "status": task.status,
        "priority": task.priority,
        "type": task.type,
        "requires_validation": task.requires_validation,
        "success_criteria": task.success_criteria,
        "max_iterations": task.max_iterations,
        "iterations": task.iterations,
        "progress": task.progress,
        "due_date": task.due_date,
        "time_estimate": task.time_estimate,
        "tags": tag_names,
        "created_by": task.created_by,
        "created_at": task.created_at,
        "updated_at": task.updated_at
    }


@router.post("/{task_id}/comments", response_model=CommentResponse.CommentResponse)
async def add_task_comment(
    task_id: str,
    comment: CommentCreate.CommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Add a comment to a task
    """
    query = select(Task).where(Task.id == task_id)
    result = await db.execute(query)
    task = result.scalars().first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Create comment
    db_comment = TaskComment(
        task_id=task_id,
        author_id=current_user.id,
        content=comment.content
    )
    
    # If task requires validation and user is not the assignee, consider this feedback
    if task.requires_validation and task.assigned_to != current_user.id:
        # Increment iterations
        task.iterations += 1
        
        # If max iterations reached, mark as failed
        if task.iterations >= task.max_iterations:
            task.status = TaskStatus.FAILED
        else:
            task.status = TaskStatus.REVISION_NEEDED
    
    db.add(db_comment)
    await db.commit()
    await db.refresh(db_comment)
    
    # Get author info
    query = select(User).where(User.id == db_comment.author_id)
    result = await db.execute(query)
    author = result.scalars().first()
    
    return {
        "id": db_comment.id,
        "task_id": db_comment.task_id,
        "author_id": db_comment.author_id,
        "author_name": author.username if author else "Unknown",
        "author_type": author.user_type if author else "unknown",
        "content": db_comment.content,
        "created_at": db_comment.created_at,
        "updated_at": db_comment.updated_at
    }


@router.get("/{task_id}/comments", response_model=List[CommentResponse.CommentResponse])
async def get_task_comments(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get comments for a task
    """
    query = select(Task).where(Task.id == task_id)
    result = await db.execute(query)
    task = result.scalars().first()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Get comments
    query = select(TaskComment).where(TaskComment.task_id == task_id)
    result = await db.execute(query)
    comments = result.scalars().all()
    
    # Build response
    comment_responses = []
    for comment in comments:
        # Get author info
        query = select(User).where(User.id == comment.author_id)
        result = await db.execute(query)
        author = result.scalars().first()
        
        comment_responses.append({
            "id": comment.id,
            "task_id": comment.task_id,
            "author_id": comment.author_id,
            "author_name": author.username if author else "Unknown",
            "author_type": author.user_type if author else "unknown",
            "content": comment.content,
            "created_at": comment.created_at,
            "updated_at": comment.updated_at
        })
    
    return comment_responses 