import { useState, useEffect, useContext, createContext, ReactNode } from 'react';
import * as tagService from '../services/tags/tagService';
import { Tag, UserAccess, UserRole, TaggedEntity } from '../services/tags/types';
import { useAuth } from './useAuth';

interface TagAccessContextType {
  userRole: UserRole | null;
  setUserRole: (role: UserRole) => void;
  hasAccessToEntity: (entityId: string) => boolean;
  getAccessibleEntities: (entityType?: 'workspace' | 'project') => TaggedEntity[];
  availableTags: Tag[];
  assignedTags: string[];
  assignTagToEntity: (entityId: string, entityName: string, entityType: 'workspace' | 'project', tagIds: string[]) => void;
  assignTagsToUser: (tagIds: string[]) => void;
}

const TagAccessContext = createContext<TagAccessContextType | undefined>(undefined);

interface TagAccessProviderProps {
  children: ReactNode;
}

export const TagAccessProvider = ({ children }: TagAccessProviderProps) => {
  const { user } = useAuth();
  const [userAccess, setUserAccess] = useState<UserAccess | null>(null);
  const [availableTags, setAvailableTags] = useState<Tag[]>([]);
  const [isAdmin, setIsAdmin] = useState(false);

  // Initialize with mock data for development
  useEffect(() => {
    if (user) {
      // For development, create a mock user access if it doesn't exist
      const access = tagService.getUserAccess(user.id);
      if (!access) {
        const newAccess: UserAccess = {
          userId: user.id,
          username: user.username || 'User',
          role: 'developer', // default role
          tags: ['tag-1', 'tag-2'] // default tags
        };
        tagService.setUserAccess(newAccess);
        setUserAccess(newAccess);
      } else {
        setUserAccess(access);
      }

      // Load available tags
      setAvailableTags(tagService.getTags());
    }
  }, [user]);

  // Update admin status when userAccess changes
  useEffect(() => {
    setIsAdmin(userAccess?.role === 'admin');
  }, [userAccess]);

  const setUserRole = (role: UserRole) => {
    if (user && userAccess) {
      const updated = tagService.setUserRole(user.id, role);
      if (updated) {
        setUserAccess({ ...userAccess, role });
      }
    }
  };

  const hasAccessToEntity = (entityId: string): boolean => {
    if (!user) return false;
    return tagService.userHasAccessToEntity(user.id, entityId);
  };

  const getAccessibleEntities = (entityType?: 'workspace' | 'project'): TaggedEntity[] => {
    if (!user) return [];
    
    const allEntities = tagService.getTaggedEntities();
    
    // Filter by entity type if provided
    const typeFilteredEntities = entityType
      ? allEntities.filter(entity => entity.type === entityType)
      : allEntities;
    
    // Admin can see all entities
    if (isAdmin) return typeFilteredEntities;
    
    // Regular users can only see entities with tags they have access to
    return typeFilteredEntities.filter(entity => 
      hasAccessToEntity(entity.id)
    );
  };

  const assignTagToEntity = (
    entityId: string,
    entityName: string,
    entityType: 'workspace' | 'project',
    tagIds: string[]
  ) => {
    if (!isAdmin) return; // Only admins can assign tags
    
    tagService.tagEntity(entityId, entityName, entityType, tagIds);
    setAvailableTags([...tagService.getTags()]); // Refresh available tags
  };

  const assignTagsToUser = (tagIds: string[]) => {
    if (!user || !userAccess || !isAdmin) return;
    
    const updatedAccess: UserAccess = {
      ...userAccess,
      tags: tagIds
    };
    
    tagService.setUserAccess(updatedAccess);
    setUserAccess(updatedAccess);
  };

  const value = {
    userRole: userAccess?.role || null,
    setUserRole,
    hasAccessToEntity,
    getAccessibleEntities,
    availableTags,
    assignedTags: userAccess?.tags || [],
    assignTagToEntity,
    assignTagsToUser
  };

  return (
    <TagAccessContext.Provider value={value}>
      {children}
    </TagAccessContext.Provider>
  );
};

export const useTagAccess = (): TagAccessContextType => {
  const context = useContext(TagAccessContext);
  if (context === undefined) {
    throw new Error('useTagAccess must be used within a TagAccessProvider');
  }
  return context;
}; 