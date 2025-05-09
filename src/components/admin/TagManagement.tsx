import { useState, useEffect } from 'react';
import { useTagAccess } from '../../hooks/useTagAccess';
import { Tag } from '../../services/tags/types';
import * as tagService from '../../services/tags/tagService';

const TagManagement = () => {
  const { userRole, availableTags } = useTagAccess();
  const [tags, setTags] = useState<Tag[]>([]);
  const [newTag, setNewTag] = useState<Omit<Tag, 'id'>>({
    name: '',
    color: '#3182ce', // Default blue color
    type: 'project'
  });
  const [isEditing, setIsEditing] = useState<string | null>(null);
  const [editTag, setEditTag] = useState<Partial<Tag>>({});

  // Only admins should have access to this component
  const isAdmin = userRole === 'admin';

  useEffect(() => {
    // Load tags when the component mounts
    setTags(availableTags);
  }, [availableTags]);

  const handleCreateTag = () => {
    if (!isAdmin || !newTag.name.trim()) return;
    
    const createdTag = tagService.createTag(newTag);
    setTags([...tags, createdTag]);
    
    // Reset form
    setNewTag({
      name: '',
      color: '#3182ce',
      type: 'project'
    });
  };

  const handleEditClick = (tag: Tag) => {
    setIsEditing(tag.id);
    setEditTag({ ...tag });
  };

  const handleUpdateTag = () => {
    if (!isAdmin || !isEditing || !editTag.name?.trim()) return;
    
    const updatedTag = tagService.updateTag(isEditing, editTag);
    if (updatedTag) {
      setTags(tags.map(tag => tag.id === isEditing ? updatedTag : tag));
    }
    
    // Reset editing state
    setIsEditing(null);
    setEditTag({});
  };

  const handleDeleteTag = (tagId: string) => {
    if (!isAdmin) return;
    
    const deleted = tagService.deleteTag(tagId);
    if (deleted) {
      setTags(tags.filter(tag => tag.id !== tagId));
    }
  };

  if (!isAdmin) {
    return <div className="p-6">Only administrators can manage tags.</div>;
  }

  return (
    <div className="p-6">
      <h2 className="text-xl font-semibold mb-4">Tag Management</h2>
      
      {/* Create New Tag */}
      <div className="bg-white p-4 rounded-lg shadow-sm mb-6">
        <h3 className="text-lg font-medium mb-3">Create New Tag</h3>
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Name
            </label>
            <input
              type="text"
              value={newTag.name}
              onChange={(e) => setNewTag({...newTag, name: e.target.value})}
              className="w-full p-2 border rounded"
              placeholder="Tag name"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Color
            </label>
            <input
              type="color"
              value={newTag.color}
              onChange={(e) => setNewTag({...newTag, color: e.target.value})}
              className="w-full p-1 h-10 border rounded cursor-pointer"
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Type
            </label>
            <select
              value={newTag.type}
              onChange={(e) => setNewTag({
                ...newTag, 
                type: e.target.value as 'workspace' | 'project' | 'user'
              })}
              className="w-full p-2 border rounded"
            >
              <option value="workspace">Workspace</option>
              <option value="project">Project</option>
              <option value="user">User</option>
            </select>
          </div>
          
          <div className="flex items-end">
            <button
              onClick={handleCreateTag}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Create Tag
            </button>
          </div>
        </div>
      </div>
      
      {/* Tag List */}
      <div className="bg-white p-4 rounded-lg shadow-sm">
        <h3 className="text-lg font-medium mb-3">Existing Tags</h3>
        
        {tags.length === 0 ? (
          <p className="text-gray-500">No tags available.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="py-3 px-4 text-left">Name</th>
                  <th className="py-3 px-4 text-left">Color</th>
                  <th className="py-3 px-4 text-left">Type</th>
                  <th className="py-3 px-4 text-left">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {tags.map(tag => (
                  <tr key={tag.id}>
                    <td className="py-3 px-4">
                      {isEditing === tag.id ? (
                        <input
                          type="text"
                          value={editTag.name || ''}
                          onChange={(e) => setEditTag({...editTag, name: e.target.value})}
                          className="w-full p-1 border rounded"
                        />
                      ) : (
                        <div className="flex items-center">
                          <span
                            className="w-3 h-3 rounded-full mr-2"
                            style={{ backgroundColor: tag.color }}
                          ></span>
                          {tag.name}
                        </div>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      {isEditing === tag.id ? (
                        <input
                          type="color"
                          value={editTag.color || '#000000'}
                          onChange={(e) => setEditTag({...editTag, color: e.target.value})}
                          className="w-12 p-0 h-8 border rounded cursor-pointer"
                        />
                      ) : (
                        <div className="flex items-center">
                          <span className="text-xs text-gray-500">{tag.color}</span>
                        </div>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      {isEditing === tag.id ? (
                        <select
                          value={editTag.type || 'project'}
                          onChange={(e) => setEditTag({
                            ...editTag, 
                            type: e.target.value as 'workspace' | 'project' | 'user'
                          })}
                          className="w-full p-1 border rounded"
                        >
                          <option value="workspace">Workspace</option>
                          <option value="project">Project</option>
                          <option value="user">User</option>
                        </select>
                      ) : (
                        <span className="capitalize">{tag.type}</span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      {isEditing === tag.id ? (
                        <div className="flex space-x-2">
                          <button
                            onClick={handleUpdateTag}
                            className="px-3 py-1 bg-green-600 text-white text-sm rounded hover:bg-green-700"
                          >
                            Save
                          </button>
                          <button
                            onClick={() => {
                              setIsEditing(null);
                              setEditTag({});
                            }}
                            className="px-3 py-1 bg-gray-500 text-white text-sm rounded hover:bg-gray-600"
                          >
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleEditClick(tag)}
                            className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDeleteTag(tag.id)}
                            className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
                          >
                            Delete
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default TagManagement; 