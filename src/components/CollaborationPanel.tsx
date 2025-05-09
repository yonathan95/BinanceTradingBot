import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { io, Socket } from 'socket.io-client';

interface Collaborator {
  id: string;
  name: string;
  avatar: string;
  status: 'active' | 'idle' | 'offline';
  cursor?: {
    file: string;
    position: { line: number; column: number };
  };
  lastActive: string;
}

interface Comment {
  id: string;
  author: {
    id: string;
    name: string;
    avatar: string;
  };
  content: string;
  file: string;
  line: number;
  timestamp: string;
  resolved: boolean;
  replies: Comment[];
}

interface CollaborationPanelProps {
  projectId: string;
  currentFile: string | null;
}

const CollaborationPanel: React.FC<CollaborationPanelProps> = ({
  projectId,
  currentFile
}) => {
  const [collaborators, setCollaborators] = useState<Collaborator[]>([]);
  const [comments, setComments] = useState<Comment[]>([]);
  const [newComment, setNewComment] = useState('');
  const [activeTab, setActiveTab] = useState<'collaborators' | 'comments'>('collaborators');
  const [socket, setSocket] = useState<Socket | null>(null);
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const commentInputRef = useRef<HTMLTextAreaElement>(null);

  // Connect to WebSocket when component mounts
  useEffect(() => {
    const socketUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/ws';
    const newSocket = io(socketUrl, {
      query: { projectId }
    });

    newSocket.on('connect', () => {
      console.log('Connected to collaboration server');
    });

    newSocket.on('disconnect', () => {
      console.log('Disconnected from collaboration server');
    });

    newSocket.on('collaborator_joined', (collaborator: Collaborator) => {
      setCollaborators(prevCollaborators => {
        if (prevCollaborators.some(c => c.id === collaborator.id)) {
          return prevCollaborators.map(c => 
            c.id === collaborator.id ? { ...c, status: 'active' } : c
          );
        } else {
          return [...prevCollaborators, collaborator];
        }
      });
    });

    newSocket.on('collaborator_left', (collaboratorId: string) => {
      setCollaborators(prevCollaborators => 
        prevCollaborators.map(c => 
          c.id === collaboratorId ? { ...c, status: 'offline' } : c
        )
      );
    });

    newSocket.on('cursor_moved', (data: { userId: string; file: string; position: { line: number; column: number } }) => {
      setCollaborators(prevCollaborators => 
        prevCollaborators.map(c => 
          c.id === data.userId 
            ? { 
                ...c, 
                cursor: { 
                  file: data.file, 
                  position: data.position 
                },
                lastActive: new Date().toISOString()
              } 
            : c
        )
      );
    });

    newSocket.on('comment_added', (comment: Comment) => {
      setComments(prevComments => [...prevComments, comment]);
    });

    newSocket.on('comment_updated', (updatedComment: Comment) => {
      setComments(prevComments => 
        prevComments.map(c => 
          c.id === updatedComment.id ? updatedComment : c
        )
      );
    });

    setSocket(newSocket);

    return () => {
      newSocket.disconnect();
    };
  }, [projectId]);

  // Fetch initial collaborators and comments data
  useEffect(() => {
    const fetchCollaborationData = async () => {
      try {
        setIsLoading(true);
        const [collaboratorsResponse, commentsResponse] = await Promise.all([
          axios.get(`/api/projects/${projectId}/collaborators`),
          axios.get(`/api/projects/${projectId}/comments`)
        ]);
        
        setCollaborators(collaboratorsResponse.data);
        setComments(commentsResponse.data);
        setError('');
      } catch (err) {
        setError('Failed to load collaboration data');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchCollaborationData();
  }, [projectId]);

  // Update cursor position
  const updateCursorPosition = (position: { line: number; column: number }) => {
    if (socket && currentFile) {
      socket.emit('cursor_move', {
        file: currentFile,
        position
      });
    }
  };

  // Add new comment
  const handleAddComment = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!newComment.trim() || !currentFile) return;
    
    try {
      const response = await axios.post(`/api/projects/${projectId}/comments`, {
        content: newComment,
        file: currentFile,
        line: 1, // This should be the actual line number where the comment is being added
      });
      
      setComments(prevComments => [...prevComments, response.data]);
      setNewComment('');
      
      // Also emit via socket for real-time updates
      if (socket) {
        socket.emit('comment_add', response.data);
      }
    } catch (err) {
      setError('Failed to add comment');
      console.error(err);
    }
  };

  // Toggle comment resolution
  const handleToggleResolution = async (commentId: string, resolved: boolean) => {
    try {
      const response = await axios.patch(`/api/projects/${projectId}/comments/${commentId}`, {
        resolved: !resolved
      });
      
      setComments(prevComments => 
        prevComments.map(c => 
          c.id === commentId ? response.data : c
        )
      );
      
      // Also emit via socket for real-time updates
      if (socket) {
        socket.emit('comment_update', response.data);
      }
    } catch (err) {
      setError('Failed to update comment');
      console.error(err);
    }
  };

  // Filter comments by current file
  const currentFileComments = currentFile 
    ? comments.filter(comment => comment.file === currentFile)
    : comments;

  if (isLoading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading collaboration data...</p>
      </div>
    );
  }

  return (
    <div className="collaboration-panel">
      <div className="tabs">
        <button 
          className={`tab ${activeTab === 'collaborators' ? 'active' : ''}`}
          onClick={() => setActiveTab('collaborators')}
        >
          Collaborators ({collaborators.filter(c => c.status === 'active').length})
        </button>
        <button 
          className={`tab ${activeTab === 'comments' ? 'active' : ''}`}
          onClick={() => setActiveTab('comments')}
        >
          Comments ({currentFileComments.length})
        </button>
      </div>

      {error && <div className="error-message">{error}</div>}

      <div className="tab-content">
        {activeTab === 'collaborators' && (
          <div className="collaborators-list">
            {collaborators.length === 0 ? (
              <p className="empty-message">No collaborators yet</p>
            ) : (
              collaborators.map(collaborator => (
                <div 
                  key={collaborator.id} 
                  className={`collaborator-item ${collaborator.status}`}
                >
                  <div className="collaborator-avatar">
                    <img src={collaborator.avatar} alt={collaborator.name} />
                    <span className={`status-indicator ${collaborator.status}`}></span>
                  </div>
                  <div className="collaborator-info">
                    <div className="collaborator-name">{collaborator.name}</div>
                    <div className="collaborator-status">
                      {collaborator.status === 'active' && collaborator.cursor ? (
                        <span>
                          Editing {collaborator.cursor.file} at line {collaborator.cursor.position.line}
                        </span>
                      ) : (
                        <span>
                          {collaborator.status === 'active' ? 'Active' : 
                           collaborator.status === 'idle' ? 'Idle' : 'Offline'}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="collaborator-time">
                    {collaborator.lastActive && 
                      `Last active: ${new Date(collaborator.lastActive).toLocaleTimeString()}`}
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'comments' && (
          <div className="comments-container">
            <div className="comments-list">
              {currentFileComments.length === 0 ? (
                <p className="empty-message">No comments for this file</p>
              ) : (
                currentFileComments.map(comment => (
                  <div 
                    key={comment.id} 
                    className={`comment-item ${comment.resolved ? 'resolved' : ''}`}
                  >
                    <div className="comment-header">
                      <div className="comment-author">
                        <img src={comment.author.avatar} alt={comment.author.name} />
                        <span>{comment.author.name}</span>
                      </div>
                      <div className="comment-time">
                        {new Date(comment.timestamp).toLocaleString()}
                      </div>
                    </div>
                    <div className="comment-content">{comment.content}</div>
                    <div className="comment-actions">
                      <button 
                        className={`btn btn-sm ${comment.resolved ? 'btn-success' : 'btn-outline-success'}`}
                        onClick={() => handleToggleResolution(comment.id, comment.resolved)}
                      >
                        {comment.resolved ? 'Resolved' : 'Resolve'}
                      </button>
                      <button className="btn btn-sm btn-outline-primary">
                        Reply
                      </button>
                    </div>
                    {comment.replies.length > 0 && (
                      <div className="comment-replies">
                        {comment.replies.map(reply => (
                          <div key={reply.id} className="reply-item">
                            <div className="reply-header">
                              <div className="reply-author">
                                <img src={reply.author.avatar} alt={reply.author.name} />
                                <span>{reply.author.name}</span>
                              </div>
                              <div className="reply-time">
                                {new Date(reply.timestamp).toLocaleString()}
                              </div>
                            </div>
                            <div className="reply-content">{reply.content}</div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>

            {currentFile && (
              <form className="add-comment-form" onSubmit={handleAddComment}>
                <textarea
                  ref={commentInputRef}
                  className="comment-input"
                  placeholder="Add a comment..."
                  value={newComment}
                  onChange={(e) => setNewComment(e.target.value)}
                  rows={3}
                ></textarea>
                <button 
                  type="submit" 
                  className="btn btn-primary"
                  disabled={!newComment.trim()}
                >
                  Add Comment
                </button>
              </form>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default CollaborationPanel; 