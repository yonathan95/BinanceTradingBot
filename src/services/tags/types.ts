export type Tag = {
  id: string;
  name: string;
  color: string;
  type: 'workspace' | 'project' | 'user';
};

export type UserRole = 'admin' | 'developer';

export type UserAccess = {
  userId: string;
  username: string;
  role: UserRole;
  tags: string[]; // Tag IDs the user has access to
};

export type TaggedEntity = {
  id: string;
  name: string;
  type: 'workspace' | 'project';
  tags: string[]; // Tag IDs associated with this entity
};

export type WorkspaceAccess = {
  workspaceId: string;
  projects: string[]; // Project IDs in this workspace
  tags: string[]; // Tag IDs at workspace level
};

export type ProjectAccess = {
  projectId: string;
  workspaceId: string;
  tags: string[]; // Tag IDs at project level
}; 