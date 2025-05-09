import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import AgentProfile from '../components/AgentProfile';

const AgentProfilePage: React.FC = () => {
  const { agentId } = useParams<{ agentId: string }>();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Validate that agentId exists
    if (!agentId) {
      setError('Agent ID is required');
      setIsLoading(false);
      return;
    }

    // Check if agent exists (could make an API call here)
    const checkAgentExists = async () => {
      try {
        // In a real implementation, this would verify the agent exists
        // const response = await fetch(`/api/agents/${agentId}/exists`);
        // if (!response.ok) throw new Error('Agent not found');
        
        setIsLoading(false);
      } catch (err) {
        setError('Agent not found or inaccessible');
        setIsLoading(false);
      }
    };

    checkAgentExists();
  }, [agentId]);

  const handleBack = () => {
    navigate(-1);
  };

  if (isLoading) {
    return <div className="loading-container">Loading agent profile...</div>;
  }

  if (error) {
    return (
      <div className="error-container">
        <h2>Error</h2>
        <p>{error}</p>
        <button onClick={handleBack} className="back-button">
          Go Back
        </button>
      </div>
    );
  }

  return (
    <div className="agent-profile-page">
      <div className="page-header">
        <button onClick={handleBack} className="back-button">
          &larr; Back
        </button>
        <h1>Agent Profile</h1>
      </div>
      
      {agentId && <AgentProfile agentId={agentId} />}
    </div>
  );
};

export default AgentProfilePage; 