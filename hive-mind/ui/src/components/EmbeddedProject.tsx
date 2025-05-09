import React, { useState, useEffect } from 'react';
import { Box, Tabs, Paper, Text, Group, Title, Loader, Button, Code, Alert, Divider, Textarea, ScrollArea } from '@mantine/core';
import { IconAlertCircle } from './layout/icons';
import { 
  GitPullRequest as IconGitPullRequest, 
  Code as IconCode, 
  Refresh as IconRefresh, 
  FileCode as IconFileCode,
  Check as IconCheck,
  X as IconX 
} from 'tabler-icons-react';
import axios from 'axios';

interface FileNode {
  id: string;
  name: string;
  type: 'file' | 'directory';
  path: string;
  children?: FileNode[];
}

interface ReviewComment {
  reviewer: string;
  timestamp: number;
  comments: string;
  approved?: boolean;
}

interface PendingReview {
  review_id: string;
  path: string;
  author: string;
  timestamp: number;
  commit_message: string;
  content: string;
  content_hash: string;
  status: 'pending' | 'approved' | 'rejected';
  reviews: ReviewComment[];
  is_approved: boolean;
}

export default function EmbeddedProject() {
  const [files, setFiles] = useState<FileNode[]>([]);
  const [pendingReviews, setPendingReviews] = useState<PendingReview[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<string | null>('files');
  const [selectedReview, setSelectedReview] = useState<PendingReview | null>(null);
  const [reviewComment, setReviewComment] = useState('');
  const [originalContent, setOriginalContent] = useState<string>('');
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Connect to websocket for real-time updates
  useEffect(() => {
    const wsUrl = `ws://${window.location.host}/api/embedded-project/events`;
    const newSocket = new WebSocket(wsUrl);
    
    newSocket.onopen = () => {
      console.log('Connected to embedded project events');
    };
    
    newSocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.type === 'file_changed') {
          // Refresh file list
          fetchFiles();
          
          // If the changed file is currently selected, update its content
          if (data.path === selectedFile) {
            setFileContent(data.content);
          }
          
          // Update last change timestamp
          setLastUpdate(new Date());
        } else if (data.type === 'review_created' || data.type === 'review_updated') {
          // Refresh pending reviews
          fetchPendingReviews();
          
          // If the updated review is currently selected, refresh it
          if (selectedReview && data.review_id === selectedReview.review_id) {
            fetchReviewDetails(data.review_id);
          }
        }
      } catch (e) {
        console.error('Error processing websocket message:', e);
      }
    };
    
    newSocket.onerror = (error) => {
      console.error('WebSocket error:', error);
      setError('Error connecting to real-time updates');
    };
    
    return () => {
      if (newSocket.readyState === WebSocket.OPEN) {
        newSocket.close();
      }
    };
  }, [selectedFile, selectedReview]);

  // Fetch files and pending reviews on component mount
  useEffect(() => {
    fetchFiles();
    fetchPendingReviews();
  }, []);

  const fetchFiles = async () => {
    try {
      setIsLoading(true);
      const response = await axios.get('/api/embedded-project/files');
      setFiles(response.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching embedded project files:', err);
      setError('Failed to load embedded project files');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchPendingReviews = async () => {
    try {
      const response = await axios.get('/api/embedded-project/reviews/pending');
      setPendingReviews(response.data);
    } catch (err) {
      console.error('Error fetching pending reviews:', err);
    }
  };

  const fetchFileContent = async (path: string) => {
    try {
      setIsLoading(true);
      const response = await axios.get(`/api/embedded-project/files/${encodeURIComponent(path)}/content`);
      setSelectedFile(path);
      setFileContent(response.data.content);
      setError(null);
    } catch (err) {
      console.error('Error fetching file content:', err);
      setError(`Failed to load content for ${path}`);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchReviewDetails = async (reviewId: string) => {
    try {
      setIsLoading(true);
      const response = await axios.get(`/api/embedded-project/reviews/${reviewId}`);
      setSelectedReview(response.data);
      
      // Also fetch the original file content if it exists
      if (response.data.path) {
        try {
          const originalResponse = await axios.get(`/api/embedded-project/files/${encodeURIComponent(response.data.path)}/content`);
          setOriginalContent(originalResponse.data.content);
        } catch (err) {
          // File might not exist yet, so set original content to empty
          setOriginalContent('');
        }
      }
      
      setError(null);
    } catch (err) {
      console.error('Error fetching review details:', err);
      setError(`Failed to load details for review ${reviewId}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFileSelect = (path: string) => {
    fetchFileContent(path);
  };

  const handleReviewSelect = (review: PendingReview) => {
    fetchReviewDetails(review.review_id);
  };

  const handleAddComment = async () => {
    if (!selectedReview || !reviewComment.trim()) return;
    
    try {
      setIsSubmitting(true);
      await axios.post(`/api/embedded-project/reviews/${selectedReview.review_id}/comment`, {
        comments: reviewComment
      });
      
      // Refresh the review details
      fetchReviewDetails(selectedReview.review_id);
      setReviewComment('');
    } catch (err) {
      console.error('Error adding comment:', err);
      setError('Failed to add comment');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleApproveReview = async () => {
    if (!selectedReview) return;
    
    try {
      setIsSubmitting(true);
      await axios.post(`/api/embedded-project/reviews/${selectedReview.review_id}/approve`, {
        message: reviewComment || 'Approved'
      });
      
      // Refresh reviews
      fetchPendingReviews();
      setSelectedReview(null);
      setReviewComment('');
    } catch (err) {
      console.error('Error approving review:', err);
      setError('Failed to approve review');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRejectReview = async () => {
    if (!selectedReview) return;
    
    if (!reviewComment.trim()) {
      setError('Please provide a reason for rejection');
      return;
    }
    
    try {
      setIsSubmitting(true);
      await axios.post(`/api/embedded-project/reviews/${selectedReview.review_id}/reject`, {
        message: reviewComment
      });
      
      // Refresh reviews
      fetchPendingReviews();
      setSelectedReview(null);
      setReviewComment('');
    } catch (err) {
      console.error('Error rejecting review:', err);
      setError('Failed to reject review');
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderFileTree = (nodes: FileNode[], depth = 0) => {
    return nodes.map(node => (
      <Box key={node.id} ml={depth * 16} mb={8}>
        <Box 
          key={`box-${node.id}`}
          className={selectedFile === node.path ? 'selected-file-item' : 'file-item'}
          onClick={() => node.type === 'file' ? handleFileSelect(node.path) : null}
          style={{ cursor: node.type === 'file' ? 'pointer' : 'default', padding: '4px 8px', borderRadius: '4px' }}
        >
          {node.type === 'directory' ? '📁 ' : '📄 '} {node.name}
        </Box>
        {node.children && node.children.length > 0 && renderFileTree(node.children, depth + 1)}
      </Box>
    ));
  };

  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleString();
  };

  // Compute a simple diff display
  const renderDiff = () => {
    if (!selectedReview) return null;
    
    // Split the content into lines
    const originalLines = originalContent.split('\n');
    const newLines = selectedReview.content.split('\n');
    
    // Simple line-by-line comparison
    const diffLines = [];
    const maxLines = Math.max(originalLines.length, newLines.length);
    
    for (let i = 0; i < maxLines; i++) {
      const originalLine = i < originalLines.length ? originalLines[i] : '';
      const newLine = i < newLines.length ? newLines[i] : '';
      
      if (originalLine !== newLine) {
        if (originalLine) {
          diffLines.push(<div key={`removed-${i}`} style={{ backgroundColor: 'rgba(255, 0, 0, 0.1)' }}>- {originalLine}</div>);
        }
        if (newLine) {
          diffLines.push(<div key={`added-${i}`} style={{ backgroundColor: 'rgba(0, 255, 0, 0.1)' }}>+ {newLine}</div>);
        }
      } else {
        diffLines.push(<div key={`unchanged-${i}`}> {originalLine}</div>);
      }
    }
    
    return (
      <ScrollArea h={300}>
        <Code block>
          {diffLines}
        </Code>
      </ScrollArea>
    );
  };

  return (
    <Box>
      <Group mb="md" position="apart">
        <Title order={2}>Embedded Project</Title>
        <Group>
          <Text size="sm" c="dimmed">
            Last updated: {lastUpdate.toLocaleString()}
          </Text>
          <Button
            leftIcon={<IconRefresh size={16} />}
            variant="light"
            onClick={() => {
              fetchFiles();
              fetchPendingReviews();
              setLastUpdate(new Date());
            }}
          >
            Refresh
          </Button>
        </Group>
      </Group>

      {error && (
        <Alert icon={<IconAlertCircle size={16} />} title="Error" color="red" mb="md" withCloseButton onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Tabs value={activeTab} onChange={setActiveTab}>
        <Tabs.List>
          <Tabs.Tab value="files" leftSection={<IconFileCode size={14} />}>Files</Tabs.Tab>
          <Tabs.Tab 
            value="reviews" 
            leftSection={<IconGitPullRequest size={14} />}
            rightSection={
              pendingReviews.length > 0 ? (
                <Box 
                  style={{
                    backgroundColor: '#228be6',
                    borderRadius: '50%',
                    height: 18,
                    width: 18,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}
                >
                  <Text size="xs" c="white">
                    {pendingReviews.length}
                  </Text>
                </Box>
              ) : null
            }
          >
            Pending Reviews
          </Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="files" pt="md">
          <Paper withBorder p="md">
            <Group mb="md" justify="apart">
              <Title order={3}>Project Files</Title>
            </Group>
            <Divider mb="md" />
            
            <Box style={{ display: 'flex', height: '70vh' }}>
              <Paper 
                withBorder 
                p="md" 
                style={{ 
                  width: '30%', 
                  maxHeight: '100%', 
                  overflowY: 'auto',
                  marginRight: '16px'
                }}
              >
                {isLoading && files.length === 0 ? (
                  <Box style={{ display: 'flex', justifyContent: 'center', padding: '20px' }}>
                    <Loader />
                  </Box>
                ) : files.length === 0 ? (
                  <Text c="dimmed">No files in the embedded project</Text>
                ) : (
                  renderFileTree(files)
                )}
              </Paper>
              
              <Paper 
                withBorder 
                p="md"
                style={{ 
                  flexGrow: 1, 
                  maxHeight: '100%', 
                  overflowY: 'auto'
                }}
              >
                {selectedFile ? (
                  <>
                    <Group mb="md">
                      <Title order={4}>{selectedFile}</Title>
                    </Group>
                    <Divider mb="md" />
                    {isLoading ? (
                      <Box style={{ display: 'flex', justifyContent: 'center', padding: '20px' }}>
                        <Loader />
                      </Box>
                    ) : (
                      <Code block>{fileContent}</Code>
                    )}
                  </>
                ) : (
                  <Box style={{ 
                    display: 'flex', 
                    justifyContent: 'center', 
                    alignItems: 'center',
                    height: '100%'
                  }}>
                    <Text c="dimmed">Select a file to view its content</Text>
                  </Box>
                )}
              </Paper>
            </Box>
          </Paper>
        </Tabs.Panel>

        <Tabs.Panel value="reviews" pt="md">
          {!selectedReview ? (
            <Paper withBorder p="md">
              <Group mb="md">
                <Title order={3}>Pending Reviews</Title>
              </Group>
              <Divider mb="md" />
              
              {isLoading ? (
                <Box style={{ display: 'flex', justifyContent: 'center', padding: '20px' }}>
                  <Loader />
                </Box>
              ) : pendingReviews.length === 0 ? (
                <Text c="dimmed">No pending reviews</Text>
              ) : (
                <Box>
                  {pendingReviews.map(review => (
                    <Paper 
                      key={review.review_id}
                      withBorder
                      p="md"
                      mb="md"
                      className="review-item"
                      style={{ cursor: 'pointer' }}
                      onClick={() => handleReviewSelect(review)}
                    >
                      <Group justify="apart">
                        <div>
                          <Text fw={500}>{review.path}</Text>
                          <Text size="sm">Author: {review.author}</Text>
                          <Text size="sm">Created: {formatTimestamp(review.timestamp)}</Text>
                          <Text size="sm">Message: {review.commit_message}</Text>
                        </div>
                        <Group>
                          <Button color="blue">View Details</Button>
                        </Group>
                      </Group>
                    </Paper>
                  ))}
                </Box>
              )}
            </Paper>
          ) : (
            <Paper withBorder p="md">
              <Group mb="md">
                <div>
                  <Title order={3}>Review: {selectedReview.path}</Title>
                  <Text>Author: {selectedReview.author}</Text>
                  <Text>Created: {formatTimestamp(selectedReview.timestamp)}</Text>
                </div>
                <Button 
                  variant="subtle" 
                  onClick={() => {
                    setSelectedReview(null);
                    setReviewComment('');
                  }}
                  ml="auto"
                >
                  Back to Reviews
                </Button>
              </Group>
              <Divider mb="md" />

              <Paper withBorder p="md" mb="md">
                <Title order={4} mb="sm">Commit Message</Title>
                <Text>{selectedReview.commit_message}</Text>
              </Paper>

              <Paper withBorder p="md" mb="md">
                <Title order={4} mb="sm">Changes</Title>
                {isLoading ? (
                  <Box style={{ display: 'flex', justifyContent: 'center', padding: '20px' }}>
                    <Loader />
                  </Box>
                ) : (
                  renderDiff()
                )}
              </Paper>

              <Paper withBorder p="md" mb="md">
                <Title order={4} mb="sm">Comments</Title>
                {selectedReview.reviews.length === 0 ? (
                  <Text c="dimmed" mb="md">No comments yet</Text>
                ) : (
                  <Box mb="md">
                    {selectedReview.reviews.map((review, index) => (
                      <Paper 
                        key={index} 
                        withBorder 
                        p="md" 
                        mb="md"
                        style={{
                          backgroundColor: review.approved !== undefined
                            ? (review.approved 
                              ? 'rgba(0, 255, 0, 0.05)' 
                              : 'rgba(255, 0, 0, 0.05)')
                            : 'transparent'
                        }}
                      >
                        <Group mb="xs">
                          <Text fw={500}>{review.reviewer}</Text>
                          <Text size="sm" ml="auto">{formatTimestamp(review.timestamp)}</Text>
                        </Group>
                        <Text mb="xs">{review.comments}</Text>
                        {review.approved !== undefined && (
                          <Text fw={700} c={review.approved ? 'green' : 'red'}>
                            {review.approved ? 'APPROVED' : 'REJECTED'}
                          </Text>
                        )}
                      </Paper>
                    ))}
                  </Box>
                )}

                <Textarea
                  placeholder="Add your comment or feedback..."
                  label="Your Comment"
                  value={reviewComment}
                  onChange={(e) => setReviewComment(e.currentTarget.value)}
                  minRows={3}
                  mb="md"
                />

                <Group justify="flex-end">
                  <Button 
                    leftSection={<IconCheck size={16} />} 
                    color="green"
                    onClick={handleApproveReview}
                    loading={isSubmitting}
                    disabled={isSubmitting}
                  >
                    Approve
                  </Button>
                  <Button 
                    leftSection={<IconX size={16} />} 
                    color="red"
                    variant="outline"
                    onClick={handleRejectReview}
                    loading={isSubmitting}
                    disabled={isSubmitting || !reviewComment.trim()}
                  >
                    Reject
                  </Button>
                  <Button 
                    onClick={handleAddComment}
                    loading={isSubmitting}
                    disabled={isSubmitting || !reviewComment.trim()}
                  >
                    Add Comment
                  </Button>
                </Group>
              </Paper>
            </Paper>
          )}
        </Tabs.Panel>
      </Tabs>
    </Box>
  );
} 