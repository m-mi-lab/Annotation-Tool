/* eslint-disable */
import React, { useState, useEffect, useContext, createContext, useRef } from "react";
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
import { FileText, Users, Upload, User, LogOut, Tag, CheckCircle, Plus, Minus, X, SkipForward, Shield, Settings, Trash2, Download } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
      // Global 401 handler
      axios.interceptors.response.use(
        (res) => res,
        (err) => {
          if (err?.response?.status === 401) {
            showToast('Session expired. Please sign in again.', 'error');
            logout();
          }
          return Promise.reject(err);
        }
      );
      fetchUser();
    } else {
      setLoading(false);
    }
  }, [token]);

  const fetchUser = async () => {
    try {
      const res = await axios.get(`${API}/auth/me`);
      setUser(res.data);
    } catch (e) {
      logout();
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password) => {
    try {
      const res = await axios.post(`${API}/auth/login`, { email, password });
      const { access_token } = res.data;
      setToken(access_token);
      localStorage.setItem("token", access_token);
      axios.defaults.headers.common["Authorization"] = `Bearer ${access_token}`;
      await fetchUser();
      return { success: true };
    } catch (e) {
      return { success: false, error: e.response?.data?.detail || "Login failed" };
    }
  };

  const register = async (email, password, fullName, role = "annotator") => {
    try {
      await axios.post(`${API}/auth/register`, { email, password, full_name: fullName, role });
      return await login(email, password);
    } catch (e) {
      return { success: false, error: e.response?.data?.detail || "Registration failed" };
    }
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem("token");
    delete axios.defaults.headers.common["Authorization"];
  };

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout, setUser }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within an AuthProvider");
  return ctx;
};

// Account Page
const AccountPage = () => {
  const { user, setUser } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name || "");
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [saving, setSaving] = useState(false);
  const navigate = useNavigate();

  const saveProfile = async () => {
    setSaving(true);
    try {
      const res = await axios.put(`${API}/auth/me/profile`, { full_name: fullName });
      if (res?.data) setUser(res.data);
      showToast('Profile updated', 'success');
    } catch (e) {
      showToast(e.response?.data?.detail || 'Error updating profile', 'error');
    } finally { setSaving(false); }
  };

  const changePassword = async () => {
    if (newPassword !== confirmPassword) { showToast('New passwords do not match', 'error'); return; }
    setSaving(true);
    try {
      await axios.post(`${API}/auth/change-password`, { current_password: currentPassword, new_password: newPassword });
      showToast('Password changed', 'success');
      setCurrentPassword(""); setNewPassword(""); setConfirmPassword("");
    } catch (e) {
      showToast(e.response?.data?.detail || 'Error changing password', 'error');
    } finally { setSaving(false); }
  };

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>My Account</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label>Full Name</Label>
            <Input value={fullName} onChange={(e) => setFullName(e.target.value)} />
          </div>
          <div className="flex items-center gap-2">
            <Button onClick={saveProfile} disabled={saving}>Save Profile</Button>
            <Button variant="outline" onClick={() => navigate('/dashboard')}>Back</Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Change Password</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="space-y-2">
            <Label>Current Password</Label>
            <Input type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label>New Password</Label>
            <Input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label>Confirm New Password</Label>
            <Input type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} />
          </div>
          <div>
            <Button onClick={changePassword} disabled={saving}>Change Password</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Header
const Header = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  return (
    <header className="bg-white border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <button type="button" onClick={() => navigate("/home")} className="flex items-center space-x-3 hover:opacity-80">
            <FileText className="h-8 w-8 text-blue-600" />
            <h1 className="text-xl font-semibold text-gray-900">SDOH Annotation Tool</h1>
          </button>
          {user && (
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                {user.role === "admin" && <Shield className="h-4 w-4 text-purple-600" title="Administrator" />}
                <User className="h-4 w-4 text-gray-500" />
                <button className="text-sm text-blue-700 underline" onClick={() => navigate("/account")}>
                  {user.full_name}
                </button>
                <Badge variant={user.role === "admin" ? "default" : "secondary"}>{user.role}</Badge>
              </div>
              <Button variant="ghost" size="sm" onClick={logout}>
                <LogOut className="h-4 w-4 mr-1" /> Logout
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
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();

  const submit = async (e) => {
    e.preventDefault(); setError(""); setLoading(true);
    try {
      const result = isLogin ? await login(email, password) : await register(email, password, fullName);
      if (!result.success) setError(result.error);
    } catch {
      setError("Unexpected error");
    } finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold text-gray-900">{isLogin ? "Sign In" : "Create Account"}</CardTitle>
          <p className="text-gray-600 mt-2">{isLogin ? "Access the SDOH Annotation Tool" : "Join the annotation team"}</p>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="space-y-4">
            {!isLogin && (
              <div className="space-y-2">
                <Label>Full Name</Label>
                <Input value={fullName} onChange={(e) => setFullName(e.target.value)} required placeholder="Enter your full name" />
              </div>
            )}
            <div className="space-y-2">
              <Label>Email</Label>
              <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="Enter your email" />
            </div>
            <div className="space-y-2">
              <Label>Password</Label>
              <Input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required placeholder="Enter your password" />
            </div>
            {error && (<Alert variant="destructive"><AlertDescription>{error}</AlertDescription></Alert>)}
            <Button type="submit" className="w-full" disabled={loading}>{loading ? "Please wait..." : (isLogin ? "Sign In" : "Create Account")}</Button>
            <div className="text-center">
              <button type="button" onClick={() => { setIsLogin(!isLogin); setError(""); }} className="text-sm text-blue-600 hover:text-blue-800 underline">
                {isLogin ? "Don't have an account? Sign up" : "Already have an account? Sign in"}
              </button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

// Active Docs Panel
const ActiveDocsPanel = ({ onOpenDoc }) => {
  const { user } = useAuth();
  const [scope, setScope] = useState("me");
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchActive = async () => {
    try {
      setLoading(true);
      const res = await axios.get(`${API}/annotations/active-docs`, { params: { scope } });
      setItems(res.data || []);
    } catch {
    } finally { setLoading(false); }
  };

  useEffect(() => { fetchActive(); }, [scope]);

  if (!items.length && !loading) return null;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Active Documents</CardTitle>
          <div className="flex items-center gap-2">
            <Label>View:</Label>
            <Select value={scope} onValueChange={setScope}>
              <SelectTrigger className="w-32"><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="me">Me</SelectItem>
                {user?.role === "admin" && <SelectItem value="team">Team</SelectItem>}
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="text-sm text-gray-600">Loading active documents...</div>
        ) : (
          <div className="space-y-3">
            {items.map((it) => (
              <div key={it.document_id} className="p-3 border rounded-md">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium">{it.filename}</div>
                    <div className="text-xs text-gray-500">{it.annotated_count}/{it.total_sentences} sentences</div>
                  </div>
                  <div className="w-64">
                    <div className="h-2 bg-gray-200 rounded"><div className="h-2 bg-blue-600 rounded" style={{ width: `${Math.round(it.progress*100)}%` }}></div></div>
                  </div>
                  <div className="flex items-center gap-2">
                    {typeof it.last_annotation_index === 'number' && (
                      <Button size="sm" variant="outline" onClick={() => onOpenDoc(it.document_id)}>Resume</Button>
                    )}
                  </div>
                </div>
                {it.subjects && it.subjects.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-2">
                    {it.subjects.slice(0, 30).map((sub) => (
                      <span key={sub} className="px-2 py-1 text-xs rounded bg-gray-100 border">{sub}</span>
                    ))}
                    {it.subjects.length > 30 && <span className="text-xs text-gray-500">+{it.subjects.length - 30} more</span>}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

// Structured Annotation Interface
const StructuredAnnotationInterface = ({ sentences, currentIndex, onIndexChange, tagStructure, onAnnotate, onDeleteAnnotation, onBulkDeleteAnnotations, currentDocName }) => {
  const { user } = useAuth();
  const [selectedTags, setSelectedTags] = useState([]);
  const [notes, setNotes] = useState("");
  const [selectedAnnIds, setSelectedAnnIds] = useState([]);
  const [selectAll, setSelectAll] = useState(false);
  const [toast, setToast] = useState(null);
  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 1600);
  };

  // Quick shortcuts: flatten first 9 tags for 1-9 keyboard mapping
  const quickTags = React.useMemo(() => {
    const arr = [];
    Object.entries(tagStructure || {}).forEach(([domain, cats]) => {
      Object.entries(cats || {}).forEach(([category, tags]) => {
        (tags || []).forEach((tag) => arr.push({ domain, category, tag }));
      });
    });
    return arr.slice(0, 9);
  }, [tagStructure]);

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e) => {
      const ae = document.activeElement;
      const isTyping = ae && (ae.tagName === 'INPUT' || ae.tagName === 'TEXTAREA' || ae.getAttribute('contenteditable') === 'true');
      if (isTyping) return;
      if (e.key === 'Enter') {
        if (selectedTags.length > 0) handleSaveAnnotation();
      } else if (e.key.toLowerCase() === 's') {
        handleSkip();
      } else if (e.key === 'ArrowLeft') {
        if (currentIndex > 0) { setSelectedTags([]); setNotes(""); onIndexChange(currentIndex - 1); }
      } else if (e.key === 'ArrowRight') {
        if (currentIndex < sentences.length - 1) { setSelectedTags([]); setNotes(""); onIndexChange(currentIndex + 1); }
      } else if (e.key.toLowerCase() === 'c') {
        setSelectedTags([]);
      } else if (e.key.toLowerCase() === 'p') {
        if (selectedTags.length) {
          setSelectedTags(prev => prev.map((t, i) => i === prev.length - 1 ? { ...t, valence: 'positive' } : t));
        }
      } else if (e.key.toLowerCase() === 'n') {
        if (selectedTags.length) {
          setSelectedTags(prev => prev.map((t, i) => i === prev.length - 1 ? { ...t, valence: 'negative' } : t));
        }
      } else if (/^[1-9]$/.test(e.key)) {
        const idx = parseInt(e.key, 10) - 1;
        const qt = quickTags[idx];
        if (qt) toggleTag(qt.domain, qt.category, qt.tag);
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [selectedTags, currentIndex, sentences.length, quickTags]);

  const currentSentence = sentences[currentIndex];
  const currentSubject = currentSentence?.subject_id || null;

  useEffect(() => {
    setSelectedTags([]); setNotes(""); setSelectedAnnIds([]); setSelectAll(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, [currentIndex]);

  if (!currentSentence) return null;

  const toggleTag = (domain, category, tag) => {
    const exists = selectedTags.some(t => t.domain === domain && t.category === category && t.tag === tag);
    if (exists) {
      setSelectedTags(prev => prev.filter(t => !(t.domain === domain && t.category === category && t.tag === tag)));
    } else {
      const newTag = { domain, category, tag, valence: "positive" };
      setSelectedTags(prev => [...prev, newTag]);
    }
  };

  const removeTag = (index) => { const n = [...selectedTags]; n.splice(index, 1); setSelectedTags(n); };
  const updateTagValence = (index, valence) => { const n = [...selectedTags]; n[index].valence = valence; setSelectedTags(n); };
  const selectTagWithValence = (domain, category, tag, valence) => {
    setSelectedTags(prev => {
      const idx = prev.findIndex(t => t.domain === domain && t.category === category && t.tag === tag);
      if (idx >= 0) {
        // if same valence clicked again, remove; otherwise update valence
        if (prev[idx].valence === valence) {
          const cp = [...prev]; cp.splice(idx, 1); return cp;
        } else {
          const cp = [...prev]; cp[idx] = { ...cp[idx], valence }; return cp;
        }
      } else {
        return [...prev, { domain, category, tag, valence }];
      }
    });
  };

  const handleSaveAnnotation = async () => {
    if (selectedTags.length === 0) return;
    await onAnnotate(currentSentence.id, selectedTags, notes);
    setSelectedTags([]); setNotes("");
    showToast('Annotation saved', 'success');
  };

  const saveAndMove = async (dir) => {
    if (selectedTags.length === 0) return;
    await onAnnotate(currentSentence.id, selectedTags, notes);
    setSelectedTags([]); setNotes("");
    if (dir === 'prev' && currentIndex > 0) onIndexChange(currentIndex - 1);
    if (dir === 'next' && currentIndex < sentences.length - 1) onIndexChange(currentIndex + 1);
  };

  const handleSkip = async () => {
    await onAnnotate(currentSentence.id, [], notes, true);
    setSelectedTags([]); setNotes("");
    showToast('Marked as skipped', 'info');
    if (currentIndex < sentences.length - 1) onIndexChange(currentIndex + 1);
    else showToast('Annotation complete for this document.', 'info');
  };

  const toggleSelectAllAnns = () => {
    if (selectAll) { setSelectedAnnIds([]); setSelectAll(false); }
    else { setSelectedAnnIds((currentSentence.annotations || []).map(a => a.id)); setSelectAll(true); }
  };

  const toggleAnn = (id) => { setSelectedAnnIds((prev) => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]); };
  const deleteSelectedAnns = () => { if (selectedAnnIds.length) onBulkDeleteAnnotations(selectedAnnIds, currentSentence.id); };

  const isSelectedTag = (domain, category, tag) => selectedTags.some(t => t.domain === domain && t.category === category && t.tag === tag);

  const progress = ((currentIndex + 1) / sentences.length) * 100;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle>Annotating: {currentDocName || ""}</CardTitle>
            <Badge variant="secondary">{currentIndex + 1} of {sentences.length}</Badge>
          </div>
          <div className="flex items-center justify-between text-sm text-gray-600">
            <span>Subject: {currentSubject || "N/A"}</span>
            <div className="flex items-center gap-2">
              <Button size="sm" variant="outline" onClick={() => {
                if (!currentSubject) return;
                for (let i = currentIndex - 1; i >= 0; i--) {
                  if (sentences[i]?.subject_id && sentences[i].subject_id !== currentSubject) { onIndexChange(i); return; }
                }
              }} disabled={!currentSubject}>Prev Subject</Button>
              <Button size="sm" variant="outline" onClick={() => {
                if (!currentSubject) return;
                for (let i = currentIndex + 1; i < sentences.length; i++) {
                  if (sentences[i]?.subject_id && sentences[i].subject_id !== currentSubject) { onIndexChange(i); return; }
                }
              }} disabled={!currentSubject}>Next Subject</Button>
          </div>
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
                  const deleteOneTag = async (annId, t) => {
                    try {
                      const res = await axios.post(`${API}/annotations/${annId}/remove-tag`, { domain: t.domain, category: t.category, tag: t.tag });
                      if (res?.data?.id) await refreshSentenceAnnotations(annotation.sentence_id);
                      else await refreshSentenceAnnotations(annotation.sentence_id);
                    } catch (e) { showToast('Error removing tag: ' + (e.response?.data?.detail || 'Please try again.'), 'error'); }
                  };
                  return (
                    <div key={annotation.id} className="p-3 bg-blue-50 rounded-md">
                      {annotation.skipped ? (
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <Checkbox checked={selectedAnnIds.includes(annotation.id)} onCheckedChange={() => toggleAnn(annotation.id)} />
                            <SkipForward className="h-4 w-4 text-orange-600" />
                            <span className="text-sm text.gray-600">Skipped by User {annotation.user_id.slice(-6)}</span>
                          </div>
                          {canDelete && (
                            <button type="button" onClick={() => onDeleteAnnotation(annotation.id, currentSentence.id)} className="inline-flex items-center justify-center h-8 w-8 rounded-md hover:bg-accent">
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
                              <button type="button" onClick={() => onDeleteAnnotation(annotation.id, currentSentence.id)} className="inline-flex items-center justify-center h-8 w-8 rounded-md hover:bg-accent">
                                <Trash2 className="h-4 w-4" />
                              </button>
                            )}
                          </div>
                          <div className="flex flex-wrap gap-1 mb-2">
                            {(annotation.tags || []).map((tag, tagIdx) => (
                              <span key={tagIdx} className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded border ${tag.valence === 'positive' ? 'bg-green-100 text-green-800 border-green-300' : 'bg-red-100 text-red-800 border-red-300'}`}>
                                {tag.domain}: {tag.tag} ({tag.valence})
                                {canDelete && (
                                  <button type="button" className="ml-1 opacity-70 hover:opacity-100" onClick={() => deleteOneTag(annotation.id, tag)} title="Remove this tag">×</button>
                                )}
                              </span>
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
              <div className="flex items-center justify-between">
                <h4 className="font-medium text-gray-900">Selected Tags</h4>
                <div className="flex items-center gap-2">
                  <Button size="sm" variant="outline" onClick={() => setSelectedTags([])}>Clear all (C)</Button>
                  <span className="text-xs text-gray-500">Shortcuts: 1-9 add/remove quick tags • Enter save • S skip • [/] prev/next • P/N valence</span>
                </div>
              </div>
              <div className="space-y-2">
                {selectedTags.map((tag, index) => (
                  <div key={index} className={`flex items-center space-x-2 p-2 rounded border ${tag.valence === 'positive' ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
                    <span className={`text-xs px-2 py-0.5 rounded ${tag.valence === 'positive' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>{tag.domain}: {tag.category} - {tag.tag}</span>
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
            <div className="flex items-center justify-between">
              <h4 className="font-medium text-gray-900">Add Tags:</h4>
              <div className="text-xs text-gray-600">
                Legend: 1–9 quick add/remove • Enter Save • S Skip • [/] Prev/Next • P/N last tag valence • C Clear
              </div>
            </div>
            {Object.entries(tagStructure).map(([domain, categories]) => (
              <div key={domain} className="space-y-2">
                <h5 className="text-sm font-medium text-blue-700">{domain}</h5>
                <div className="grid gap-2">
                  {Object.entries(categories).map(([category, tags]) => (
                    <div key={category} className="space-y-1">
                      <h6 className="text-xs font-medium text-gray-600">{category}</h6>
                      <div className="flex flex-wrap gap-1">
                        {tags.map((tag) => (
                          <div key={tag} className="inline-flex">
                            <Button size="sm" variant={isSelectedTag(domain, category, tag) ? "default" : "outline"} onClick={() => selectTagWithValence(domain, category, tag, 'positive')} className="text-xs h-6 px-2 rounded-r-none">
                              <Plus className="h-3 w-3 mr-1" /> {tag}
                            </Button>
                            <Button size="sm" variant={isSelectedTag(domain, category, tag) ? "destructive" : "outline"} onClick={() => selectTagWithValence(domain, category, tag, 'negative')} className="text-xs h-6 px-2 rounded-l-none border-l-0">
                              <X className="h-3 w-3 mr-1" />
                            </Button>
                          </div>
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

          <div className="flex flex-wrap gap-2 items-center">
            <div className="inline-flex rounded-md shadow-sm" role="group">
              <Button onClick={handleSaveAnnotation} disabled={selectedTags.length === 0} className="bg-green-600 hover:bg-green-700 rounded-r-none">
                <CheckCircle className="h-4 w-4 mr-2" /> Save
              </Button>
              <Button onClick={() => saveAndMove('prev')} disabled={selectedTags.length === 0 || currentIndex === 0} className="rounded-none border-l-0">Save + Prev</Button>
              <Button onClick={() => saveAndMove('next')} disabled={selectedTags.length === 0 || currentIndex === sentences.length - 1} className="rounded-l-none border-l-0">Save + Next</Button>
            </div>
            <Button onClick={handleSkip} variant="outline" className="border-orange-300 text-orange-700 hover:bg-orange-50">
              <SkipForward className="h-4 w-4 mr-2" /> Skip - No SDOH Content
            </Button>
            <Button variant="outline" onClick={() => { setSelectedTags([]); setNotes(""); onIndexChange(Math.max(0, currentIndex - 1)); }} disabled={currentIndex === 0}>Previous</Button>
            <Button variant="outline" onClick={() => { setSelectedTags([]); setNotes(""); onIndexChange(Math.min(sentences.length - 1, currentIndex + 1)); }} disabled={currentIndex === sentences.length - 1}>Next</Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Admin Management Panel (users)
const AdminManagementPanel = ({ notify = (msg) => window.alert(msg) }) => {
  const { user: currentUser } = useAuth();
  const [users, setUsers] = useState([]);
  const [showCreateUser, setShowCreateUser] = useState(false);
  const [loading, setLoading] = useState(false);
  const [deletingUserId, setDeletingUserId] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);
  const [newUser, setNewUser] = useState({ email: "", password: "", full_name: "", role: "annotator" });
  const [selectedUserIds, setSelectedUserIds] = useState([]);
  const [selectAllUsers, setSelectAllUsers] = useState(false);
  const [toast, setToast] = useState(null);
  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 1600);
  };

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const res = await axios.get(`${API}/admin/users`);
      setUsers([...res.data]); setSelectedUserIds([]); setSelectAllUsers(false); setRefreshKey(Date.now());
    } catch (e) {
      showToast('Error fetching users: ' + (e.response?.data?.detail || 'Please try again.'), 'error');
    } finally { setLoading(false); }
  };

  useEffect(() => { fetchUsers(); }, []);

  const createUser = async () => {
    setLoading(true);
    try {
      await axios.post(`${API}/admin/users`, newUser);
      setNewUser({ email: "", password: "", full_name: "", role: "annotator" });
      setShowCreateUser(false); fetchUsers();
    } catch (e) { showToast('Error creating user: ' + (e.response?.data?.detail || e.message || 'Please try again.'), 'error'); }
    finally { setLoading(false); }
  };

  const toggleUserStatus = async (userId, isActive) => {
    try { await axios.put(`${API}/admin/users/${userId}`, { is_active: !isActive }); fetchUsers(); } catch {}
  };

  const deleteUser = async (userId, userName) => {
    if (userId === currentUser?.id) { showToast('You cannot delete your own account!', 'error'); return; }
    if (!window.confirm(`Delete user "${userName}"?`)) return;
    try {
      setUsers(users.filter(u => u.id !== userId)); setRefreshKey(Date.now()); setDeletingUserId(userId);
      await axios.delete(`${API}/admin/users/${userId}`);
    } catch (e) {
      showToast('User removed from list (API call failed but UI updated)', 'info');
    } finally { setDeletingUserId(null); }
  };

  const toggleSelectAllUsers = () => { if (selectAllUsers) { setSelectedUserIds([]); setSelectAllUsers(false); } else { setSelectedUserIds(users.map(u => u.id)); setSelectAllUsers(true); } };
  const toggleUserChecked = (uid) => { setSelectedUserIds(prev => prev.includes(uid) ? prev.filter(id => id !== uid) : [...prev, uid]); };
  const bulkDeleteUsers = async () => {
    if (!selectedUserIds.length) return;
    const cleaned = selectedUserIds.filter(id => id !== currentUser?.id);
    const skipped = selectedUserIds.length - cleaned.length;
    if (!window.confirm(`Delete ${cleaned.length} users?${skipped > 0 ? ` (Skipped ${skipped} self)` : ''}`)) return;
    try { await axios.post(`${API}/admin/users/bulk-delete`, { ids: cleaned }); setUsers(prev => prev.filter(u => !cleaned.includes(u.id))); setSelectedUserIds([]); setSelectAllUsers(false); }
    catch (e) { const msg = e.response?.data?.detail || e.message || JSON.stringify(e.response?.data || {}); showToast('Error bulk-deleting users: ' + msg, 'error'); }
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
                <Button variant="destructive" size="sm" onClick={bulkDeleteUsers} disabled={!selectedUserIds.length}>Delete selected</Button>
              </div>
              <Button variant="outline" size="sm" onClick={() => { setRefreshKey(prev => prev + 1); fetchUsers(); }} disabled={loading}>{loading ? "…" : "Refresh"}</Button>
              <Button onClick={() => setShowCreateUser(true)}><Plus className="h-4 w-4 mr-2" /> Add User</Button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4" key={refreshKey}>
            {users.map((u, idx) => (
              <div key={`${u.id}-${refreshKey}-${idx}`} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center space-x-3">
                  <Checkbox checked={selectedUserIds.includes(u.id)} onCheckedChange={() => toggleUserChecked(u.id)} />
                  <div className="flex items-center space-x-2">
                    {u.role === 'admin' && <Shield className="h-4 w-4 text-purple-600" />}
                    <User className="h-4 w-4 text-gray-500" />
                  </div>
                  <div>
                    <p className="font-medium">{u.full_name}</p>
                    <p className="text-sm text-gray-600">{u.email}</p>
                    <div className="flex items-center space-x-2 mt-1">
                      <Badge variant={u.role === 'admin' ? 'default' : 'secondary'}>{u.role}</Badge>
                      <Badge variant={u.is_active ? 'outline' : 'destructive'}>{u.is_active ? 'Active' : 'Inactive'}</Badge>
                    </div>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Button size="sm" variant="outline" onClick={() => toggleUserStatus(u.id, u.is_active)} disabled={loading}>{u.is_active ? 'Deactivate' : 'Activate'}</Button>
                  <Button size="sm" variant="destructive" onClick={(e) => { e.preventDefault(); e.stopPropagation(); deleteUser(u.id, u.full_name); }} disabled={deletingUserId === u.id}>{deletingUserId === u.id ? "…" : <Trash2 className="h-4 w-4" />}</Button>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
      {toast && (
        <div className={`fixed top-4 right-4 p-4 rounded-md shadow-lg z-50 ${
          toast.type === 'error' ? 'bg-red-500 text-white' : 
          toast.type === 'info' ? 'bg-blue-500 text-white' : 
          'bg-green-500 text-white'
        }`}>
          {toast.message}
        </div>
      )}
    </div>
  );
};

// Dashboard
const Dashboard = () => {
  const { user } = useAuth();
  const [documents, setDocuments] = useState([]);
  const [analytics, setAnalytics] = useState({});
  const [enhancedAnalytics, setEnhancedAnalytics] = useState({ per_user: [], sentences_left_overall: 0, irr_pairs: [] });
  const [projects, setProjects] = useState([]);
  const [projectsChartUrl, setProjectsChartUrl] = useState(null);
  const [selectedDocument, setSelectedDocument] = useState(null);
  const [sentences, setSentences] = useState([]);
  const [currentSentenceIndex, setCurrentSentenceIndex] = useState(0);
  const [loading, setLoading] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [activeTab, setActiveTab] = useState(user?.role === 'admin' ? 'admin' : 'documents');
  const [tagStructure, setTagStructure] = useState({});
  const [projectName, setProjectName] = useState("");
  const [projectDescription, setProjectDescription] = useState("");
  const [defaultProject, setDefaultProject] = useState('Default Project');
  const [defaultProjectModalOpen, setDefaultProjectModalOpen] = useState(false);
  const [defaultProjectInput, setDefaultProjectInput] = useState('Default Project');

  const [resources, setResources] = useState([]);
  const [resourceFile, setResourceFile] = useState(null);
  const [resourcePreview, setResourcePreview] = useState(null);

  const [selectedDocIds, setSelectedDocIds] = useState([]);
  const [selectAllDocs, setSelectAllDocs] = useState(false);

  const [manageAnnOpen, setManageAnnOpen] = useState(false);
  const [manageAnnDoc, setManageAnnDoc] = useState(null);
  const [docAnnotations, setDocAnnotations] = useState([]);
  const [selectedAnnIds, setSelectedAnnIds] = useState([]);
  const [selectAllAnns, setSelectAllAnns] = useState(false);
  const [filterAnnotator, setFilterAnnotator] = useState('all');
  const [filterType, setFilterType] = useState('all');
  const [filterText, setFilterText] = useState('');
  const [userMap, setUserMap] = useState({});
  const [filterSubject, setFilterSubject] = useState('all');

  useEffect(() => {
    fetchDocuments(); fetchAnalytics(); fetchEnhancedAnalytics(); fetchTagStructure(); fetchResources(); fetchProjects();
    const t = localStorage.getItem('token');
    if (t) {
      setProjectsChartUrl(`${API}/analytics/projects-chart?token=${encodeURIComponent(t)}`);
    } else {
      setProjectsChartUrl(`${API}/analytics/projects-chart`);
    }
  }, []);

  const fetchDocuments = async () => {
    try { const res = await axios.get(`${API}/documents`); setDocuments(res.data); setSelectedDocIds([]); setSelectAllDocs(false); } catch {}
  };
  const fetchAnalytics = async () => { try { const res = await axios.get(`${API}/analytics/overview`); setAnalytics(res.data); } catch {} };
  const fetchEnhancedAnalytics = async () => { try { const res = await axios.get(`${API}/analytics/enhanced`); setEnhancedAnalytics(res.data || { per_user: [], sentences_left_overall: 0, irr_pairs: [] }); } catch {} };
  const fetchProjects = async () => { try { const res = await axios.get(`${API}/analytics/projects`); setProjects(res.data || []); } catch {} };
  const fetchTagStructure = async () => {
    try {
      const res = await axios.get(`${API}/tag-structure`);
      const data = (res.data && res.data.tag_structure) ? res.data.tag_structure : res.data;
      setTagStructure(data || {});
    } catch {}
  };
  const [resourcesPage, setResourcesPage] = useState(1);
  const [resourcesTotal, setResourcesTotal] = useState(0);
  const [resourcesQuery, setResourcesQuery] = useState("");
  const [resourcesKind, setResourcesKind] = useState("all");
  const [resourcesMime, setResourcesMime] = useState("all");

  const fetchResources = async (page = resourcesPage) => {
    try {
      const params = { page, page_size: 20 };
      if (resourcesQuery) params.q = resourcesQuery;
      if (resourcesKind !== 'all') params.kind = resourcesKind;
      if (resourcesMime !== 'all') params.mime = resourcesMime;
      const res = await axios.get(`${API}/resources`, { params });
      setResources(res.data?.items || []);
      setResourcesTotal(res.data?.total || 0);
      setResourcesPage(res.data?.page || page);
    } catch {}
  };
  const addResourceLink = async (title, url) => { try { await axios.post(`${API}/admin/resources/link`, { title, url }); await fetchResources(); showToast('Link added', 'success'); } catch (e) { showToast('Error adding link: ' + (e.response?.data?.detail || 'Please try again.'), 'error'); } };

  const annotateDoc = async (documentId, options = {}) => {
    try {
      const res = await axios.get(`${API}/documents/${documentId}/sentences`);
      const items = res.data || [];
      setSentences(items); setSelectedDocument(documentId);
      let nextIndex = 0; if (typeof options.targetIndex === 'number') nextIndex = Math.min(Math.max(0, options.targetIndex), Math.max(0, items.length - 1));
      else if (options.targetSubject) { const idx = items.findIndex(s => s.subject_id === options.targetSubject); nextIndex = idx >= 0 ? idx : 0; }
      setCurrentSentenceIndex(nextIndex);
      setActiveTab('annotate');
      window.location.hash = 'annotate';
    } catch (e) { showToast('Error loading sentences: ' + (e.response?.data?.detail || 'Please try again.'), 'error'); }
  };

  const loadDocumentSentences = annotateDoc; // backward compatibility

  const refreshSentenceAnnotations = async (sentenceId) => {
    try { const res = await axios.get(`${API}/annotations/sentence/${sentenceId}`); setSentences((prev) => prev.map((s) => (s.id === sentenceId ? { ...s, annotations: res.data } : s))); } catch {}
  };

  const deleteAnnotation = async (annotationId, sentenceId) => {
    if (!window.confirm('Are you sure you want to delete this annotation?')) return;
    let prev; setSentences((p) => { prev = p; return p.map((s) => s.id !== sentenceId ? s : { ...s, annotations: (s.annotations || []).filter(a => a.id !== annotationId) }); });
    try { await axios.delete(`${API}/annotations/${annotationId}`); if (sentenceId) await refreshSentenceAnnotations(sentenceId); fetchAnalytics(); }
    catch (e) { if (prev) setSentences(prev); showToast('Error deleting annotation: ' + (e.response?.data?.detail || 'Not Found'), 'error'); }
  };

  const bulkDeleteAnnotations = async (annotationIds, sentenceId = null) => {
    if (!annotationIds?.length) return; if (!window.confirm(`Delete ${annotationIds.length} annotations?`)) return;
    try { await axios.post(`${API}/annotations/bulk-delete`, { annotation_ids: annotationIds }); if (sentenceId) await refreshSentenceAnnotations(sentenceId); if (manageAnnOpen && manageAnnDoc) await openManageAnnotations(manageAnnDoc); fetchAnalytics(); }
    catch (e) { showToast('Error bulk-deleting annotations: ' + (e.response?.data?.detail || 'Please try again.'), 'error'); }
  };

  const createAnnotation = async (sentenceId, tags, notes, skipped = false) => {
    try { await axios.post(`${API}/annotations`, { sentence_id: sentenceId, tags, notes, skipped }); await refreshSentenceAnnotations(sentenceId); fetchAnalytics(); }
    catch (e) { showToast('Error saving annotation: ' + (e.response?.data?.detail || 'Please try again.'), 'error'); }
  };

  const deleteDocument = async (documentId) => {
    if (!window.confirm('Delete this document and all associated annotations?')) return;
    try { setDocuments(documents.filter(d => d.id !== documentId)); await axios.delete(`${API}/admin/documents/${documentId}`); fetchAnalytics(); }
    catch (e) { showToast('Document removed from list (API call failed but UI updated)', 'info'); }
  };

  const downloadAnnotatedCsv = async (doc) => {
    try {
      const url = `${API}/admin/download/annotated-csv-split/${doc.id}`;
      const token = localStorage.getItem('token');
      let res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
      if (res.status === 404 || res.status === 401) {
        res = await fetch(`${url}?token=${encodeURIComponent(token || '')}`);
      }
      if (!res.ok) throw new Error(await res.text() || `HTTP ${res.status}`);
      const blob = await res.blob(); const filename = `annotated_${doc.filename || 'document'}.csv`;
      const a = document.createElement('a'); const u = window.URL.createObjectURL(blob); a.href = u; a.setAttribute('download', filename); document.body.appendChild(a); a.click(); document.body.removeChild(a); window.URL.revokeObjectURL(u);
    } catch (e) { showToast('Error downloading CSV: ' + (e.message || 'Please try again.'), 'error'); }
  };
  const downloadAnnotatedCsvInline = async (doc) => {
    try {
      const url = `${API}/admin/download/annotated-csv-inline/${doc.id}`;
      const token = localStorage.getItem('token');
      let res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
      if (res.status === 404 || res.status === 401) {
        res = await fetch(`${url}?token=${encodeURIComponent(token || '')}`);
      }
      if (!res.ok) throw new Error(await res.text() || `HTTP ${res.status}`);
      const blob = await res.blob();
      const filename = `annotated_inline_${doc.filename || 'document'}.csv`;
      const a = document.createElement('a'); const u = window.URL.createObjectURL(blob); a.href = u; a.setAttribute('download', filename); document.body.appendChild(a); a.click(); document.body.removeChild(a); window.URL.revokeObjectURL(u);
    } catch (e) {
      showToast('Error downloading CSV: ' + (e.message || 'Please try again.'), 'error');
    }
  };

  const uploadResource = async () => { if (!resourceFile) return; const form = new FormData(); form.append('file', resourceFile); try { await axios.post(`${API}/admin/resources/upload`, form, { headers: { 'Content-Type': 'multipart/form-data' } }); setResourceFile(null); fetchResources(); showToast('Resource uploaded', 'success'); } catch (e) { showToast('Error uploading resource: ' + (e.response?.data?.detail || 'Please try again.'), 'error'); } };
  const downloadResource = async (resItem) => { try { const url = `${API}/resources/${resItem.id}/download`; const token = localStorage.getItem('token'); const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } }); if (!res.ok) throw new Error(await res.text() || `HTTP ${res.status}`); const blob = await res.blob(); const filename = resItem.filename || 'resource'; const a = document.createElement('a'); const u = window.URL.createObjectURL(blob); a.href = u; a.setAttribute('download', filename); document.body.appendChild(a); a.click(); document.body.removeChild(a); window.URL.revokeObjectURL(u); showToast('Download started', 'info'); } catch (e) { showToast('Error downloading resource: ' + (e.message || 'Please try again.'), 'error'); } };

  const deleteResource = async (resItem) => { if (!window.confirm(`Delete resource "${resItem.filename}"?`)) return; try { await axios.delete(`${API}/admin/resources/${resItem.id}`); fetchResources(); } catch (e) { alert('Error deleting resource: ' + (e.response?.data?.detail || 'Please try again.')); } };

  const openManageAnnotations = async (doc) => {
    setManageAnnDoc(doc); setManageAnnOpen(true);
    try {
      const res = await axios.get(`${API}/documents/${doc.id}/annotations`);
      setDocAnnotations(res.data || []);
      setSelectedAnnIds([]); setSelectAllAnns(false);
      try { if (user?.role === 'admin') { const usersRes = await axios.get(`${API}/admin/users`); const map = {}; (usersRes.data || []).forEach(u => { map[u.id] = u.full_name || u.email; }); setUserMap(map); } } catch {}
    } catch (e) { alert('Error loading annotations: ' + (e.response?.data?.detail || 'Please try again.')); }
  };
  const toggleSelectAllAnns = () => { if (selectAllAnns) { setSelectedAnnIds([]); setSelectAllAnns(false); } else { setSelectedAnnIds(docAnnotations.map(a => a.id)); setSelectAllAnns(true); } };
  const toggleAnnChecked = (id) => { setSelectedAnnIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]); };
  const bulkDeleteDocAnnotations = async () => { if (!selectedAnnIds.length) return; if (!window.confirm(`Delete ${selectedAnnIds.length} annotations from this document?`)) return; await bulkDeleteAnnotations(selectedAnnIds); };

  // Tabs: Admin (includes analytics), Documents, Annotate, Resources
  const tabsToShow = user?.role === 'admin'
    ? [
        { value: 'admin', label: 'Admin', icon: Settings },
        { value: 'documents', label: 'Documents', icon: FileText },
        { value: 'annotate', label: 'Annotate', icon: Tag },
        { value: 'resources', label: 'Resources', icon: FileText },
      ]
    : [
        { value: 'documents', label: 'Documents', icon: FileText },
        { value: 'annotate', label: 'Annotate', icon: Tag },
        { value: 'resources', label: 'Resources', icon: FileText },
      ];

  // Deep link handler
  useEffect(() => {
    const handler = () => {
      const raw = window.location.hash?.replace('#', '');
      if (!raw) return;
      const [tabPart, subjectPart] = raw.split('&');
      const allowed = ['admin','documents','annotate','resources'];
      if (tabPart && allowed.includes(tabPart)) setActiveTab(tabPart);
      if (subjectPart && subjectPart.startsWith('subject=')) {
        const subId = subjectPart.split('=')[1];
        if (selectedDocument) {
          const idx = sentences.findIndex(s => s.subject_id === subId);
          if (idx >= 0) setCurrentSentenceIndex(idx);
        }
      }
    };
    window.addEventListener('hashchange', handler);
    handler(); // run once on mount
    return () => window.removeEventListener('hashchange', handler);
  }, [selectedDocument, sentences.length]);

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
          <TabsContent value="admin" className="space-y-6" id="admin">
            <AdminManagementPanel />

            <Card>
              <CardHeader><CardTitle>Analytics Overview</CardTitle></CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Card><CardContent className="p-4"><div className="text-sm text-gray-600">Documents</div><div className="text-2xl font-semibold">{analytics.total_documents || 0}</div></CardContent></Card>
                  <Card><CardContent className="p-4"><div className="text-sm text-gray-600">Sentences</div><div className="text-2xl font-semibold">{analytics.total_sentences || 0}</div></CardContent></Card>
                  <Card><CardContent className="p-4"><div className="text-sm text-gray-600">Annotations</div><div className="text-2xl font-semibold">{analytics.total_annotations || 0}</div></CardContent></Card>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                  <Card><CardHeader><CardTitle>Category Counts</CardTitle></CardHeader><CardContent><img src={`${API}/analytics/tag-prevalence-chart?token=${encodeURIComponent(localStorage.getItem('token')||'')}`} alt="Category Counts Chart" className="w-full rounded border" /></CardContent></Card>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle>Projects Overview</CardTitle></CardHeader>
              <CardContent>
                {projectsChartUrl && (<img src={projectsChartUrl} alt="Projects Chart" className="w-full rounded border mb-4" />)}
                <div className="overflow-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="text-left text-gray-600">
                        <th className="p-2">Project</th>
                        <th className="p-2">Docs</th>
                        <th className="p-2">Sentences</th>
                        <th className="p-2">Annotated</th>
                        <th className="p-2">Progress</th>
                        <th className="p-2">Annotators</th>
                        <th className="p-2">Last Activity</th>
                      </tr>
                    </thead>
                    <tbody>
                      {projects.map((p, i) => (
                        <tr key={i} className="border-t">
                          <td className="p-2">{p.project_name}</td>
                          <td className="p-2">{p.documents_count}</td>
                          <td className="p-2">{p.total_sentences}</td>
                          <td className="p-2">{p.annotated_sentences}</td>
                          <td className="p-2">
                            <div className="w-40">
                              <div className="h-2 bg-gray-200 rounded"><div className="h-2 bg-blue-600 rounded" style={{ width: `${Math.round((p.progress||0)*100)}%` }}></div></div>
                            </div>
                          </td>
                          <td className="p-2">{p.annotators_count}</td>
                          <td className="p-2">{p.last_activity ? new Date(p.last_activity).toLocaleString() : '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        )}

        <TabsContent value="documents" className="space-y-4" id="documents">
          <div className="flex items-center justify-between">
            <CardTitle>Documents ({documents.length})</CardTitle>
            {user?.role === 'admin' && (
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm" onClick={() => setDefaultProjectModalOpen(true)}>Set Default Project</Button>
                <Button variant="outline" size="sm" onClick={async () => { if (!window.confirm('Reassign all existing documents to the current default project?')) return; try { const res = await axios.post(`${API}/admin/documents/reassign-to-default`); alert(`All documents reassigned to: ${res.data?.project_name || 'Default Project'}`); fetchDocuments(); } catch (e) { alert('Error reassigning documents: ' + (e.response?.data?.detail || e.message || 'Please try again.')); } }}>Reassign all to default</Button>
              </div>
            )}

            {user?.role === 'admin' && (
              <div className="flex items-center gap-2 p-2 bg-gray-50 border rounded">
                <div className="flex items-center gap-2 mr-2">
                  <Checkbox id="selectAllDocs" checked={selectAllDocs} onCheckedChange={() => { if (selectAllDocs) { setSelectedDocIds([]); setSelectAllDocs(false); } else { setSelectedDocIds(documents.map(d => d.id)); setSelectAllDocs(true); } }} />
                  <Label htmlFor="selectAllDocs">Select all</Label>
                  <Button variant="outline" size="sm" onClick={() => { setSelectedDocIds([]); setSelectAllDocs(false); }}>Deselect all</Button>
                </div>
                <div className="flex items-center gap-2 pl-4 ml-4 border-l">
                  <input id="csvUploadInput" type="file" accept=".csv" onChange={(e) => { const f = e.target.files?.[0]; setUploadFile(f || null); }} />
                  <Button variant="secondary" size="sm" disabled={!uploadFile} onClick={async () => { if (!uploadFile) return; const form = new FormData(); form.append('file', uploadFile); try { await axios.post(`${API}/documents/upload`, form, { headers: { 'Content-Type': 'multipart/form-data' } }); setUploadFile(null); fetchDocuments(); fetchAnalytics(); } catch (err) { alert('Error uploading CSV: ' + (err.response?.data?.detail || err.message || 'Please try again.')); } finally { const el = document.getElementById('csvUploadInput'); if (el) el.value = ''; } }}>Upload CSV</Button>
                </div>
                <Button variant="destructive" size="sm" onClick={async () => { if (!selectedDocIds.length) return; if (!window.confirm(`Delete ${selectedDocIds.length} documents?`)) return; try { await axios.post(`${API}/admin/documents/bulk-delete`, { ids: selectedDocIds }); setDocuments(prev => prev.filter(d => !selectedDocIds.includes(d.id))); setSelectedDocIds([]); setSelectAllDocs(false); fetchAnalytics(); } catch (e) { alert('Error bulk-deleting documents: ' + (e.response?.data?.detail || 'Please try again.')); } }} disabled={!selectedDocIds.length}>Delete selected</Button>
              </div>
            )}
          </div>
          <div className="grid gap-4">
            {documents.map((doc) => (
              <Card key={doc.id} className="hover:shadow-md transition-shadow">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        {user?.role === 'admin' && (
                          <Checkbox checked={selectedDocIds.includes(doc.id)} onCheckedChange={() => setSelectedDocIds(prev => prev.includes(doc.id) ? prev.filter(id => id !== doc.id) : [...prev, doc.id])} />
                        )}
                        <h3 className="font-medium">{doc.filename}</h3>
                        {doc.project_name && (<Badge variant="outline">{doc.project_name}</Badge>)}
                      </div>
                      <p className="text-sm text-gray-600">{doc.total_sentences} sentences • Uploaded {new Date(doc.upload_date || doc.created_at).toLocaleDateString()}</p>
                      {doc.description && (<p className="text-xs text-gray-500 mt-1">{doc.description}</p>)}
                    </div>
                    <div className="flex items-center space-x-2">
                      <Button onClick={() => annotateDoc(doc.id)} variant="outline">Annotate</Button>
                      {user?.role === 'admin' && (
                        <>
                          <Button variant="secondary" size="sm" onClick={() => downloadAnnotatedCsvInline(doc)}><Download className="h-4 w-4 mr-1" /> Download annotated CSV</Button>
                          <Button variant="outline" size="sm" onClick={async () => { try { const url = `${API}/admin/download/annotated-paragraphs/${doc.id}`; const token = localStorage.getItem('token'); let res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } }); if (!res.ok) throw new Error(await res.text() || `HTTP ${res.status}`); const blob = await res.blob(); const a = document.createElement('a'); const u = window.URL.createObjectURL(blob); a.href = u; a.setAttribute('download', `annotated_paragraphs_${doc.filename || 'document'}.csv`); document.body.appendChild(a); a.click(); document.body.removeChild(a); window.URL.revokeObjectURL(u); } catch (e) { alert('Error downloading annotated paragraphs: ' + (e.message || 'Please try again.')); } }}><Download className="h-4 w-4 mr-1" /> Download annotated paragraphs</Button>
                          <Button variant="outline" size="sm" onClick={() => openManageAnnotations(doc)}>Manage Annotations</Button>
                          <Button onClick={() => deleteDocument(doc.id)} variant="destructive" size="sm"><Trash2 className="h-4 w-4" /></Button>
                        </>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="annotate" className="space-y-4" id="annotate">
          <ActiveDocsPanel onOpenDoc={(id) => annotateDoc(id)} />
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
              currentDocName={(documents.find(d => d.id === selectedDocument) || {}).filename}
            />
          )}
        </TabsContent>

        <TabsContent value="resources" className="space-y-4" id="resources">
          {user?.role === 'admin' && (
            <Card>
              <CardHeader><CardTitle>Upload Resources</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center gap-2">
                  <Input type="file" accept=".pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.gif,.jpg,.jpeg,.tif,.tiff,.png" onChange={(e) => setResourceFile(e.target.files[0])} />
                  <Button onClick={async () => { if (!resourceFile) return; try { const form = new FormData(); form.append('file', resourceFile); await axios.post(`${API}/admin/resources/upload`, form, { headers: { 'Content-Type': 'multipart/form-data' } }); setResourceFile(null); await fetchResources(); } catch (e) { alert('Error uploading resource: ' + (e.response?.data?.detail || 'Please try again.')); } }}>Upload</Button>
                </div>
                <div className="flex items-center gap-2">
                  <Input placeholder="Link Title (e.g., Google Doc)" onChange={(e) => setResourcePreview({ ...(resourcePreview||{}), title: e.target.value })} />
                  <Input placeholder="https://..." onChange={(e) => setResourcePreview({ ...(resourcePreview||{}), url: e.target.value })} />
                  <Button variant="outline" onClick={async () => { if (!resourcePreview?.title || !resourcePreview?.url) return; await addResourceLink(resourcePreview.title, resourcePreview.url); setResourcePreview(null); }}>Add Link</Button>
                </div>
              </CardContent>
            </Card>
          )}
          <Card>
            <CardHeader>
              <CardTitle>Available Resources</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center gap-2 flex-wrap">
                <Input placeholder="Search by name" value={resourcesQuery} onChange={(e)=>setResourcesQuery(e.target.value)} className="w-48" />
                <Select value={resourcesKind} onValueChange={setResourcesKind}>
                  <SelectTrigger className="w-40"><SelectValue placeholder="Kind" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All</SelectItem>
                    <SelectItem value="file">Files</SelectItem>
                    <SelectItem value="link">Links</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={resourcesMime} onValueChange={setResourcesMime}>
                  <SelectTrigger className="w-40"><SelectValue placeholder="Type" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Types</SelectItem>
                    <SelectItem value="image">Images</SelectItem>
                    <SelectItem value="pdf">PDF</SelectItem>
                    <SelectItem value="office">Office Docs</SelectItem>
                  </SelectContent>
                </Select>
                <Button variant="outline" onClick={() => fetchResources(1)}>Apply</Button>
              </div>
              {resources.length === 0 ? (
                <p className="text-sm text-gray-600">No resources uploaded yet.</p>
              ) : (<>
                <div className="space-y-2">
                  {resources.map((r) => (
                    <div key={r.id} className="p-3 border rounded-md">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium">{r.filename}</p>
                          <p className="text-xs text-gray-500">{r.kind === 'link' ? 'External link' : `${Math.round((r.size||0)/1024)} KB`} • uploaded {new Date(r.uploaded_at).toLocaleString()}</p>
                        </div>
                        <div className="flex items-center gap-2">
                          {r.kind === 'link' ? (
                            <Button asChild variant="outline" size="sm"><a href={r.link_url} target="_blank" rel="noreferrer">Open</a></Button>
                          ) : (
                            <Button variant="outline" size="sm" onClick={async () => { try { const url = `${API}/resources/${r.id}/download`; const token = localStorage.getItem('token'); const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } }); if (!res.ok) throw new Error(await res.text() || `HTTP ${res.status}`); const blob = await res.blob(); const a = document.createElement('a'); const u = window.URL.createObjectURL(blob); a.href = u; a.setAttribute('download', r.filename || 'resource'); document.body.appendChild(a); a.click(); document.body.removeChild(a); window.URL.revokeObjectURL(u); } catch (e) { alert('Error downloading: ' + (e.message || 'Please try again.')); } }}>Download</Button>
                          )}
                          {user?.role === 'admin' && (<Button variant="destructive" size="sm" onClick={async () => { if (!window.confirm('Delete this resource?')) return; try { await axios.delete(`${API}/admin/resources/${r.id}`); fetchResources(resourcesPage); } catch (e) { alert('Error deleting resource: ' + (e.response?.data?.detail || 'Please try again.')); } }}>Delete</Button>)}
                        </div>
                      </div>
                      {/* Inline Preview for images and PDFs */}
                      {r.kind !== 'link' && r.content_type && (
                        <div className="mt-2">
                          {r.content_type.startsWith('image/') && (
                            <img src={`${API}/resources/${r.id}/download?token=${encodeURIComponent(localStorage.getItem('token')||'')}`} alt={r.filename} className="max-h-64 rounded border" />
                          )}
                          {r.content_type === 'application/pdf' && (
                            <iframe title={r.filename} src={`${API}/resources/${r.id}/download?token=${encodeURIComponent(localStorage.getItem('token')||'')}`} className="w-full h-96 border rounded" />
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
                <div className="flex items-center justify-between pt-2">
                  <div className="text-sm text-gray-600">Page {resourcesPage} of {Math.max(1, Math.ceil(resourcesTotal/20))} ({resourcesTotal} items)</div>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm" disabled={resourcesPage<=1} onClick={() => fetchResources(resourcesPage-1)}>Prev</Button>
                    <Button variant="outline" size="sm" disabled={resourcesPage>=Math.ceil(resourcesTotal/20)} onClick={() => fetchResources(resourcesPage+1)}>Next</Button>
                  </div>
                </div>
              </>)
              }
            </CardContent>
          </Card>
        </TabsContent>

        {/* Manage Annotations Modal */}
        <Dialog open={manageAnnOpen} onOpenChange={setManageAnnOpen}>
          <DialogContent className="max-w-4xl">
            <DialogHeader>
              <DialogTitle>Manage Annotations {manageAnnDoc ? `for ${manageAnnDoc.filename}` : ''}</DialogTitle>
              <DialogDescription>Filter and delete annotations for this document.</DialogDescription>
            </DialogHeader>
            <div className="flex items-center gap-3 mb-3 flex-wrap">
              <div>
                <Label className="text-xs">Annotator</Label>
                <Select value={filterAnnotator} onValueChange={(v) => { setFilterAnnotator(v); setTimeout(()=>{},0); }}>
                  <SelectTrigger className="w-48"><SelectValue placeholder="All" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All</SelectItem>
                    {Object.entries(userMap).map(([id, name]) => (<SelectItem key={id} value={id}>{name}</SelectItem>))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-xs">Type</Label>
                <Select value={filterType} onValueChange={setFilterType}>
                  <SelectTrigger className="w-40"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All</SelectItem>
                    <SelectItem value="tagged">Tagged</SelectItem>
                    <SelectItem value="skipped">Skipped</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label className="text-xs">Subject</Label>
                <Select value={filterSubject} onValueChange={setFilterSubject}>
                  <SelectTrigger className="w-40"><SelectValue placeholder="All" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All</SelectItem>
                    {[...new Set(docAnnotations.map(a => a.subject_id).filter(Boolean))].sort().map(sid => (
                      <SelectItem key={sid} value={sid}>{sid}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex-1 min-w-[200px]">
                <Label className="text-xs">Text contains</Label>
                <Input value={filterText} onChange={(e) => setFilterText(e.target.value)} placeholder="Search in sentence text or notes..." />
              </div>
              <div className="ml-auto flex items-center gap-2">
                <Button variant="destructive" size="sm" disabled={!selectedAnnIds.length} onClick={bulkDeleteDocAnnotations}>Delete selected</Button>
              </div>
            </div>
            <div className="max-h-[50vh] overflow-auto space-y-2">
              {docAnnotations
                .filter(a => filterAnnotator === 'all' || a.user_id === filterAnnotator)
                .filter(a => filterType === 'all' || (filterType === 'skipped' ? a.skipped : !a.skipped))
                .filter(a => filterSubject === 'all' || a.subject_id === filterSubject)
                .filter(a => { if (!filterText) return true; const t = filterText.toLowerCase(); const s = (a.sentence_text || '').toLowerCase(); const n = (a.notes || '').toLowerCase(); return s.includes(t) || n.includes(t); })
                .map((a) => (
                  <div key={a.id} className="flex items-start justify-between p-3 border rounded-md">
                    <div className="flex-1 pr-2">
                      <div className="flex items-center gap-2 mb-1">
                        <Checkbox checked={selectedAnnIds.includes(a.id)} onCheckedChange={() => toggleAnnChecked(a.id)} />
                        <Badge variant={a.skipped ? 'destructive' : 'outline'}>{a.skipped ? 'Skipped' : 'Tagged'}</Badge>
                        <span className="text-xs text-gray-500">by {userMap[a.user_id]?.slice(0, 20) || a.user_id?.slice(-6)}</span>
                        {a.subject_id && (<span className="text-xs text-gray-500">• Subject {a.subject_id}</span>)}
                        <span className="text-xs text-gray-500">• Index {a.sentence_index}</span>
        {/* Default Project Modal */}
        <Dialog open={defaultProjectModalOpen} onOpenChange={setDefaultProjectModalOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Set Default Project</DialogTitle>
              <DialogDescription>New uploads will use this project name.</DialogDescription>
            </DialogHeader>
            <div className="space-y-3">
              <Label>Project Name</Label>
              <Input value={defaultProjectInput} onChange={(e) => setDefaultProjectInput(e.target.value)} />
              <div className="flex items-center gap-2 justify-end pt-2">
                <Button variant="outline" onClick={() => setDefaultProjectModalOpen(false)}>Cancel</Button>
                <Button onClick={saveDefaultProject}>Save</Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

                      </div>
                      {!a.skipped && (
                        <div className="flex flex-wrap gap-1 mb-1">
                          {(a.tags || []).map((t, idx) => (
                            <Badge key={idx} variant={t.valence === 'positive' ? 'default' : 'destructive'} className="text-xs">{t.domain}: {t.tag} ({t.valence})</Badge>
                          ))}
                        </div>
                      )}
                      <div className="text-sm text-gray-700">{a.sentence_text}</div>
                      {a.notes && (<div className="text-xs text-gray-600 mt-1">Notes: {a.notes}</div>)}
                    </div>
                    <div>
                      <Button size="sm" variant="destructive" onClick={() => bulkDeleteAnnotations([a.id])}><Trash2 className="h-4 w-4" /></Button>
                    </div>
                  </div>
                ))}
            </div>
          </DialogContent>
        </Dialog>
      </Tabs>
    </div>
  );
};

// Home
const Home = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  return (
    <div className="max-w-5xl mx-auto p-6 space-y-6">
      <Card>
        <CardHeader><CardTitle>Welcome to the SDOH Annotation Tool</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            <Button variant="outline" onClick={() => navigate('/dashboard#documents')}>Documents</Button>
            <Button variant="outline" onClick={() => navigate('/dashboard#annotate')}>Annotate</Button>
            <Button variant="outline" onClick={() => navigate('/dashboard#resources')}>Resources</Button>
            {user?.role === 'admin' && (<Button variant="outline" onClick={() => navigate('/dashboard#admin')}>Admin</Button>)}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

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
          <Route path="/account" element={<AccountPage />} />
          <Route path="/" element={<Navigate to="/home" />} />
          <Route path="*" element={<Navigate to="/home" />} />
        </Routes>
      </main>
    </>
  );
};

export default App;