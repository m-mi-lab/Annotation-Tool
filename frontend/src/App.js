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
import { FileText, Users, BarChart3, Upload, User, LogOut, Tag, CheckCircle } from "lucide-react";

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

  const register = async (email, password, fullName) => {
    try {
      await axios.post(`${API}/auth/register`, {
        email,
        password,
        full_name: fullName
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
                <User className="h-4 w-4 text-gray-500" />
                <span className="text-sm text-gray-700">{user.full_name}</span>
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
  const [documents, setDocuments] = useState([]);
  const [analytics, setAnalytics] = useState({});
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [sentences, setSentences] = useState([]);
  const [currentSentenceIndex, setCurrentSentenceIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [activeTab, setActiveTab] = useState('upload');
  const [domains] = useState([
    "Economic Stability",
    "Education Access and Quality", 
    "Health Care Access and Quality",
    "Neighborhood and Built Environment",
    "Social and Community Context"
  ]);

  useEffect(() => {
    fetchDocuments();
    fetchAnalytics();
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

  const handleFileUpload = async () => {
    if (!uploadFile) return;

    setLoading(true);
    const formData = new FormData();
    formData.append('file', uploadFile);

    try {
      await axios.post(`${API}/documents/upload`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      
      setUploadFile(null);
      fetchDocuments();
      fetchAnalytics();
    } catch (error) {
      console.error('Error uploading file:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAnnotateClick = (documentId) => {
    loadDocumentSentences(documentId);
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
    }
  };

  const createAnnotation = async (sentenceId, domain, tags, notes) => {
    try {
      await axios.post(`${API}/annotations`, {
        sentence_id: sentenceId,
        domain,
        tags,
        notes
      });
      
      // Refresh sentences to show new annotation
      if (selectedDocument) {
        loadDocumentSentences(selectedDocument);
      }
    } catch (error) {
      console.error('Error creating annotation:', error);
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="upload" className="flex items-center space-x-2">
            <Upload className="h-4 w-4" />
            <span>Upload</span>
          </TabsTrigger>
          <TabsTrigger value="annotate" className="flex items-center space-x-2">
            <Tag className="h-4 w-4" />
            <span>Annotate</span>
          </TabsTrigger>
          <TabsTrigger value="documents" className="flex items-center space-x-2">
            <FileText className="h-4 w-4" />
            <span>Documents</span>
          </TabsTrigger>
          <TabsTrigger value="analytics" className="flex items-center space-x-2">
            <BarChart3 className="h-4 w-4" />
            <span>Analytics</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="upload" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Upload CSV Document</CardTitle>
              <p className="text-sm text-gray-600">
                Upload a CSV file containing discharge summaries for annotation
              </p>
            </CardHeader>
            <CardContent className="space-y-4">
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
                {loading ? 'Uploading...' : 'Upload Document'}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="annotate" className="space-y-4">
          {(() => {
            console.log('Annotate tab state:', { selectedDocument, sentencesLength: sentences.length });
            
            if (!selectedDocument) {
              return (
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
              );
            } else if (sentences.length === 0) {
              return (
                <Card>
                  <CardContent className="text-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">
                      Loading sentences for annotation...
                    </p>
                  </CardContent>
                </Card>
              );
            } else {
              return (
                <AnnotationInterface 
                  sentences={sentences}
                  currentIndex={currentSentenceIndex}
                  onIndexChange={setCurrentSentenceIndex}
                  domains={domains}
                  onAnnotate={createAnnotation}
                />
              );
            }
          })()}
        </TabsContent>

        <TabsContent value="documents" className="space-y-4">
          <div className="grid gap-4">
            {(() => {
              console.log('Rendering documents tab, documents:', documents.length);
              return documents.map((doc, index) => {
                console.log(`Rendering document ${index}:`, doc);
                return (
                  <Card key={doc.id} className="cursor-pointer hover:shadow-md transition-shadow">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="font-medium">{doc.filename}</h3>
                          <p className="text-sm text-gray-600">
                            {doc.total_sentences} sentences • Uploaded {new Date(doc.upload_date).toLocaleDateString()}
                          </p>
                        </div>
                        <Button
                          onClick={() => handleAnnotateClick(doc.id)}
                          variant="outline"
                        >
                          Annotate
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                );
              });
            })()}
          </div>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
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
            
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-2">
                  <Users className="h-5 w-5 text-orange-600" />
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

const AnnotationInterface = ({ sentences, currentIndex, onIndexChange, domains, onAnnotate }) => {
  const [selectedDomain, setSelectedDomain] = useState('');
  const [tags, setTags] = useState('');
  const [notes, setNotes] = useState('');
  
  console.log('AnnotationInterface props:', { sentences: sentences?.length, currentIndex, selectedDomain });
  
  const currentSentence = sentences[currentIndex];
  console.log('Current sentence:', currentSentence);
  
  if (!currentSentence) return null;

  const handleAnnotate = async () => {
    if (!selectedDomain || !tags.trim()) return;
    
    const tagList = tags.split(',').map(tag => tag.trim()).filter(tag => tag);
    await onAnnotate(currentSentence.id, selectedDomain, tagList, notes);
    
    // Reset form and move to next sentence
    setSelectedDomain('');
    setTags('');
    setNotes('');
    
    if (currentIndex < sentences.length - 1) {
      onIndexChange(currentIndex + 1);
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
                    <div className="flex items-center space-x-2 mb-1">
                      <Badge variant="outline">{annotation.domain}</Badge>
                      <span className="text-sm text-gray-600">
                        by User {annotation.user_id.slice(-6)}
                      </span>
                    </div>
                    <p className="text-sm">
                      Tags: {annotation.tags.join(', ')}
                    </p>
                    {annotation.notes && (
                      <p className="text-sm text-gray-600 mt-1">
                        Notes: {annotation.notes}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Annotation Form */}
          <div className="space-y-4 border-t pt-4">
            <h4 className="font-medium text-gray-900">Add New Annotation:</h4>
            
            <div className="space-y-2">
              <Label>Social Determinant Domain</Label>
              <select
                value={selectedDomain}
                onChange={(e) => setSelectedDomain(e.target.value)}
                className="w-full p-2 border rounded-md"
              >
                <option value="">Select a domain...</option>
                {domains.map((domain) => (
                  <option key={domain} value={domain}>{domain}</option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <Label>Tags (comma-separated)</Label>
              <Input
                value={tags}
                onChange={(e) => setTags(e.target.value)}
                placeholder="e.g., housing instability, financial stress"
              />
            </div>

            <div className="space-y-2">
              <Label>Notes (optional)</Label>
              <Textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Additional context or observations..."
                rows={3}
              />
            </div>

            <div className="flex space-x-2">
              <Button
                onClick={handleAnnotate}
                disabled={!selectedDomain || !tags.trim()}
              >
                Save Annotation
              </Button>
              
              <Button
                variant="outline"
                onClick={() => onIndexChange(Math.max(0, currentIndex - 1))}
                disabled={currentIndex === 0}
              >
                Previous
              </Button>
              
              <Button
                variant="outline"
                onClick={() => onIndexChange(Math.min(sentences.length - 1, currentIndex + 1))}
                disabled={currentIndex === sentences.length - 1}
              >
                Next
              </Button>
            </div>
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