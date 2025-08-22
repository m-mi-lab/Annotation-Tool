import React, { useState, useEffect, useContext, createContext } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import axios from "axios";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Label } from "./components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "./components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Badge } from "./components/ui/badge";
import { Textarea } from "./components/ui/textarea";
import { Alert, AlertDescription } from "./components/ui/alert";
import { Progress } from "./components/ui/progress";
import { Checkbox } from "./components/ui/checkbox";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select";
import { Separator } from "./components/ui/separator";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from "./components/ui/dialog";
import { FileText, Users, BarChart3, Upload, User, LogOut, Tag, CheckCircle, Plus, X, SkipForward, Shield, Settings, Trash2, Edit, Eye } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem('token'));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      fetchUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchUser = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`);
      setUser(response.data);
    } catch (error) {
      console.error('Error fetching user:', error);
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const response = await axios.post(`${API}/auth/login`, { email, password });
      const { access_token } = response.data;
      
      setToken(access_token);
      localStorage.setItem('token', access_token);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      await fetchUser();
      return { success: true };
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Login failed' };
    }
  };

  const register = async (email, password, fullName, role = 'annotator') => {
    try {
      await axios.post(`${API}/auth/register`, {
        email,
        password,
        full_name: fullName,
        role
      });
      
      // Auto-login after registration
      return await login(email, password);
    } catch (error) {
      return { success: false, error: error.response?.data?.detail || 'Registration failed' };
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    delete axios.defaults.headers.common['Authorization'];
  };

  const value = {
    user,
    token,
    loading,
    login,
    register,
    logout
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// Components
const Header = () => {
  const { user, logout } = useAuth();

  return (
    <header className="bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-3">
            <FileText className="h-8 w-8 text-blue-600" />
            <h1 className="text-xl font-semibold text-gray-900">
              SDOH Annotation Tool
            </h1>
          </div>
          
          {user && (
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                {user.role === 'admin' && (
                  <Shield className="h-4 w-4 text-purple-600" title="Administrator" />
                )}
                <User className="h-4 w-4 text-gray-500" />
                <span className="text-sm text-gray-700">{user.full_name}</span>
                <Badge variant={user.role === 'admin' ? 'default' : 'secondary'}>
                  {user.role}
                </Badge>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={logout}
                className="flex items-center space-x-1"
              >
                <LogOut className="h-4 w-4" />
                <span>Logout</span>
              </Button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};

const AuthForm = () => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  const { login, register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      let result;
      if (isLogin) {
        result = await login(email, password);
      } else {
        result = await register(email, password, fullName);
      }

      if (!result.success) {
        setError(result.error);
      }
    } catch (err) {
      setError('An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold text-gray-900">
            {isLogin ? 'Sign In' : 'Create Account'}
          </CardTitle>
          <p className="text-gray-600 mt-2">
            {isLogin 
              ? 'Access the SDOH Annotation Tool' 
              : 'Join the annotation team'
            }
          </p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <div className="space-y-2">
                <Label htmlFor="fullName">Full Name</Label>
                <Input
                  id="fullName"
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  required
                  placeholder="Enter your full name"
                />
              </div>
            )}
            
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="Enter your email"
              />
            </div>
            
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="Enter your password"
              />
            </div>

            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Please wait...' : (isLogin ? 'Sign In' : 'Create Account')}
            </Button>

            <div className="text-center">
              <button
                type="button"
                onClick={() => {
                  setIsLogin(!isLogin);
                  setError('');
                }}
                className="text-sm text-blue-600 hover:text-blue-800 underline"
              >
                {isLogin 
                  ? "Don't have an account? Sign up" 
                  : "Already have an account? Sign in"
                }
              </button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

const Dashboard = () => {
  const { user } = useAuth();
  const [documents, setDocuments] = useState([]);
  const [analytics, setAnalytics] = useState({});
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [sentences, setSentences] = useState([]);
  const [currentSentenceIndex, setCurrentSentenceIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [activeTab, setActiveTab] = useState(user?.role === 'admin' ? 'manage' : 'documents');
  const [tagStructure, setTagStructure] = useState({});
  const [projectName, setProjectName] = useState('');
  const [projectDescription, setProjectDescription] = useState('');

  useEffect(() => {
    fetchDocuments();
    fetchAnalytics();
    fetchTagStructure();
  }, []);

  const fetchDocuments = async () => {
    try {
      const response = await axios.get(`${API}/documents`);
      setDocuments(response.data);
    } catch (error) {
      console.error('Error fetching documents:', error);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const response = await axios.get(`${API}/analytics/overview`);
      setAnalytics(response.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
    }
  };

  const fetchTagStructure = async () => {
    try {
      const response = await axios.get(`${API}/tag-structure`);
      setTagStructure(response.data.tag_structure);
    } catch (error) {
      console.error('Error fetching tag structure:', error);
    }
  };

  const handleFileUpload = async () => {
    if (!uploadFile) return;

    setLoading(true);
    const formData = new FormData();
    formData.append('file', uploadFile);
    if (projectName) formData.append('project_name', projectName);
    if (projectDescription) formData.append('description', projectDescription);

    try {
      await axios.post(`${API}/documents/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      setUploadFile(null);
      setProjectName('');
      setProjectDescription('');
      fetchDocuments();
      fetchAnalytics();
    } catch (error) {
      console.error('Error uploading file:', error);
      alert('Error uploading file. ' + (error.response?.data?.detail || 'Please try again.'));
    } finally {
      setLoading(false);
    }
  };

  const loadDocumentSentences = async (documentId) => {
    try {
      const response = await axios.get(`${API}/documents/${documentId}/sentences`);
      setSentences(response.data);
      setSelectedDocument(documentId);
      setCurrentSentenceIndex(0);
      
      // Switch to annotate tab
      setActiveTab('annotate');
    } catch (error) {
      console.error('Error loading sentences:', error);
      alert('Error loading sentences: ' + (error.response?.data?.detail || 'Please try again.'));
    }
  };

  const createAnnotation = async (sentenceId, tags, notes, skipped = false) => {
    try {
      // Handle annotation completion signal
      if (sentenceId === 'ANNOTATION_COMPLETE') {
        setActiveTab('documents');
        return;
      }

      await axios.post(`${API}/annotations`, {
        sentence_id: sentenceId,
        tags: tags,
        notes: notes,
        skipped: skipped
      });
      
      // Refresh sentences to show new annotation
      if (selectedDocument) {
        loadDocumentSentences(selectedDocument);
      }
      
      // Refresh analytics
      fetchAnalytics();
    } catch (error) {
      console.error('Error creating annotation:', error);
      alert('Error saving annotation: ' + (error.response?.data?.detail || 'Please try again.'));
    }
  };

  const deleteDocument = async (documentId) => {
    if (!window.confirm('Are you sure you want to delete this document? This will also delete all associated annotations.')) {
      return;
    }

    try {
      await axios.delete(`${API}/admin/documents/${documentId}`);
      fetchDocuments();
      fetchAnalytics();
    } catch (error) {
      console.error('Error deleting document:', error);
      alert('Error deleting document: ' + (error.response?.data?.detail || 'Please try again.'));
    }
  };

  // Determine which tabs to show based on user role
  const getTabsForUser = () => {
    if (user?.role === 'admin') {
      return [
        { value: 'manage', label: 'Manage', icon: Settings },
        { value: 'upload', label: 'Upload', icon: Upload },
        { value: 'documents', label: 'Documents', icon: FileText },
        { value: 'annotate', label: 'Annotate', icon: Tag },
        { value: 'analytics', label: 'Analytics', icon: BarChart3 }
      ];
    } else {
      return [
        { value: 'documents', label: 'Documents', icon: FileText },
        { value: 'annotate', label: 'Annotate', icon: Tag },
        { value: 'analytics', label: 'Analytics', icon: BarChart3 }
      ];
    }
  };

  const tabsToShow = getTabsForUser();

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="inline-flex h-12 items-center justify-start rounded-lg bg-gray-100 p-1 text-gray-500 w-auto">
          {tabsToShow.map((tab) => (
            <TabsTrigger 
              key={tab.value} 
              value={tab.value} 
              className="inline-flex items-center justify-center whitespace-nowrap rounded-md px-4 py-2 text-sm font-medium ring-offset-white transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 data-[state=active]:bg-white data-[state=active]:text-gray-900 data-[state=active]:shadow-sm hover:bg-white/60 space-x-2"
            >
              <tab.icon className="h-4 w-4" />
              <span>{tab.label}</span>
            </TabsTrigger>
          ))}
        </TabsList>

        {/* Admin Management Tab */}
        {user?.role === 'admin' && (
          <TabsContent value="manage" className="space-y-4">
            <AdminManagementPanel />
          </TabsContent>
        )}

        {/* Admin Upload Tab */}
        {user?.role === 'admin' && (
          <TabsContent value="upload" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Upload CSV Document</CardTitle>
                <p className="text-sm text-gray-600">
                  Upload a CSV file containing discharge summaries for annotation by the team
                </p>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="projectName">Project Name (Optional)</Label>
                  <Input
                    id="projectName"
                    type="text"
                    value={projectName}
                    onChange={(e) => setProjectName(e.target.value)}
                    placeholder="e.g., Hospital XYZ Discharge Analysis"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="projectDescription">Description (Optional)</Label>
                  <Textarea
                    id="projectDescription"
                    value={projectDescription}
                    onChange={(e) => setProjectDescription(e.target.value)}
                    placeholder="Brief description of the annotation project..."
                    rows={3}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="csvFile">Select CSV File</Label>
                  <Input
                    id="csvFile"
                    type="file"
                    accept=".csv"
                    onChange={(e) => setUploadFile(e.target.files[0])}
                  />
                </div>
                
                <Button 
                  onClick={handleFileUpload}
                  disabled={!uploadFile || loading}
                  className="w-full"
                >
                  {loading ? 'Uploading...' : 'Upload Document for Team Annotation'}
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
        )}

        <TabsContent value="annotate" className="space-y-4">
          {!selectedDocument ? (
            <Card>
              <CardContent className="text-center py-8">
                <Tag className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 mb-2">
                  Select a document from the Documents tab to start annotating
                </p>
                <Button 
                  variant="outline"
                  onClick={() => setActiveTab('documents')}
                >
                  Browse Documents
                </Button>
              </CardContent>
            </Card>
          ) : sentences.length === 0 ? (
            <Card>
              <CardContent className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="text-gray-600">
                  Loading sentences for annotation...
                </p>
              </CardContent>
            </Card>
          ) : (
            <StructuredAnnotationInterface 
              sentences={sentences}
              currentIndex={currentSentenceIndex}
              onIndexChange={setCurrentSentenceIndex}
              tagStructure={tagStructure}
              onAnnotate={createAnnotation}
            />
          )}
        </TabsContent>

        <TabsContent value="documents" className="space-y-4">
          <div className="grid gap-4">
            {documents.map((doc) => (
              <Card key={doc.id} className="cursor-pointer hover:shadow-md transition-shadow">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        <h3 className="font-medium">{doc.filename}</h3>
                        {doc.project_name && (
                          <Badge variant="outline">{doc.project_name}</Badge>
                        )}
                      </div>
                      <p className="text-sm text-gray-600">
                        {doc.total_sentences} sentences • Uploaded {new Date(doc.upload_date).toLocaleDateString()}
                      </p>
                      {doc.description && (
                        <p className="text-xs text-gray-500 mt-1">{doc.description}</p>
                      )}
                    </div>
                    <div className="flex items-center space-x-2">
                      <Button
                        onClick={() => loadDocumentSentences(doc.id)}
                        variant="outline"
                      >
                        Annotate
                      </Button>
                      {user?.role === 'admin' && (
                        <Button
                          onClick={() => deleteDocument(doc.id)}
                          variant="destructive"
                          size="sm"
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-2">
                  <FileText className="h-5 w-5 text-blue-600" />
                  <div>
                    <p className="text-sm text-gray-600">Documents</p>
                    <p className="text-2xl font-semibold">{analytics.total_documents || 0}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-2">
                  <Tag className="h-5 w-5 text-green-600" />
                  <div>
                    <p className="text-sm text-gray-600">Sentences</p>
                    <p className="text-2xl font-semibold">{analytics.total_sentences || 0}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-5 w-5 text-purple-600" />
                  <div>
                    <p className="text-sm text-gray-600">Annotations</p>
                    <p className="text-2xl font-semibold">{analytics.total_annotations || 0}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-2">
                  <Tag className="h-5 w-5 text-emerald-600" />
                  <div>
                    <p className="text-sm text-gray-600">Tagged Sentences</p>
                    <p className="text-2xl font-semibold">{analytics.tagged_sentences || 0}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-2">
                  <SkipForward className="h-5 w-5 text-orange-600" />
                  <div>
                    <p className="text-sm text-gray-600">Skipped Sentences</p>
                    <p className="text-2xl font-semibold">{analytics.skipped_sentences || 0}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-2">
                  <Users className="h-5 w-5 text-indigo-600" />
                  <div>
                    <p className="text-sm text-gray-600">Annotators</p>
                    <p className="text-2xl font-semibold">{analytics.unique_annotators || 0}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
};

const AdminManagementPanel = () => {
  const { user: currentUser } = useAuth(); // Get current user context
  const [users, setUsers] = useState([]);
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [loading, setLoading] = useState(false);
  const [deletingUserId, setDeletingUserId] = useState(null);
  const [newUser, setNewUser] = useState({
    email: '',
    password: '',
    full_name: '',
    role: 'annotator'
  });

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      console.log('Fetching users from API...');
      const response = await axios.get(`${API}/admin/users`);
      console.log('Received users from API:', response.data.length, 'users');
      console.log('User list:', response.data.map(u => ({ id: u.id, name: u.full_name, email: u.email })));
      
      setUsers(response.data);
      console.log('State updated with new user list');
      
    } catch (error) {
      console.error('Error fetching users:', error);
      alert('Error fetching users: ' + (error.response?.data?.detail || 'Please try again.'));
    }
  };

  const createUser = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/admin/users`, newUser);
      setNewUser({ email: '', password: '', full_name: '', role: 'annotator' });
      setShowCreateUser(false);
      fetchUsers();
    } catch (error) {
      console.error('Error creating user:', error);
      alert('Error creating user: ' + (error.response?.data?.detail || 'Please try again.'));
    } finally {
      setLoading(false);
    }
  };

  const toggleUserStatus = async (userId, currentStatus) => {
    try {
      await axios.put(`${API}/admin/users/${userId}`, {
        is_active: !currentStatus
      });
      fetchUsers();
    } catch (error) {
      console.error('Error updating user status:', error);
    }
  };

  const deleteUser = async (userId, userName) => {
    console.log('Starting deletion process for:', { userId, userName });
    
    // Prevent deleting yourself
    if (userId === currentUser?.id) {
      alert("You cannot delete your own account!");
      return;
    }
    
    // Enhanced confirmation dialog
    const confirmed = window.confirm(
      `Are you sure you want to delete the user "${userName}"?\n\n` +
      'This will permanently remove:\n' +
      '• The user account\n' +
      '• All their annotations\n' +
      '• Their login access\n\n' +
      'This action cannot be undone!'
    );

    if (!confirmed) {
      console.log('User cancelled deletion');
      return;
    }

    try {
      console.log('User confirmed deletion, proceeding...');
      
      // Set loading state
      setDeletingUserId(userId);
      
      console.log('Making DELETE request to:', `${API}/admin/users/${userId}`);
      
      // Make the delete request
      const response = await axios.delete(`${API}/admin/users/${userId}`);
      console.log('Delete response:', response.status, response.data);
      
      // Immediately remove the user from the UI state (optimistic update)
      console.log('Optimistically removing user from UI...');
      setUsers(prevUsers => {
        const updatedUsers = prevUsers.filter(user => user.id !== userId);
        console.log(`Removed user from state. User count: ${prevUsers.length} -> ${updatedUsers.length}`);
        return updatedUsers;
      });
      
      // Show success message
      alert(`User "${userName}" deleted successfully!`);
      
      // Also refresh from server to ensure consistency (but don't wait for it)
      fetchUsers().catch(error => {
        console.error('Error refreshing user list after deletion:', error);
      });
      
    } catch (error) {
      console.error('Error during deletion:', error);
      console.error('Error response:', error.response);
      const errorMessage = error.response?.data?.detail || 'Failed to delete user. Please try again.';
      alert('Error deleting user: ' + errorMessage);
      
      // Refresh the list in case of error to ensure accuracy
      await fetchUsers();
    } finally {
      console.log('Cleaning up loading state');
      setDeletingUserId(null);
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>User Management</CardTitle>
            <div className="flex items-center space-x-2">
              <Button 
                variant="outline" 
                size="sm"
                onClick={fetchUsers}
                disabled={loading}
              >
                {loading ? (
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>
                ) : (
                  'Refresh'
                )}
              </Button>
              <Button onClick={() => setShowCreateUser(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Add User
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {users.map((user) => (
              <div key={user.id} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className="flex items-center space-x-2">
                    {user.role === 'admin' && <Shield className="h-4 w-4 text-purple-600" />}
                    <User className="h-4 w-4 text-gray-500" />
                  </div>
                  <div>
                    <p className="font-medium">{user.full_name}</p>
                    <p className="text-sm text-gray-600">{user.email}</p>
                    <div className="flex items-center space-x-2 mt-1">
                      <Badge variant={user.role === 'admin' ? 'default' : 'secondary'}>
                        {user.role}
                      </Badge>
                      <Badge variant={user.is_active ? 'outline' : 'destructive'}>
                        {user.is_active ? 'Active' : 'Inactive'}
                      </Badge>
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => toggleUserStatus(user.id, user.is_active)}
                    disabled={loading}
                  >
                    {user.is_active ? 'Deactivate' : 'Activate'}
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={(e) => {
                      console.log('Delete button clicked!', { userId: user.id, userName: user.full_name }); // Debug log
                      e.preventDefault();
                      e.stopPropagation();
                      deleteUser(user.id, user.full_name);
                    }}
                    disabled={deletingUserId === user.id}
                  >
                    {deletingUserId === user.id ? (
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    ) : (
                      <Trash2 className="h-4 w-4" />
                    )}
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {showCreateUser && (
        <Dialog open={showCreateUser} onOpenChange={setShowCreateUser}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create New User</DialogTitle>
              <DialogDescription>
                Add a new annotator or administrator to the system
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              <div className="space-y-2">
                <Label>Full Name</Label>
                <Input
                  value={newUser.full_name}
                  onChange={(e) => setNewUser({ ...newUser, full_name: e.target.value })}
                  placeholder="Enter full name"
                />
              </div>
              <div className="space-y-2">
                <Label>Email</Label>
                <Input
                  type="email"
                  value={newUser.email}
                  onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                  placeholder="Enter email address"
                />
              </div>
              <div className="space-y-2">
                <Label>Password</Label>
                <Input
                  type="password"
                  value={newUser.password}
                  onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                  placeholder="Enter password"
                />
              </div>
              <div className="space-y-2">
                <Label>Role</Label>
                <Select value={newUser.role} onValueChange={(value) => setNewUser({ ...newUser, role: value })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="annotator">Annotator</SelectItem>
                    <SelectItem value="admin">Administrator</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => setShowCreateUser(false)}>
                  Cancel
                </Button>
                <Button onClick={createUser} disabled={loading}>
                  {loading ? 'Creating...' : 'Create User'}
                </Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
};

const StructuredAnnotationInterface = ({ sentences, currentIndex, onIndexChange, tagStructure, onAnnotate }) => {
  const [selectedTags, setSelectedTags] = useState([]);
  const [notes, setNotes] = useState('');
  
  const currentSentence = sentences[currentIndex];
  
  // Reset form when sentence changes
  useEffect(() => {
    setSelectedTags([]);
    setNotes('');
    // Scroll to top when sentence changes
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [currentIndex]);
  
  if (!currentSentence) return null;

  const addTag = (domain, category, tag) => {
    const newTag = {
      domain,
      category,
      tag,
      valence: 'positive' // Default valence
    };
    
    // Check if tag already exists
    const exists = selectedTags.some(t => 
      t.domain === domain && t.category === category && t.tag === tag
    );
    
    if (!exists) {
      setSelectedTags([...selectedTags, newTag]);
    }
  };

  const removeTag = (index) => {
    const newTags = [...selectedTags];
    newTags.splice(index, 1);
    setSelectedTags(newTags);
  };

  const updateTagValence = (index, valence) => {
    const newTags = [...selectedTags];
    newTags[index].valence = valence;
    setSelectedTags(newTags);
  };

  const handleSaveAnnotation = async () => {
    if (selectedTags.length === 0) return;
    
    await onAnnotate(currentSentence.id, selectedTags, notes);
    
    // Reset form
    setSelectedTags([]);
    setNotes('');
    
    // Move to next sentence or return to documents if this was the last sentence
    if (currentIndex < sentences.length - 1) {
      onIndexChange(currentIndex + 1);
    } else {
      // Last sentence - return to documents tab
      alert('Annotation complete! Returning to documents list.');
      // This will be handled in the parent component
      onAnnotate('ANNOTATION_COMPLETE', [], '', false);
    }
  };

  const handleSkip = async () => {
    await onAnnotate(currentSentence.id, [], notes, true);
    
    // Reset form
    setSelectedTags([]);
    setNotes('');
    
    // Move to next sentence or return to documents if this was the last sentence
    if (currentIndex < sentences.length - 1) {
      onIndexChange(currentIndex + 1);
    } else {
      // Last sentence - return to documents tab
      alert('Annotation complete! Returning to documents list.');
      // This will be handled in the parent component
      onAnnotate('ANNOTATION_COMPLETE', [], '', false);
    }
  };

  const progress = ((currentIndex + 1) / sentences.length) * 100;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Sentence Annotation</CardTitle>
            <Badge variant="secondary">
              {currentIndex + 1} of {sentences.length}
            </Badge>
          </div>
          <Progress value={progress} className="w-full" />
        </CardHeader>
        
        <CardContent className="space-y-6">
          {/* Current Sentence */}
          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-lg leading-relaxed">{currentSentence.text}</p>
          </div>

          {/* Existing Annotations */}
          {currentSentence.annotations && currentSentence.annotations.length > 0 && (
            <div className="space-y-2">
              <h4 className="font-medium text-gray-900">Existing Annotations:</h4>
              <div className="space-y-2">
                {currentSentence.annotations.map((annotation, idx) => (
                  <div key={idx} className="p-3 bg-blue-50 rounded-md">
                    {annotation.skipped ? (
                      <div className="flex items-center space-x-2">
                        <SkipForward className="h-4 w-4 text-orange-600" />
                        <span className="text-sm text-gray-600">
                          Skipped by User {annotation.user_id.slice(-6)}
                        </span>
                      </div>
                    ) : (
                      <div>
                        <div className="flex items-center space-x-2 mb-1">
                          <span className="text-sm text-gray-600">
                            by User {annotation.user_id.slice(-6)}
                          </span>
                        </div>
                        <div className="flex flex-wrap gap-1 mb-2">
                          {annotation.tags.map((tag, tagIdx) => (
                            <Badge 
                              key={tagIdx} 
                              variant={tag.valence === 'positive' ? 'default' : 'destructive'}
                              className="text-xs"
                            >
                              {tag.domain}: {tag.tag} ({tag.valence})
                            </Badge>
                          ))}
                        </div>
                        {annotation.notes && (
                          <p className="text-sm text-gray-600">
                            Notes: {annotation.notes}
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Selected Tags Display */}
          {selectedTags.length > 0 && (
            <div className="space-y-2">
              <h4 className="font-medium text-gray-900">Selected Tags:</h4>
              <div className="space-y-2">
                {selectedTags.map((tag, index) => (
                  <div key={index} className="flex items-center space-x-2 p-2 bg-green-50 rounded">
                    <Badge variant="outline">
                      {tag.domain}: {tag.category} - {tag.tag}
                    </Badge>
                    <Select value={tag.valence} onValueChange={(value) => updateTagValence(index, value)}>
                      <SelectTrigger className="w-32">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="positive">Positive</SelectItem>
                        <SelectItem value="negative">Negative</SelectItem>
                      </SelectContent>
                    </Select>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => removeTag(index)}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Tag Selection Interface */}
          <div className="space-y-4 border-t pt-4">
            <h4 className="font-medium text-gray-900">Add Tags:</h4>
            
            {Object.entries(tagStructure).map(([domain, categories]) => (
              <div key={domain} className="space-y-2">
                <h5 className="text-sm font-medium text-blue-700">{domain}</h5>
                <div className="grid gap-2">
                  {Object.entries(categories).map(([category, tags]) => (
                    <div key={category} className="space-y-1">
                      <h6 className="text-xs font-medium text-gray-600">{category}</h6>
                      <div className="flex flex-wrap gap-1">
                        {tags.map((tag) => (
                          <Button
                            key={tag}
                            size="sm"
                            variant="outline"
                            onClick={() => addTag(domain, category, tag)}
                            className="text-xs h-6 px-2"
                          >
                            <Plus className="h-3 w-3 mr-1" />
                            {tag}
                          </Button>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
                <Separator />
              </div>
            ))}
          </div>

          {/* Notes */}
          <div className="space-y-2">
            <Label>Notes (optional)</Label>
            <Textarea
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Additional context or observations..."
              rows={3}
            />
          </div>

          {/* Action Buttons */}
          <div className="flex space-x-2">
            <Button
              onClick={handleSaveAnnotation}
              disabled={selectedTags.length === 0}
              className="bg-green-600 hover:bg-green-700"
            >
              <CheckCircle className="h-4 w-4 mr-2" />
              Save Annotation
            </Button>
            
            <Button
              onClick={handleSkip}
              variant="outline"
              className="border-orange-300 text-orange-700 hover:bg-orange-50"
            >
              <SkipForward className="h-4 w-4 mr-2" />
              Skip - No SDOH Content
            </Button>
            
            <Button
              variant="outline"
              onClick={() => {
                setSelectedTags([]);
                setNotes('');
                onIndexChange(Math.max(0, currentIndex - 1));
              }}
              disabled={currentIndex === 0}
            >
              Previous
            </Button>
            
            <Button
              variant="outline"
              onClick={() => {
                setSelectedTags([]);
                setNotes('');
                onIndexChange(Math.min(sentences.length - 1, currentIndex + 1));
              }}
              disabled={currentIndex === sentences.length - 1}
            >
              Next
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Main App Component
function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <div className="min-h-screen bg-gray-50">
          <AuthenticatedApp />
        </div>
      </BrowserRouter>
    </AuthProvider>
  );
}

const AuthenticatedApp = () => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  if (!user) {
    return <AuthForm />;
  }

  return (
    <>
      <Header />
      <main>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </main>
    </>
  );
};

export default App;