import React, { useState, useEffect, useContext, createContext } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from "react-router-dom";
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
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "./components/ui/dialog";
import { FileText, Users, BarChart3, Upload, User, LogOut, Tag, CheckCircle, Plus, X, SkipForward, Shield, Settings, Trash2, Download } from "lucide-react";

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
      await axios.post(`${API}/auth/register`, { email, password, full_name: fullName, role });
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

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within an AuthProvider');
  return context;
};

// Header
const Header = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  return (
    <header className="bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <button type="button" onClick={() => navigate('/home')} className="flex items-center space-x-3 hover:opacity-80">
            <FileText className="h-8 w-8 text-blue-600" />
            <h1 className="text-xl font-semibold text-gray-900">SDOH Annotation Tool</h1>
          </button>
          {user && (
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                {user.role === 'admin' && <Shield className="h-4 w-4 text-purple-600" title="Administrator" />} 
                <User className="h-4 w-4 text-gray-500" />
                <span className="text-sm text-gray-700">{user.full_name}</span>
                <Badge variant={user.role === 'admin' ? 'default' : 'secondary'}>{user.role}</Badge>
              </div>
              <Button variant="ghost" size="sm" onClick={logout} className="flex items-center space-x-1">
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

// Auth Form
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
      const result = isLogin ? await login(email, password) : await register(email, password, fullName);
      if (!result.success) setError(result.error);
    } catch {
      setError('An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold text-gray-900">{isLogin ? 'Sign In' : 'Create Account'}</CardTitle>
          <p className="text-gray-600 mt-2">{isLogin ? 'Access the SDOH Annotation Tool' : 'Join the annotation team'}</p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <div className="space-y-2">
                <Label htmlFor="fullName">Full Name</Label>
                <Input id="fullName" type="text" value={fullName} onChange={(e) => setFullName(e.target.value)} required placeholder="Enter your full name" />
              </div>
            )}
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="Enter your email" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required placeholder="Enter your password" />
            </div>
            {error && (
              <Alert variant="destructive"><AlertDescription>{error}</AlertDescription></Alert>
            )}
            <Button type="submit" className="w-full" disabled={loading}>{loading ? 'Please wait...' : (isLogin ? 'Sign In' : 'Create Account')}</Button>
            <div className="text-center">
              <button type="button" onClick={() => { setIsLogin(!isLogin); setError(''); }} className="text-sm text-blue-600 hover:text-blue-800 underline">
                {isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
              </button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

// Home Page
const Home = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Welcome to the SDOH Annotation Tool</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            <Button variant="outline" onClick={() => navigate('/dashboard')}>Go to Dashboard</Button>
            <Button variant="outline" onClick={() => navigate('/dashboard#documents')}>Documents</Button>
            <Button variant="outline" onClick={() => navigate('/dashboard#annotate')}>Annotate</Button>
            <Button variant="outline" onClick={() => navigate('/dashboard#resources')}>Resources</Button>
            <Button variant="outline" onClick={() => navigate('/dashboard#analytics')}>Analytics</Button>
            {user?.role === 'admin' && (
              <Button variant="outline" onClick={() => navigate('/dashboard#manage')}>Admin Upload</Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Dashboard
const Dashboard = () => {
  const { user } = useAuth();
  const [documents, setDocuments] = useState([]);
  const [analytics, setAnalytics] = useState({});
  const [enhancedAnalytics, setEnhancedAnalytics] = useState({ per_user: [], sentences_left_overall: 0, irr_pairs: [] });
  const [tagPrevalence, setTagPrevalence] = useState({ domain_counts: {}, category_counts: {}, tag_counts: {}, valence_counts: {} });
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [sentences, setSentences] = useState([]);
  const [currentSentenceIndex, setCurrentSentenceIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [activeTab, setActiveTab] = useState(user?.role === 'admin' ? 'manage' : 'documents');
  const [tagStructure, setTagStructure] = useState({});
  const [projectName, setProjectName] = useState('');
  const [projectDescription, setProjectDescription] = useState('');

  const [resources, setResources] = useState([]);
  const [resourceFile, setResourceFile] = useState(null);

  // Bulk selection for docs
  const [selectedDocIds, setSelectedDocIds] = useState([]);
  const [selectAllDocs, setSelectAllDocs] = useState(false);

  // Document-level annotations manager
  const [manageAnnOpen, setManageAnnOpen] = useState(false);
  const [manageAnnDoc, setManageAnnDoc] = useState(null);
  const [docAnnotations, setDocAnnotations] = useState([]);
  const [selectedAnnIds, setSelectedAnnIds] = useState([]);
  const [selectAllAnns, setSelectAllAnns] = useState(false);

  useEffect(() => {
    fetchDocuments();
    fetchAnalytics();
    fetchTagStructure();
    fetchResources();
    fetchEnhancedAnalytics();
    fetchTagPrevalence();
    // eslint-disable-next-line
  }, []);

  const fetchDocuments = async () => {
    try {
      const response = await axios.get(`${API}/documents`);
      setDocuments(response.data);
      setSelectedDocIds([]);
      setSelectAllDocs(false);
    } catch (error) {
      console.error('Error fetching documents:', error);
    }
  };

  const fetchAnalytics = async () => {
    try {
      const response = await axios.get(`${API}/analytics/overview`);
      setAnalytics(response.data);
    } catch (error) { /* noop */ }
  };

  const fetchEnhancedAnalytics = async () => {
    try {
      const res = await axios.get(`${API}/analytics/enhanced`);
      setEnhancedAnalytics(res.data || { per_user: [], sentences_left_overall: 0, irr_pairs: [] });
    } catch (err) {
      console.error('Error fetching enhanced analytics', err);
    }
  };

  const fetchTagPrevalence = async () => {
    try {
      const res = await axios.get(`${API}/analytics/tag-prevalence`);
      setTagPrevalence(res.data || { domain_counts: {}, category_counts: {}, tag_counts: {}, valence_counts: {} });
    } catch (err) {
      console.error('Error fetching tag prevalence', err);
    }
  };

  const fetchTagStructure = async () => {
    try {
      const response = await axios.get(`${API}/tag-structure`);
      setTagStructure(response.data.tag_structure);
    } catch (error) { /* noop */ }
  };

  const fetchResources = async () => {
    try {
      const res = await axios.get(`${API}/resources`);
      setResources(res.data || []);
    } catch (err) { /* noop */ }
  };

  const handleFileUpload = async () => {
    if (!uploadFile) return;
    setLoading(true);
    const formData = new FormData();
    formData.append('file', uploadFile);
    if (projectName) formData.append('project_name', projectName);
    if (projectDescription) formData.append('description', projectDescription);
    try {
      await axios.post(`${API}/documents/upload`, formData, { headers: { 'Content-Type': 'multipart/form-data' } });
      setUploadFile(null); setProjectName(''); setProjectDescription('');
      fetchDocuments(); fetchAnalytics();
    } catch (error) {
      alert('Error uploading file. ' + (error.response?.data?.detail || 'Please try again.'));
    } finally { setLoading(false); }
  };

  const loadDocumentSentences = async (documentId) => {
    // If deep-linked via hash, ensure tab switches correctly
    if (window.location.hash === '#annotate') {
      setActiveTab('annotate');
    }
    try {
      const response = await axios.get(`${API}/documents/${documentId}/sentences`);
      setSentences(response.data);
      setSelectedDocument(documentId);
      setCurrentSentenceIndex(0);
      setActiveTab('annotate');
    } catch (error) {
      alert('Error loading sentences: ' + (error.response?.data?.detail || 'Please try again.'));
    }
  };

  const refreshSentenceAnnotations = async (sentenceId) => {
    try {
      const res = await axios.get(`${API}/annotations/sentence/${sentenceId}`);
      setSentences((prev) => prev.map((s) => (s.id === sentenceId ? { ...s, annotations: res.data } : s)));
    } catch (err) { /* noop */ }
  };

  const deleteAnnotation = async (annotationId, sentenceId) => {
    if (!window.confirm('Are you sure you want to delete this annotation?')) return;
    let previousSentences;
    setSentences((prev) => {
      previousSentences = prev;
      if (!sentenceId) return prev;
      return prev.map((s) => s.id !== sentenceId ? s : { ...s, annotations: (s.annotations || []).filter((a) => a.id !== annotationId) });
    });
    try {
      await axios.delete(`${API}/annotations/${annotationId}`);
      if (sentenceId) await refreshSentenceAnnotations(sentenceId);
      else if (selectedDocument) await loadDocumentSentences(selectedDocument);
      fetchAnalytics();
    } catch (error) {
      if (previousSentences) setSentences(previousSentences);
      alert('Error deleting annotation: ' + (error.response?.data?.detail || 'Please try again.'));
    }
  };

  const bulkDeleteAnnotations = async (annotationIds, sentenceId = null) => {
    if (!annotationIds || annotationIds.length === 0) return;
    if (!window.confirm(`Delete ${annotationIds.length} annotations?`)) return;
    try {
      await axios.post(`${API}/annotations/bulk-delete`, { annotation_ids: annotationIds });
      if (sentenceId) await refreshSentenceAnnotations(sentenceId);
      if (manageAnnOpen && manageAnnDoc) await openManageAnnotations(manageAnnDoc);
      fetchAnalytics();
    } catch (err) {
      alert('Error bulk-deleting annotations: ' + (err.response?.data?.detail || 'Please try again.'));
    }
  };

  const createAnnotation = async (sentenceId, tags, notes, skipped = false) => {
    try {
      if (sentenceId === 'ANNOTATION_COMPLETE') { setActiveTab('documents'); return; }
      await axios.post(`${API}/annotations`, { sentence_id: sentenceId, tags, notes, skipped });
      await refreshSentenceAnnotations(sentenceId);
      fetchAnalytics();
    } catch (error) {
      alert('Error saving annotation: ' + (error.response?.data?.detail || 'Please try again.'));
    }
  };

  const deleteDocument = async (documentId) => {
    if (!window.confirm('Are you sure you want to delete this document? This will also delete all associated annotations.')) return;
    try {
      setDocuments(documents.filter(doc => doc.id !== documentId));
      await axios.delete(`${API}/admin/documents/${documentId}`);
      fetchAnalytics();
    } catch (error) {
      alert('Document removed from list (API call failed but UI updated)');
    }
  };

  const downloadAnnotatedCsv = async (doc) => {
    try {
      const url = `${API}/admin/download/annotated-csv/${doc.id}`;
      const token = localStorage.getItem('token');
      const res = await fetch(url, { method: 'GET', headers: { Authorization: `Bearer ${token}` } });
      if (!res.ok) { throw new Error(await res.text() || `HTTP ${res.status}`); }
      const blob = await res.blob();
      if (!blob || blob.size === 0) { alert('No data available to download (empty CSV).'); return; }
      const filename = `annotated_${doc.filename || 'document'}.csv`;
      const link = document.createElement('a');
      const urlObj = window.URL.createObjectURL(blob);
      link.href = urlObj; link.setAttribute('download', filename);
      document.body.appendChild(link); link.click(); document.body.removeChild(link); window.URL.revokeObjectURL(urlObj);
    } catch (error) {
      alert('Error downloading CSV: ' + (error.message || 'Please try again.'));
    }
  };

  const uploadResource = async () => {
    if (!resourceFile) return;
    const form = new FormData(); form.append('file', resourceFile);
    try {
      await axios.post(`${API}/admin/resources/upload`, form, { headers: { 'Content-Type': 'multipart/form-data' } });
      setResourceFile(null); fetchResources();
    } catch (err) { alert('Error uploading resource: ' + (err.response?.data?.detail || 'Please try again.')); }
  };

  const downloadResource = async (resItem) => {
    try {
      const url = `${API}/resources/${resItem.id}/download`;
      const token = localStorage.getItem('token');
      const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
      if (!res.ok) throw new Error(await res.text() || `HTTP ${res.status}`);
      const blob = await res.blob();
      const filename = resItem.filename || 'resource';
      const link = document.createElement('a'); const urlObj = window.URL.createObjectURL(blob);
      link.href = urlObj; link.setAttribute('download', filename);
      document.body.appendChild(link); link.click(); document.body.removeChild(link); window.URL.revokeObjectURL(urlObj);
    } catch (err) { alert('Error downloading resource: ' + (err.message || 'Please try again.')); }
  };

  const deleteResource = async (resItem) => {
    if (!window.confirm(`Delete resource "${resItem.filename}"?`)) return;
    try { await axios.delete(`${API}/admin/resources/${resItem.id}`); fetchResources(); }
    catch (err) { alert('Error deleting resource: ' + (err.response?.data?.detail || 'Please try again.')); }
  };

  // Bulk docs selection
  const toggleSelectAllDocs = () => {
    if (selectAllDocs) { setSelectedDocIds([]); setSelectAllDocs(false); }
    else { setSelectedDocIds(documents.map(d => d.id)); setSelectAllDocs(true); }
  };
  const toggleDocChecked = (docId) => {
    setSelectedDocIds((prev) => prev.includes(docId) ? prev.filter(id => id !== docId) : [...prev, docId]);
  };
  const bulkDeleteDocuments = async () => {
    if (selectedDocIds.length === 0) return;
    if (!window.confirm(`Delete ${selectedDocIds.length} documents and all their sentences/annotations?`)) return;
    try {
      await axios.post(`${API}/admin/documents/bulk-delete`, { document_ids: selectedDocIds });
      setDocuments((prev) => prev.filter(d => !selectedDocIds.includes(d.id)));
      setSelectedDocIds([]); setSelectAllDocs(false); fetchAnalytics();
    } catch (err) { alert('Error bulk-deleting documents: ' + (err.response?.data?.detail || 'Please try again.')); }
  };

  // Manage annotations for a document
  const openManageAnnotations = async (doc) => {
    setManageAnnDoc(doc); setManageAnnOpen(true);
    try {
      const res = await axios.get(`${API}/documents/${doc.id}/annotations`);
      setDocAnnotations(res.data || []);
      setSelectedAnnIds([]); setSelectAllAnns(false);
    } catch (err) {
      alert('Error loading annotations: ' + (err.response?.data?.detail || 'Please try again.'));
    }
  };
  const toggleSelectAllAnns = () => {
    if (selectAllAnns) { setSelectedAnnIds([]); setSelectAllAnns(false); }
    else { setSelectedAnnIds(docAnnotations.map(a => a.id)); setSelectAllAnns(true); }
  };
  const toggleAnnChecked = (annId) => {
    setSelectedAnnIds((prev) => prev.includes(annId) ? prev.filter(id => id !== annId) : [...prev, annId]);
  };
  const bulkDeleteDocAnnotations = async () => {
    if (selectedAnnIds.length === 0) return;
    if (!window.confirm(`Delete ${selectedAnnIds.length} annotations from this document?`)) return;
    await bulkDeleteAnnotations(selectedAnnIds);
  };

  const tabsToShow = user?.role === 'admin'
    ? [
        { value: 'manage', label: 'Manage', icon: Settings },
        { value: 'upload', label: 'Upload', icon: Upload },
        { value: 'documents', label: 'Documents', icon: FileText },
        { value: 'annotate', label: 'Annotate', icon: Tag },
        { value: 'resources', label: 'Resources', icon: FileText },
        { value: 'analytics', label: 'Analytics', icon: BarChart3 }
      ]
    : [
        { value: 'documents', label: 'Documents', icon: FileText },
        { value: 'annotate', label: 'Annotate', icon: Tag },
        { value: 'resources', label: 'Resources', icon: FileText },
        { value: 'analytics', label: 'Analytics', icon: BarChart3 }
      ];

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="inline-flex h-12 items-center justify-start rounded-lg bg-gray-100 p-1 text-gray-500 w-auto">
          {tabsToShow.map((tab) => (
            <TabsTrigger key={tab.value} value={tab.value} className="inline-flex items-center whitespace-nowrap rounded-md px-4 py-2 text-sm font-medium data-[state=active]:bg-white data-[state=active]:text-gray-900 space-x-2">
              <tab.icon className="h-4 w-4" />
              <span>{tab.label}</span>
            </TabsTrigger>
          ))}
        </TabsList>

        {user?.role === 'admin' && (
          <TabsContent value="manage" className="space-y-4">
            <AdminManagementPanel />
          </TabsContent>
        )}

        {user?.role === 'admin' && (
          <TabsContent value="upload" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle>Upload CSV Document</CardTitle>
                <p className="text-sm text-gray-600">Upload a CSV file containing discharge summaries for annotation by the team</p>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="projectName">Project Name (Optional)</Label>
                  <Input id="projectName" type="text" value={projectName} onChange={(e) => setProjectName(e.target.value)} placeholder="e.g., Hospital XYZ Discharge Analysis" />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="projectDescription">Description (Optional)</Label>
                  <Textarea id="projectDescription" value={projectDescription} onChange={(e) => setProjectDescription(e.target.value)} placeholder="Brief description of the annotation project..." rows={3} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="csvFile">Select CSV File</Label>
                  <Input id="csvFile" type="file" accept=".csv" onChange={(e) => setUploadFile(e.target.files[0])} />
                </div>
                <Button onClick={handleFileUpload} disabled={!uploadFile || loading} className="w-full">{loading ? 'Uploading...' : 'Upload Document for Team Annotation'}</Button>
              </CardContent>
            </Card>
          </TabsContent>
        )}

        <TabsContent value="annotate" className="space-y-4">
          {!selectedDocument ? (
            <Card>
              <CardContent className="text-center py-8">
                <Tag className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600 mb-2">Select a document from the Documents tab to start annotating</p>
                <Button variant="outline" onClick={() => setActiveTab('documents')}>Browse Documents</Button>
              </CardContent>
            </Card>
          ) : sentences.length === 0 ? (
            <Card>
              <CardContent className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="text-gray-600">Loading sentences for annotation...</p>
              </CardContent>
            </Card>
          ) : (
            <StructuredAnnotationInterface
              sentences={sentences}
              currentIndex={currentSentenceIndex}
              onIndexChange={setCurrentSentenceIndex}
              tagStructure={tagStructure}
              onAnnotate={createAnnotation}
              onDeleteAnnotation={deleteAnnotation}
              onBulkDeleteAnnotations={bulkDeleteAnnotations}
            />
          )}
        </TabsContent>

        <TabsContent value="documents" className="space-y-4" id="documents">
          <div className="flex items-center justify-between">
            <CardTitle>Documents ({documents.length})</CardTitle>
            {user?.role === 'admin' && (
              <div className="flex items-center justify-between p-2 bg-gray-50 border rounded">
                <div className="flex items-center gap-2">
                  <Checkbox id="selectAllDocs" checked={selectAllDocs} onCheckedChange={toggleSelectAllDocs} />
                  <Label htmlFor="selectAllDocs">Select all</Label>
                  <Button variant="destructive" size="sm" onClick={bulkDeleteDocuments} disabled={selectedDocIds.length === 0}>Delete selected</Button>
                </div>
              </div>
            )}
          </div>
          <div className="grid gap-4">
            {documents.map((doc) => (
              <Card key={doc.id} className="cursor-pointer hover:shadow-md transition-shadow" id={`doc-${doc.id}`}> 
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        {user?.role === 'admin' && (
                          <Checkbox checked={selectedDocIds.includes(doc.id)} onCheckedChange={() => toggleDocChecked(doc.id)} />
                        )}
                        <h3 className="font-medium">{doc.filename}</h3>
                        {doc.project_name && (<Badge variant="outline">{doc.project_name}</Badge>)}
                      </div>
                      <p className="text-sm text-gray-600">{doc.total_sentences} sentences • Uploaded {new Date(doc.upload_date).toLocaleDateString()}</p>
                      {doc.description && (<p className="text-xs text-gray-500 mt-1">{doc.description}</p>)}
                    </div>
                    <div className="flex items-center space-x-2">
                      <Button onClick={() => loadDocumentSentences(doc.id)} variant="outline">Annotate</Button>
                      {user?.role === 'admin' && (
                        <>
                          <Button variant="secondary" size="sm" onClick={() => downloadAnnotatedCsv(doc)}>
                            <Download className="h-4 w-4 mr-1" /> CSV
                          </Button>
                          <Button variant="outline" size="sm" onClick={() => openManageAnnotations(doc)}>Manage Annotations</Button>
                          <Button onClick={() => deleteDocument(doc.id)} variant="destructive" size="sm">
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="resources" className="space-y-4" id="resources">
          {user?.role === 'admin' && (
            <Card>
              <CardHeader><CardTitle>Upload Annotation Guide / Resources</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                <Input type="file" accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx" onChange={(e) => setResourceFile(e.target.files[0])} />
                <Button onClick={uploadResource} disabled={!resourceFile}>Upload Resource</Button>
              </CardContent>
            </Card>
          )}
          <Card>
            <CardHeader><CardTitle>Available Resources</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              {resources.length === 0 ? (
                <p className="text-sm text-gray-600">No resources uploaded yet.</p>
              ) : (
                <div className="space-y-2">
                  {resources.map((r) => (
                    <div key={r.id} className="flex items-center justify-between p-3 border rounded-md">
                      <div>
                        <p className="font-medium">{r.filename}</p>
                        <p className="text-xs text-gray-500">Uploaded {new Date(r.uploaded_at).toLocaleString()}</p>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button variant="outline" size="sm" onClick={() => downloadResource(r)}>Download</Button>
                        {user?.role === 'admin' && (
                          <Button variant="destructive" size="sm" onClick={() => deleteResource(r)}>
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics" className="space-y-6" id="analytics">
          {/* Top-level counts */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card><CardContent className="p-4"><div className="flex items-center space-x-2"><FileText className="h-5 w-5 text-blue-600" /><div><p className="text-sm text-gray-600">Documents</p><p className="text-2xl font-semibold">{analytics.total_documents || 0}</p></div></div></CardContent></Card>
            <Card><CardContent className="p-4"><div className="flex items-center space-x-2"><Tag className="h-5 w-5 text-green-600" /><div><p className="text-sm text-gray-600">Sentences</p><p className="text-2xl font-semibold">{analytics.total_sentences || 0}</p></div></div></CardContent></Card>
            <Card><CardContent className="p-4"><div className="flex items-center space-x-2"><CheckCircle className="h-5 w-5 text-purple-600" /><div><p className="text-sm text-gray-600">Annotations</p><p className="text-2xl font-semibold">{analytics.total_annotations || 0}</p></div></div></CardContent></Card>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card><CardContent className="p-4"><div className="flex items-center space-x-2"><Tag className="h-5 w-5 text-emerald-600" /><div><p className="text-sm text-gray-600">Tagged Sentences</p><p className="text-2xl font-semibold">{analytics.tagged_sentences || 0}</p></div></div></CardContent></Card>
            <Card><CardContent className="p-4"><div className="flex items-center space-x-2"><SkipForward className="h-5 w-5 text-orange-600" /><div><p className="text-sm text-gray-600">Skipped Sentences</p><p className="text-2xl font-semibold">{analytics.skipped_sentences || 0}</p></div></div></CardContent></Card>
            <Card><CardContent className="p-4"><div className="flex items-center space-x-2"><Users className="h-5 w-5 text-indigo-600" /><div><p className="text-sm text-gray-600">Annotators</p><p className="text-2xl font-semibold">{analytics.unique_annotators || 0}</p></div></div></CardContent></Card>
          </div>

          {/* Per-user stats */}
          <Card>
            <CardHeader><CardTitle>Annotator Stats</CardTitle></CardHeader>
            <CardContent>
              <div className="overflow-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-gray-600">
                      <th className="p-2">Annotator</th>
                      <th className="p-2">Total</th>
                      <th className="p-2">Tagged</th>
                      <th className="p-2">Skipped</th>
                      <th className="p-2">Sentences Left</th>
                    </tr>
                  </thead>
                  <tbody>
                    {enhancedAnalytics.per_user?.map((u) => (
                      <tr key={u.user_id} className="border-t">
                        <td className="p-2">{u.full_name}</td>
                        <td className="p-2">{u.total}</td>
                        <td className="p-2">{u.tagged}</td>
                        <td className="p-2">{u.skipped}</td>
                        <td className="p-2">{u.sentences_left}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          {/* IRR */}
          <Card>
            <CardHeader><CardTitle>Inter-Rater Reliability (Pairwise Jaccard)</CardTitle></CardHeader>
            <CardContent>
              {enhancedAnalytics.irr_pairs?.length === 0 ? (
                <p className="text-sm text-gray-600">Not enough overlapping annotations to compute IRR yet.</p>
              ) : (
                <div className="overflow-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left text-gray-600">
                        <th className="p-2">Annotator 1</th>
                        <th className="p-2">Annotator 2</th>
                        <th className="p-2">Avg Jaccard</th>
                        <th className="p-2">Common Sentences</th>
                      </tr>
                    </thead>
                    <tbody>
                      {enhancedAnalytics.irr_pairs?.map((p, idx) => (
                        <tr key={idx} className="border-t">
                          <td className="p-2">{p.user1?.slice(-6)}</td>
                          <td className="p-2">{p.user2?.slice(-6)}</td>
                          <td className="p-2">{p.avg_jaccard === null ? '-' : p.avg_jaccard.toFixed(3)}</td>
                          <td className="p-2">{p.common_sentences}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Category counts and valence chart (simple) */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card>
              <CardHeader><CardTitle>Category Counts</CardTitle></CardHeader>
              <CardContent>
                <div className="max-h-[40vh] overflow-auto space-y-1 text-sm">
                  {Object.entries(tagPrevalence.category_counts || {}).map(([k, v]) => (
                    <div key={k} className="flex justify-between border-b py-1">
                      <span className="truncate pr-4">{k}</span>
                      <span className="font-medium">{v}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>Valence Distribution</CardTitle></CardHeader>
              <CardContent>
                <div className="flex items-center gap-6">
                  <div className="flex-1">
                    <div className="flex justify-between text-sm text-gray-600">
                      <span>Positive</span><span>{tagPrevalence.valence_counts?.positive || 0}</span>
                    </div>
                    <div className="h-2 bg-gray-200 rounded">
                      <div className="h-2 bg-green-500 rounded" style={{ width: `${Math.min(100, (tagPrevalence.valence_counts?.positive || 0) / Math.max(1, (tagPrevalence.valence_counts?.positive || 0) + (tagPrevalence.valence_counts?.negative || 0)) * 100)}%` }}></div>
                    </div>
                  </div>
                  <div className="flex-1">
                    <div className="flex justify-between text-sm text-gray-600">
                      <span>Negative</span><span>{tagPrevalence.valence_counts?.negative || 0}</span>
                    </div>
                    <div className="h-2 bg-gray-200 rounded">
                      <div className="h-2 bg-red-500 rounded" style={{ width: `${Math.min(100, (tagPrevalence.valence_counts?.negative || 0) / Math.max(1, (tagPrevalence.valence_counts?.positive || 0) + (tagPrevalence.valence_counts?.negative || 0)) * 100)}%` }}></div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* Document-level Annotations Manager */}
      <Dialog open={manageAnnOpen} onOpenChange={setManageAnnOpen}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>Manage Annotations {manageAnnDoc ? `for ${manageAnnDoc.filename}` : ''}</DialogTitle>
            <DialogDescription>Select annotations to delete from this document.</DialogDescription>
          </DialogHeader>
          <div className="flex items-center gap-3 mb-3">
            <Checkbox id="selectAllAnns" checked={selectAllAnns} onCheckedChange={toggleSelectAllAnns} />
            <Label htmlFor="selectAllAnns">Select all</Label>
            <Button variant="destructive" size="sm" disabled={selectedAnnIds.length === 0} onClick={bulkDeleteDocAnnotations}>Delete selected</Button>
          </div>
          <div className="max-h-[50vh] overflow-auto space-y-2">
            {docAnnotations.length === 0 ? (
              <p className="text-sm text-gray-600">No annotations found for this document.</p>
            ) : (
              docAnnotations.map((a) => (
                <div key={a.id} className="flex items-start justify-between p-3 border rounded-md">
                  <div className="flex-1 pr-2">
                    <div className="flex items-center gap-2 mb-1">
                      <Checkbox checked={selectedAnnIds.includes(a.id)} onCheckedChange={() => toggleAnnChecked(a.id)} />
                      <Badge variant="outline">{a.skipped ? 'Skipped' : 'Tagged'}</Badge>
                      <span className="text-xs text-gray-500">by {a.user_id?.slice(-6)}</span>
                    </div>
                    {!a.skipped && (
                      <div className="flex flex-wrap gap-1">
                        {(a.tags || []).map((t, idx) => (
                          <Badge key={idx} variant={t.valence === 'positive' ? 'default' : 'destructive'} className="text-xs">
                            {t.domain}: {t.tag} ({t.valence})
                          </Badge>
                        ))}
                      </div>
                    )}
                    {a.notes && <p className="text-xs text-gray-600 mt-1">Notes: {a.notes}</p>}
                  </div>
                  <div>
                    <Button size="sm" variant="destructive" onClick={() => bulkDeleteAnnotations([a.id])}><Trash2 className="h-4 w-4" /></Button>
                  </div>
                </div>
              ))
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// Admin panel with bulk user delete
const AdminManagementPanel = () => {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [loading, setLoading] = useState(false);
  const [deletingUserId, setDeletingUserId] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [newUser, setNewUser] = useState({ email: '', password: '', full_name: '', role: 'annotator' });
  const [selectedUserIds, setSelectedUserIds] = useState([]);
  const [selectAllUsers, setSelectAllUsers] = useState(false);

  useEffect(() => { fetchUsers(); }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/admin/users`);
      setUsers([...response.data]);
      setSelectedUserIds([]); setSelectAllUsers(false); setRefreshKey(Date.now());
    } catch (error) {
      alert('Error fetching users: ' + (error.response?.data?.detail || 'Please try again.'));
    } finally { setLoading(false); }
  };

  const createUser = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/admin/users`, newUser);
      setNewUser({ email: '', password: '', full_name: '', role: 'annotator' });
      setShowCreateUser(false); fetchUsers();
    } catch (error) {
      alert('Error creating user: ' + (error.response?.data?.detail || 'Please try again.'));
    } finally { setLoading(false); }
  };

  const toggleUserStatus = async (userId, currentStatus) => {
    try { await axios.put(`${API}/admin/users/${userId}`, { is_active: !currentStatus }); fetchUsers(); }
    catch (error) { /* noop */ }
  };

  const deleteUser = async (userId, userName) => {
    if (userId === currentUser?.id) { alert('You cannot delete your own account!'); return; }
    const confirmed = window.confirm(`Are you sure you want to delete the user "${userName}"?`);
    if (!confirmed) return;
    try {
      setUsers(users.filter(u => u.id !== userId)); setRefreshKey(Date.now());
      setDeletingUserId(userId);
      await axios.delete(`${API}/admin/users/${userId}`);
    } catch (error) {
      alert('User removed from list (API call failed but UI updated)');
    } finally { setDeletingUserId(null); }
  };

  const toggleSelectAllUsers = () => {
    if (selectAllUsers) { setSelectedUserIds([]); setSelectAllUsers(false); }
    else { setSelectedUserIds(users.map(u => u.id)); setSelectAllUsers(true); }
  };
  const toggleUserChecked = (uid) => { setSelectedUserIds((prev) => prev.includes(uid) ? prev.filter(id => id !== uid) : [...prev, uid]); };
  const bulkDeleteUsers = async () => {
    if (selectedUserIds.length === 0) return;
    const cleaned = selectedUserIds.filter(id => id !== currentUser?.id);
    const skipped = selectedUserIds.length - cleaned.length;
    const confirmed = window.confirm(`Delete ${cleaned.length} users?${skipped > 0 ? ` (Skipped ${skipped} self)` : ''}`);
    if (!confirmed) return;
    try {
      await axios.post(`${API}/admin/users/bulk-delete`, { user_ids: cleaned });
      setUsers((prev) => prev.filter(u => !cleaned.includes(u.id)));
      setSelectedUserIds([]); setSelectAllUsers(false);
    } catch (err) { alert('Error bulk-deleting users: ' + (err.response?.data?.detail || 'Please try again.')); }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>User Management ({users.length} users)</CardTitle>
            <div className="flex items-center space-x-2">
              <div className="flex items-center space-x-2 mr-2">
                <Checkbox id="selectAllUsers" checked={selectAllUsers} onCheckedChange={toggleSelectAllUsers} />
                <Label htmlFor="selectAllUsers">Select all</Label>
                <Button variant="destructive" size="sm" onClick={bulkDeleteUsers} disabled={selectedUserIds.length === 0}>Delete selected</Button>
              </div>
              <Button variant="outline" size="sm" onClick={() => { setRefreshKey(prev => prev + 1); fetchUsers(); }} disabled={loading}>
                {loading ? (<div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600"></div>) : ('Refresh')}
              </Button>
              <Button onClick={() => setShowCreateUser(true)}><Plus className="h-4 w-4 mr-2" />Add User</Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4" key={refreshKey}>
            {users.map((user, index) => (
              <div key={`${user.id}-${refreshKey}-${index}`} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center space-x-3">
                  <Checkbox checked={selectedUserIds.includes(user.id)} onCheckedChange={() => toggleUserChecked(user.id)} />
                  <div className="flex items-center space-x-2">
                    {user.role === 'admin' && <Shield className="h-4 w-4 text-purple-600" />}
                    <User className="h-4 w-4 text-gray-500" />
                  </div>
                  <div>
                    <p className="font-medium">{user.full_name}</p>
                    <p className="text-sm text-gray-600">{user.email}</p>
                    <div className="flex items-center space-x-2 mt-1">
                      <Badge variant={user.role === 'admin' ? 'default' : 'secondary'}>{user.role}</Badge>
                      <Badge variant={user.is_active ? 'outline' : 'destructive'}>{user.is_active ? 'Active' : 'Inactive'}</Badge>
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Button size="sm" variant="outline" onClick={() => toggleUserStatus(user.id, user.is_active)} disabled={loading}>
                    {user.is_active ? 'Deactivate' : 'Activate'}
                  </Button>
                  <Button size="sm" variant="destructive" onClick={(e) => { e.preventDefault(); e.stopPropagation(); deleteUser(user.id, user.full_name); }} disabled={deletingUserId === user.id}>
                    {deletingUserId === user.id ? (<div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>) : (<Trash2 className="h-4 w-4" />)}
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
              <DialogDescription>Add a new annotator or administrator to the system</DialogDescription>
            </DialogHeader>
            <div className="space-y-4 mt-4">
              <div className="space-y-2">
                <Label>Full Name</Label>
                <Input value={newUser.full_name} onChange={(e) => setNewUser({ ...newUser, full_name: e.target.value })} placeholder="Enter full name" />
              </div>
              <div className="space-y-2">
                <Label>Email</Label>
                <Input type="email" value={newUser.email} onChange={(e) => setNewUser({ ...newUser, email: e.target.value })} placeholder="Enter email address" />
              </div>
              <div className="space-y-2">
                <Label>Password</Label>
                <Input type="password" value={newUser.password} onChange={(e) => setNewUser({ ...newUser, password: e.target.value })} placeholder="Enter password" />
              </div>
              <div className="space-y-2">
                <Label>Role</Label>
                <Select value={newUser.role} onValueChange={(value) => setNewUser({ ...newUser, role: value })}>
                  <SelectTrigger><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="annotator">Annotator</SelectItem>
                    <SelectItem value="admin">Administrator</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex justify-end space-x-2">
                <Button variant="outline" onClick={() => setShowCreateUser(false)}>Cancel</Button>
                <Button onClick={createUser} disabled={loading}>{loading ? 'Creating...' : 'Create User'}</Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
};

// Annotation UI with sentence-level bulk delete
const StructuredAnnotationInterface = ({ sentences, currentIndex, onIndexChange, tagStructure, onAnnotate, onDeleteAnnotation, onBulkDeleteAnnotations }) => {
  const { user } = useAuth();
  const [selectedTags, setSelectedTags] = useState([]);
  const [notes, setNotes] = useState('');
  const [selectedAnnIds, setSelectedAnnIds] = useState([]);
  const [selectAll, setSelectAll] = useState(false);

  const currentSentence = sentences[currentIndex];

  useEffect(() => {
    setSelectedTags([]); setNotes(''); setSelectedAnnIds([]); setSelectAll(false);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [currentIndex]);

  if (!currentSentence) return null;

  const addTag = (domain, category, tag) => {
    const newTag = { domain, category, tag, valence: 'positive' };
    const exists = selectedTags.some(t => t.domain === domain && t.category === category && t.tag === tag);
    if (!exists) setSelectedTags([...selectedTags, newTag]);
  };

  const removeTag = (index) => { const newTags = [...selectedTags]; newTags.splice(index, 1); setSelectedTags(newTags); };
  const updateTagValence = (index, valence) => { const newTags = [...selectedTags]; newTags[index].valence = valence; setSelectedTags(newTags); };

  const handleSaveAnnotation = async () => {
    if (selectedTags.length === 0) return;
    await onAnnotate(currentSentence.id, selectedTags, notes);
    setSelectedTags([]); setNotes('');
  };

  const handleSkip = async () => {
    await onAnnotate(currentSentence.id, [], notes, true);
    setSelectedTags([]); setNotes('');
    if (currentIndex < sentences.length - 1) onIndexChange(currentIndex + 1);
    else { alert('Annotation complete! Returning to documents list.'); onAnnotate('ANNOTATION_COMPLETE', [], '', false); }
  };

  const toggleSelectAllAnns = () => {
    if (selectAll) { setSelectedAnnIds([]); setSelectAll(false); }
    else { setSelectedAnnIds((currentSentence.annotations || []).map(a => a.id)); setSelectAll(true); }
  };
  const toggleAnn = (id) => {
    setSelectedAnnIds((prev) => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  };
  const deleteSelectedAnns = () => {
    if (selectedAnnIds.length === 0) return;
    onBulkDeleteAnnotations(selectedAnnIds, currentSentence.id);
    setSelectedAnnIds([]); setSelectAll(false);
  };

  const progress = ((currentIndex + 1) / sentences.length) * 100;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Sentence Annotation</CardTitle>
            <Badge variant="secondary">{currentIndex + 1} of {sentences.length}</Badge>
          </div>
          <Progress value={progress} className="w-full" />
        </CardHeader>

        <CardContent className="space-y-6">
          <div className="p-4 bg-gray-50 rounded-lg">
            <p className="text-lg leading-relaxed">{currentSentence.text}</p>
          </div>

          {currentSentence.annotations && currentSentence.annotations.length > 0 && (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <h4 className="font-medium text-gray-900">Existing Annotations</h4>
                <div className="flex items-center gap-2">
                  <Checkbox id="selectAllSentenceAnns" checked={selectAll} onCheckedChange={toggleSelectAllAnns} />
                  <Label htmlFor="selectAllSentenceAnns">Select all</Label>
                  <Button variant="destructive" size="sm" disabled={selectedAnnIds.length === 0} onClick={deleteSelectedAnns}>Delete selected</Button>
                </div>
              </div>
              <div className="space-y-2">
                {currentSentence.annotations.map((annotation) => {
                  const canDelete = user?.role === 'admin' || annotation.user_id === user?.id;
                  return (
                    <div key={annotation.id} className="p-3 bg-blue-50 rounded-md">
                      {annotation.skipped ? (
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <Checkbox checked={selectedAnnIds.includes(annotation.id)} onCheckedChange={() => toggleAnn(annotation.id)} />
                            <SkipForward className="h-4 w-4 text-orange-600" />
                            <span className="text-sm text-gray-600">Skipped by User {annotation.user_id.slice(-6)}</span>
                          </div>
                          {canDelete && (
                            <button type="button" onClick={(e) => { e.preventDefault(); e.stopPropagation(); onDeleteAnnotation(annotation.id, currentSentence.id); }} className="inline-flex items-center justify-center h-8 w-8 rounded-md hover:bg-accent">
                              <Trash2 className="h-4 w-4" />
                            </button>
                          )}
                        </div>
                      ) : (
                        <div>
                          <div className="flex items-center justify-between mb-1">
                            <div className="flex items-center gap-2">
                              <Checkbox checked={selectedAnnIds.includes(annotation.id)} onCheckedChange={() => toggleAnn(annotation.id)} />
                              <span className="text-sm text-gray-600">by User {annotation.user_id.slice(-6)}</span>
                            </div>
                            {canDelete && (
                              <button type="button" onClick={(e) => { e.preventDefault(); e.stopPropagation(); onDeleteAnnotation(annotation.id, currentSentence.id); }} className="inline-flex items-center justify-center h-8 w-8 rounded-md hover:bg-accent">
                                <Trash2 className="h-4 w-4" />
                              </button>
                            )}
                          </div>
                          <div className="flex flex-wrap gap-1 mb-2">
                            {annotation.tags.map((tag, tagIdx) => (
                              <Badge key={tagIdx} variant={tag.valence === 'positive' ? 'default' : 'destructive'} className="text-xs">
                                {tag.domain}: {tag.tag} ({tag.valence})
                              </Badge>
                            ))}
                          </div>
                          {annotation.notes && (<p className="text-sm text-gray-600">Notes: {annotation.notes}</p>)}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {selectedTags.length > 0 && (
            <div className="space-y-2">
              <h4 className="font-medium text-gray-900">Selected Tags:</h4>
              <div className="space-y-2">
                {selectedTags.map((tag, index) => (
                  <div key={index} className="flex items-center space-x-2 p-2 bg-green-50 rounded">
                    <Badge variant="outline">{tag.domain}: {tag.category} - {tag.tag}</Badge>
                    <Select value={tag.valence} onValueChange={(value) => updateTagValence(index, value)}>
                      <SelectTrigger className="w-32"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="positive">Positive</SelectItem>
                        <SelectItem value="negative">Negative</SelectItem>
                      </SelectContent>
                    </Select>
                    <Button size="sm" variant="ghost" onClick={() => removeTag(index)}><X className="h-4 w-4" /></Button>
                  </div>
                ))}
              </div>
            </div>
          )}

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
                          <Button key={tag} size="sm" variant="outline" onClick={() => addTag(domain, category, tag)} className="text-xs h-6 px-2">
                            <Plus className="h-3 w-3 mr-1" />{tag}
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

          <div className="space-y-2">
            <Label>Notes (optional)</Label>
            <Textarea value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Additional context or observations..." rows={3} />
          </div>

          <div className="flex space-x-2">
            <Button onClick={handleSaveAnnotation} disabled={selectedTags.length === 0} className="bg-green-600 hover:bg-green-700">
              <CheckCircle className="h-4 w-4 mr-2" />Save Annotation
            </Button>
            <Button onClick={handleSkip} variant="outline" className="border-orange-300 text-orange-700 hover:bg-orange-50">
              <SkipForward className="h-4 w-4 mr-2" />Skip - No SDOH Content
            </Button>
            <Button variant="outline" onClick={() => { setSelectedTags([]); setNotes(''); onIndexChange(Math.max(0, currentIndex - 1)); }} disabled={currentIndex === 0}>Previous</Button>
            <Button variant="outline" onClick={() => { setSelectedTags([]); setNotes(''); onIndexChange(Math.min(sentences.length - 1, currentIndex + 1)); }} disabled={currentIndex === sentences.length - 1}>Next</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// App
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
  if (!user) return <AuthForm />;
  return (
    <>
      <Header />
      <main>
        <Routes>
          <Route path="/home" element={<Home />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/" element={<Navigate to="/home" />} />
          <Route path="*" element={<Navigate to="/home" />} />
        </Routes>
      </main>
    </>
  );
};

export default App;