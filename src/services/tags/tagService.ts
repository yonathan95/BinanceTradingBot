import { Tag, TaggedEntity, UserAccess, WorkspaceAccess, ProjectAccess, UserRole } from './types';

// Mock data storage - would be replaced with API calls in production
let tags: Tag[] = [];
let taggedEntities: TaggedEntity[] = [];
let userAccess: UserAccess[] = [];
let workspaceAccess: WorkspaceAccess[] = [];
let projectAccess: ProjectAccess[] = [];

// Initialize with some default data
const initializeTagService = () => {
  // Sample tags
  tags = [
    { id: 'tag-1', name: 'Frontend', color: '#4299E1', type: 'project' },
    { id: 'tag-2', name: 'Backend', color: '#48BB78', type: 'project' },
    { id: 'tag-3', name: 'DevOps', color: '#ED8936', type: 'project' },
    { id: 'tag-4', name: 'Design', color: '#9F7AEA', type: 'project' },
    { id: 'tag-5', name: 'Marketing', color: '#F56565', type: 'workspace' },
    { id: 'tag-6', name: 'Management', color: '#ECC94B', type: 'workspace' },
    { id: 'tag-7', name: 'Engineering', color: '#38B2AC', type: 'user' },
    { id: 'tag-8', name: 'Product', color: '#ED64A6', type: 'user' },
  ];

  // Would be loaded from a database in production
};

// Tag Management
export const getTags = (): Tag[] => {
  return tags;
};

export const getTagsByType = (type: 'workspace' | 'project' | 'user'): Tag[] => {
  return tags.filter(tag => tag.type === type);
};

export const createTag = (tag: Omit<Tag, 'id'>): Tag => {
  const newTag = { ...tag, id: `tag-${Date.now()}` };
  tags.push(newTag);
  return newTag;
};

export const updateTag = (id: string, tag: Partial<Omit<Tag, 'id'>>): Tag | null => {
  const index = tags.findIndex(t => t.id === id);
  if (index === -1) return null;
  
  tags[index] = { ...tags[index], ...tag };
  return tags[index];
};

export const deleteTag = (id: string): boolean => {
  const index = tags.findIndex(t => t.id === id);
  if (index === -1) return false;
  
  tags.splice(index, 1);
  return true;
};

// Entity Tag Management
export const getTaggedEntities = (): TaggedEntity[] => {
  return taggedEntities;
};

export const getEntityTags = (entityId: string): string[] => {
  const entity = taggedEntities.find(e => e.id === entityId);
  return entity ? entity.tags : [];
};

export const tagEntity = (entityId: string, entityName: string, entityType: 'workspace' | 'project', tagIds: string[]): TaggedEntity => {
  const existingIndex = taggedEntities.findIndex(e => e.id === entityId);
  
  if (existingIndex === -1) {
    const newEntity: TaggedEntity = {
      id: entityId,
      name: entityName,
      type: entityType,
      tags: tagIds
    };
    taggedEntities.push(newEntity);
    return newEntity;
  } else {
    taggedEntities[existingIndex].tags = tagIds;
    return taggedEntities[existingIndex];
  }
};

// User Access Management
export const getUserAccess = (userId: string): UserAccess | null => {
  return userAccess.find(a => a.userId === userId) || null;
};

export const setUserAccess = (access: UserAccess): UserAccess => {
  const existingIndex = userAccess.findIndex(a => a.userId === access.userId);
  
  if (existingIndex === -1) {
    userAccess.push(access);
    return access;
  } else {
    userAccess[existingIndex] = access;
    return access;
  }
};

export const getUserRole = (userId: string): UserRole | null => {
  const access = getUserAccess(userId);
  return access ? access.role : null;
};

export const setUserRole = (userId: string, role: UserRole): boolean => {
  const access = getUserAccess(userId);
  if (!access) return false;
  
  access.role = role;
  return true;
};

// Workspace Access Management
export const getWorkspaceAccess = (workspaceId: string): WorkspaceAccess | null => {
  return workspaceAccess.find(wa => wa.workspaceId === workspaceId) || null;
};

export const setWorkspaceAccess = (access: WorkspaceAccess): WorkspaceAccess => {
  const existingIndex = workspaceAccess.findIndex(wa => wa.workspaceId === access.workspaceId);
  
  if (existingIndex === -1) {
    workspaceAccess.push(access);
    return access;
  } else {
    workspaceAccess[existingIndex] = access;
    return access;
  }
};

// Project Access Management
export const getProjectAccess = (projectId: string): ProjectAccess | null => {
  return projectAccess.find(pa => pa.projectId === projectId) || null;
};

export const setProjectAccess = (access: ProjectAccess): ProjectAccess => {
  const existingIndex = projectAccess.findIndex(pa => pa.projectId === access.projectId);
  
  if (existingIndex === -1) {
    projectAccess.push(access);
    return access;
  } else {
    projectAccess[existingIndex] = access;
    return access;
  }
};

// Check if a user has access to an entity based on tags
export const userHasAccessToEntity = (userId: string, entityId: string): boolean => {
  const user = getUserAccess(userId);
  if (!user) return false;
  
  // Admins have access to everything
  if (user.role === 'admin') return true;
  
  const entity = taggedEntities.find(e => e.id === entityId);
  if (!entity) return false;
  
  // Check if the user has any of the tags associated with the entity
  return entity.tags.some(tagId => user.tags.includes(tagId));
};

// Initialize the service
initializeTagService(); 