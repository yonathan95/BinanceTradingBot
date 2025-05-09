import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import ReactDiffViewer from 'react-diff-viewer';

interface FileNode {
  id: string;
  name: string;
  type: 'file' | 'directory';
  path: string;
  children?: FileNode[];
}

interface FileVersion {
  id: string;
  version: number;
  commit_hash: string;
  commit_message: string;
  author: string;
  timestamp: string;
}

interface FileManagerProps {
  projectId: string;
  onFileSelect?: (filePath: string, content: string) => void;
}

const FileManager: React.FC<FileManagerProps> = ({ projectId, onFileSelect }) => {
  const [fileTree, setFileTree] = useState<FileNode[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string>('');
  const [fileVersions, setFileVersions] = useState<FileVersion[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<string | null>(null);
  const [compareVersion, setCompareVersion] = useState<string | null>(null);
  const [versionContent, setVersionContent] = useState<string>('');
  const [compareContent, setCompareContent] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [viewMode, setViewMode] = useState<'code' | 'diff'>('code');

  useEffect(() => {
    const fetchFileTree = async () => {
      try {
        setIsLoading(true);
        const response = await axios.get(`/api/projects/${projectId}/files`);
        setFileTree(response.data);
        setError('');
      } catch (err) {
        setError('Failed to load file structure');
        console.error(err);
      } finally {
        setIsLoading(false);
      }
    };

    fetchFileTree();
  }, [projectId]);

  const handleFileSelect = async (filePath: string, fileType: string) => {
    if (fileType === 'directory') return;
    
    try {
      setIsLoading(true);
      
      // Fetch current file content
      const contentResponse = await axios.get(`/api/projects/${projectId}/files/${encodeURIComponent(filePath)}/content`);
      setFileContent(contentResponse.data.content);
      setSelectedFile(filePath);
      
      // Fetch file version history
      const versionsResponse = await axios.get(`/api/projects/${projectId}/files/${encodeURIComponent(filePath)}/versions`);
      setFileVersions(versionsResponse.data);
      
      // Reset version selections
      setSelectedVersion(null);
      setCompareVersion(null);
      setVersionContent('');
      setCompareContent('');
      
      // Set view mode back to code
      setViewMode('code');
      
      // Call the onFileSelect callback if provided
      if (onFileSelect) {
        onFileSelect(filePath, contentResponse.data.content);
      }
    } catch (err) {
      setError('Failed to load file content');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleVersionSelect = async (versionId: string) => {
    try {
      const response = await axios.get(`/api/projects/${projectId}/files/${encodeURIComponent(selectedFile!)}/versions/${versionId}/content`);
      setSelectedVersion(versionId);
      setVersionContent(response.data.content);
      
      if (compareVersion) {
        setViewMode('diff');
      }
    } catch (err) {
      setError('Failed to load version content');
      console.error(err);
    }
  };

  const handleCompareVersionSelect = async (versionId: string) => {
    try {
      const response = await axios.get(`/api/projects/${projectId}/files/${encodeURIComponent(selectedFile!)}/versions/${versionId}/content`);
      setCompareVersion(versionId);
      setCompareContent(response.data.content);
      
      if (selectedVersion) {
        setViewMode('diff');
      }
    } catch (err) {
      setError('Failed to load compare version content');
      console.error(err);
    }
  };

  const getFileExtension = (filename: string): string => {
    const parts = filename.split('.');
    if (parts.length > 1) {
      return parts[parts.length - 1].toLowerCase();
    }
    return '';
  };

  const getLanguageFromExtension = (extension: string): string => {
    const languageMap: { [key: string]: string } = {
      'js': 'javascript',
      'jsx': 'jsx',
      'ts': 'typescript',
      'tsx': 'tsx',
      'py': 'python',
      'rb': 'ruby',
      'go': 'go',
      'java': 'java',
      'c': 'c',
      'cpp': 'cpp',
      'cs': 'csharp',
      'html': 'html',
      'css': 'css',
      'scss': 'scss',
      'json': 'json',
      'md': 'markdown',
      'yml': 'yaml',
      'yaml': 'yaml',
      'sh': 'bash',
      'bash': 'bash',
      'php': 'php',
      'sql': 'sql',
      'txt': 'text',
    };
    
    return languageMap[extension] || 'text';
  };

  const renderFileTree = (nodes: FileNode[], depth = 0) => {
    return nodes.map((node) => (
      <div key={node.id}>
        <div 
          className={`file-item ${node.type} ${selectedFile === node.path ? 'active' : ''}`}
          style={{ marginLeft: `${depth * 16}px` }}
          onClick={() => handleFileSelect(node.path, node.type)}
        >
          {node.type === 'directory' ? '📁' : '📄'} {node.name}
        </div>
        {node.children && node.children.length > 0 && renderFileTree(node.children, depth + 1)}
      </div>
    ));
  };

  if (isLoading && fileTree.length === 0) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>Loading files...</p>
      </div>
    );
  }

  const getFileLanguage = () => {
    if (!selectedFile) return 'text';
    const extension = getFileExtension(selectedFile);
    return getLanguageFromExtension(extension);
  };

  return (
    <div className="file-manager">
      <div className="file-manager-container">
        <div className="file-tree-panel">
          <div className="panel-header">
            <h3>Files</h3>
          </div>
          <div className="file-tree">
            {fileTree.length === 0 ? (
              <p className="empty-message">No files</p>
            ) : (
              renderFileTree(fileTree)
            )}
          </div>
        </div>

        <div className="file-content-panel">
          {selectedFile ? (
            <>
              <div className="file-content-header">
                <h3>{selectedFile}</h3>
                <div className="view-controls">
                  <button 
                    className={`btn ${viewMode === 'code' ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => setViewMode('code')}
                  >
                    Code
                  </button>
                  <button 
                    className={`btn ${viewMode === 'diff' ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => setViewMode('diff')}
                    disabled={!selectedVersion || !compareVersion}
                  >
                    Diff
                  </button>
                </div>
              </div>

              {error && <div className="error-message">{error}</div>}

              <div className="file-content-wrapper">
                {viewMode === 'code' ? (
                  <SyntaxHighlighter 
                    language={getFileLanguage()} 
                    style={vscDarkPlus}
                    showLineNumbers={true}
                    wrapLines={true}
                  >
                    {selectedVersion ? versionContent : fileContent}
                  </SyntaxHighlighter>
                ) : (
                  <ReactDiffViewer
                    oldValue={compareContent}
                    newValue={versionContent}
                    splitView={true}
                    useDarkTheme={true}
                    showLineNumbers={true}
                  />
                )}
              </div>
            </>
          ) : (
            <div className="empty-state">
              <p>Select a file to view its content</p>
            </div>
          )}
        </div>

        {selectedFile && (
          <div className="version-history-panel">
            <div className="panel-header">
              <h3>Version History</h3>
            </div>
            
            {fileVersions.length === 0 ? (
              <p className="empty-message">No version history available</p>
            ) : (
              <div className="versions-list">
                <div className="version-select-controls">
                  <div className="version-select">
                    <label>Version 1:</label>
                    <select 
                      value={selectedVersion || ''} 
                      onChange={(e) => handleVersionSelect(e.target.value)}
                    >
                      <option value="">Current</option>
                      {fileVersions.map(version => (
                        <option key={version.id} value={version.id}>
                          v{version.version} - {new Date(version.timestamp).toLocaleDateString()}
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  <div className="version-select">
                    <label>Version 2:</label>
                    <select 
                      value={compareVersion || ''} 
                      onChange={(e) => handleCompareVersionSelect(e.target.value)}
                      disabled={!selectedVersion}
                    >
                      <option value="">Select version to compare</option>
                      {fileVersions
                        .filter(version => version.id !== selectedVersion)
                        .map(version => (
                          <option key={version.id} value={version.id}>
                            v{version.version} - {new Date(version.timestamp).toLocaleDateString()}
                          </option>
                        ))
                      }
                    </select>
                  </div>
                </div>
                
                <div className="versions-history-list">
                  {fileVersions.map(version => (
                    <div 
                      key={version.id} 
                      className={`version-item ${selectedVersion === version.id ? 'selected' : ''}`}
                      onClick={() => handleVersionSelect(version.id)}
                    >
                      <div className="version-header">
                        <span className="version-number">v{version.version}</span>
                        <span className="version-date">
                          {new Date(version.timestamp).toLocaleString()}
                        </span>
                      </div>
                      <div className="version-author">{version.author}</div>
                      <div className="version-message">{version.commit_message}</div>
                      <div className="version-hash">{version.commit_hash.substring(0, 7)}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default FileManager; 