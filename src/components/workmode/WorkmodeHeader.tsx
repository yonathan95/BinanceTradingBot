import { useState } from 'react';
import { useTagAccess } from '../../hooks/useTagAccess';

interface WorkmodeHeaderProps {
  title: string;
  entityId: string;
  entityType: 'workspace' | 'project';
}

const WorkmodeHeader = ({ title, entityId, entityType }: WorkmodeHeaderProps) => {
  const { userRole, setUserRole } = useTagAccess();
  const [showRoleToggle, setShowRoleToggle] = useState(false);

  const toggleRole = () => {
    if (userRole === 'admin') {
      setUserRole('developer');
    } else {
      setUserRole('admin');
    }
  };

  return (
    <div className="flex justify-between items-center p-4 bg-gray-50 border-b border-gray-200">
      <div>
        <h1 className="text-2xl font-bold">{title}</h1>
        <p className="text-gray-500">
          {entityType === 'workspace' ? 'Workspace' : 'Project'} Mode
        </p>
      </div>
      
      <div className="flex items-center space-x-4">
        {/* Development mode role toggle */}
        <div className="flex items-center">
          <button 
            onClick={() => setShowRoleToggle(!showRoleToggle)}
            className="text-sm text-gray-600 hover:text-gray-800"
          >
            Development Settings
          </button>
          
          {showRoleToggle && (
            <div className="ml-4 flex items-center">
              <span className="mr-2 text-sm">Role:</span>
              <div className="relative inline-block w-10 mr-2 align-middle select-none transition duration-200 ease-in">
                <input 
                  type="checkbox" 
                  name="role-toggle" 
                  id="role-toggle" 
                  checked={userRole === 'admin'}
                  onChange={toggleRole}
                  className="toggle-checkbox absolute block w-6 h-6 rounded-full bg-white border-4 appearance-none cursor-pointer"
                />
                <label 
                  htmlFor="role-toggle" 
                  className="toggle-label block overflow-hidden h-6 rounded-full bg-gray-300 cursor-pointer"
                ></label>
              </div>
              <span className="text-sm font-medium">
                {userRole === 'admin' ? 'Administrator' : 'Developer'}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default WorkmodeHeader; 