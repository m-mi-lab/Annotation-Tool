import React, { useState, useEffect } from "react";
import axios from "axios";
import { API } from "../api";
import { useAuth } from "../context/AuthContext";
import { useToast, ToastContainer } from "../hooks/useToast";
import { downloadBlob } from "../utils/download";
import AnnotationInterface from "./AnnotationInterface";
import AdminPanel from "./AdminPanel";
import AssignedDocsPanel from "./AssignedDocsPanel";
import ActiveDocsPanel from "./ActiveDocsPanel";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Label } from "./ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs";
import { Badge } from "./ui/badge";
import { Checkbox } from "./ui/checkbox";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./ui/select";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "./ui/dialog";
import { FileText, User, Upload, Tag, X, Settings, Trash2, Download } from "lucide-react";

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
  const [assignUsersModalOpen, setAssignUsersModalOpen] = useState(false);
  const [selectedDocForAssignment, setSelectedDocForAssignment] = useState(null);
  const [selectedUserIds, setSelectedUserIds] = useState([]);
  const [users, setUsers] = useState([]);

  const [resources, setResources] = useState([]);
  const [resourceFile, setResourceFile] = useState(null);
  const [resourcePreview, setResourcePreview] = useState(null);
  const [expandedResourceId, setExpandedResourceId] = useState(null);
  const [resourcesFiltered, setResourcesFiltered] = useState(false);

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
  const { toast, showToast, setToast } = useToast();
  const [expandedDomains, setExpandedDomains] = useState({});
  const [domainTagStats, setDomainTagStats] = useState(null);
  const [documentUserProgress, setDocumentUserProgress] = useState([]);

  const fetchDomainTagStats = async () => {
    try {
      const res = await axios.get(`${API}/analytics/domain-tag-stats`);
      setDomainTagStats(res.data);
    } catch {}
  };

  const fetchDocumentUserProgress = async () => {
    try {
      const res = await axios.get(`${API}/analytics/all-documents-user-progress`);
      setDocumentUserProgress(res.data || []);
    } catch {}
  };

  useEffect(() => {
    fetchDocuments(); fetchAnalytics(); fetchEnhancedAnalytics(); fetchTagStructure(); fetchResources(); fetchProjects(); fetchUsers(); fetchDomainTagStats(); fetchDocumentUserProgress();
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
  const fetchUsers = async () => {
    try { const res = await axios.get(`${API}/admin/users`); setUsers(res.data || []); } catch {}
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

  const fetchResources = async (page = resourcesPage, overrides = {}) => {
    try {
      const params = { page, page_size: 20 };
      const query = overrides.query !== undefined ? overrides.query : resourcesQuery;
      const kind = overrides.kind !== undefined ? overrides.kind : resourcesKind;
      const mime = overrides.mime !== undefined ? overrides.mime : resourcesMime;
      if (query) params.q = query;
      if (kind !== 'all') params.kind = kind;
      if (mime !== 'all') params.mime = mime;
      const res = await axios.get(`${API}/resources`, { params });
      setResources(res.data?.items || []);
      setResourcesTotal(res.data?.total || 0);
      setResourcesPage(res.data?.page || page);
      // Track if any filters are active after fetch
      setResourcesFiltered(!!query || kind !== 'all' || mime !== 'all');
    } catch {}
  };
  const addResourceLink = async (title, url) => { try { await axios.post(`${API}/admin/resources/link`, { title, url }); await fetchResources(); showToast('Link added', 'success'); } catch (e) { showToast('Error adding link: ' + (e.response?.data?.detail || 'Please try again.'), 'error'); } };

  const annotateDoc = async (documentId, options = {}) => {
    try {
      const res = await axios.get(`${API}/documents/${documentId}/sentences`);
      const items = res.data || [];
      setSentences(items); setSelectedDocument(documentId);
      let nextIndex = 0;
      if (typeof options.targetIndex === 'number') nextIndex = options.targetIndex;
      else if (options.targetSubject) { const idx = items.findIndex(s => s.subject_id === options.targetSubject); nextIndex = idx >= 0 ? idx : 0; }
      else { try { const r = await axios.get(`${API}/documents/${documentId}/resume`); if (typeof r.data?.index === 'number') nextIndex = r.data.index; } catch {} }
      nextIndex = Math.min(Math.max(0, nextIndex), Math.max(0, items.length - 1));
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
    const ok = await confirmAction('Are you sure you want to delete this annotation?');
    if (!ok) return;
    let prev; setSentences((p) => { prev = p; return p.map((s) => s.id !== sentenceId ? s : { ...s, annotations: (s.annotations || []).filter(a => a.id !== annotationId) }); });
    try { await axios.delete(`${API}/annotations/${annotationId}`); if (sentenceId) await refreshSentenceAnnotations(sentenceId); fetchAnalytics(); }
    catch (e) { if (prev) setSentences(prev); showToast('Error deleting annotation: ' + (e.response?.data?.detail || 'Not Found'), 'error'); }
  };

  const bulkDeleteAnnotations = async (annotationIds, sentenceId = null) => {
    if (!annotationIds?.length) return; if (!window.confirm(`Delete ${annotationIds.length} annotations?`)) return;
    try { await axios.post(`${API}/annotations/bulk-delete`, { annotation_ids: annotationIds }); if (sentenceId) await refreshSentenceAnnotations(sentenceId); if (manageAnnOpen && manageAnnDoc) await openManageAnnotations(manageAnnDoc); fetchAnalytics(); }
    catch (e) { showToast('Error bulk-deleting annotations: ' + (e.response?.data?.detail || 'Please try again.'), 'error'); }
  };

  const createAnnotation = async (sentenceId, tags, notes, skipped = false, confidence = null, duration_ms = null) => {
    try { 
      const payload = { sentence_id: sentenceId, tags, notes, skipped };
      if (confidence !== null) payload.confidence = confidence;
      if (duration_ms !== null) payload.duration_ms = duration_ms;
      await axios.post(`${API}/annotations`, payload); 
      await refreshSentenceAnnotations(sentenceId); 
      fetchAnalytics(); 
    }
    catch (e) { showToast('Error saving annotation: ' + (e.response?.data?.detail || 'Please try again.'), 'error'); }
  };

  const clearAllDocumentAnnotations = async (documentId) => {
    try {
      const res = await axios.delete(`${API}/annotations/document/${documentId}/clear-all`);
      showToast(`Deleted ${res.data.deleted} annotations`, 'success');
      // Refresh the sentences to update the UI
      await annotateDoc(documentId, { targetIndex: currentSentenceIndex });
      fetchAnalytics();
    } catch (e) {
      showToast('Error clearing annotations: ' + (e.response?.data?.detail || 'Please try again.'), 'error');
    }
  };

  const deleteDocument = async (documentId) => {
    if (!window.confirm('Delete this document and all associated annotations?')) return;
    try { setDocuments(documents.filter(d => d.id !== documentId)); await axios.delete(`${API}/admin/documents/${documentId}`); fetchAnalytics(); showToast('Document deleted', 'success'); }
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
  const [confirmState, setConfirmState] = useState({ open: false, message: '', resolve: null });
  const confirmAction = (message) => new Promise((resolve) => { setConfirmState({ open: true, message, resolve }); });


  const uploadResource = async () => { if (!resourceFile) return; const form = new FormData(); form.append('file', resourceFile); try { await axios.post(`${API}/admin/resources/upload`, form, { headers: { 'Content-Type': 'multipart/form-data' } }); setResourceFile(null); fetchResources(); showToast('Resource uploaded', 'success'); } catch (e) { showToast('Error uploading resource: ' + (e.response?.data?.detail || 'Please try again.'), 'error'); } };
  const downloadResource = async (resItem) => { try { const url = `${API}/resources/${resItem.id}/download`; const token = localStorage.getItem('token'); const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } }); if (!res.ok) throw new Error(await res.text() || `HTTP ${res.status}`); const blob = await res.blob(); const filename = resItem.filename || 'resource'; const a = document.createElement('a'); const u = window.URL.createObjectURL(blob); a.href = u; a.setAttribute('download', filename); document.body.appendChild(a); a.click(); document.body.removeChild(a); window.URL.revokeObjectURL(u); showToast('Download started', 'info'); } catch (e) { showToast('Error downloading resource: ' + (e.message || 'Please try again.'), 'error'); } };

  const deleteResource = async (resItem) => { const ok = await confirmAction(`Delete resource "${resItem.filename}"?`); if (!ok) return; try { await axios.delete(`${API}/admin/resources/${resItem.id}`); fetchResources(); showToast('Resource deleted', 'success'); } catch (e) { showToast('Error deleting resource: ' + (e.response?.data?.detail || 'Please try again.'), 'error'); } };


  const openManageAnnotations = async (doc) => {
    setManageAnnDoc(doc); setManageAnnOpen(true);
    try {
      const res = await axios.get(`${API}/documents/${doc.id}/annotations`);
      setDocAnnotations(res.data || []);
      setSelectedAnnIds([]); setSelectAllAnns(false);
      try { if (user?.role === 'admin') { const usersRes = await axios.get(`${API}/admin/users`); const map = {}; (usersRes.data || []).forEach(u => { map[u.id] = u.full_name || u.email; }); setUserMap(map); } } catch {}
    } catch (e) { showToast('Error loading annotations: ' + (e.response?.data?.detail || 'Please try again.'), 'error'); }
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
        <TabsList className="inline-flex h-12 items-center justify-start rounded-lg bg-muted p-1 text-muted-foreground w-auto">
          {tabsToShow.map((tab) => (
            <TabsTrigger key={tab.value} value={tab.value} className="inline-flex items-center whitespace-nowrap rounded-md px-4 py-2 text-sm font-medium data-[state=active]:bg-card data-[state=active]:text-gray-900 space-x-2">
              <tab.icon className="h-4 w-4" />
              <span>{tab.label}</span>
            </TabsTrigger>
          ))}
        </TabsList>

        {user?.role === 'admin' && (
          <TabsContent value="admin" className="space-y-6" id="admin">
            <AdminPanel />

            <Card>
              <CardHeader><CardTitle>Analytics Overview</CardTitle></CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <Card><CardContent className="p-4"><div className="text-sm text-muted-foreground">Documents</div><div className="text-2xl font-semibold">{analytics.total_documents || 0}</div></CardContent></Card>
                  <Card><CardContent className="p-4"><div className="text-sm text-muted-foreground">Sentences</div><div className="text-2xl font-semibold">{analytics.total_sentences || 0}</div></CardContent></Card>
                  <Card><CardContent className="p-4"><div className="text-sm text-muted-foreground">Annotations</div><div className="text-2xl font-semibold">{analytics.total_annotations || 0}</div></CardContent></Card>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle>Category Counts by Domain</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                {/* Domain Summary Chart */}
                <div>
                  <h4 className="font-medium mb-2">Total Tags per Domain</h4>
                  <img src={`${API}/analytics/tag-prevalence-chart?token=${encodeURIComponent(localStorage.getItem('token')||'')}`} alt="Domain Summary Chart" className="w-full max-w-3xl rounded border" />
                </div>
                
                {/* Expandable Per-Domain Charts */}
                <div className="space-y-2">
                  <h4 className="font-medium">Tag Distribution by Domain</h4>
                  <p className="text-sm text-muted-foreground mb-3">Click on a domain to expand and see individual tag counts</p>
                  {domainTagStats?.domains?.map((domain, idx) => (
                    <div key={domain} className="border rounded-lg">
                      <button 
                        className="w-full p-3 flex items-center justify-between text-left hover:bg-muted/50 rounded-lg"
                        onClick={() => setExpandedDomains(prev => ({...prev, [domain]: !prev[domain]}))}
                      >
                        <span className="font-medium">{domain}</span>
                        <div className="flex items-center gap-3">
                          <Badge variant="secondary">{domainTagStats?.domain_totals?.[domain] || 0} tags</Badge>
                          <span className="text-muted-foreground/60">{expandedDomains[domain] ? '▼' : '▶'}</span>
                        </div>
                      </button>
                      {expandedDomains[domain] && (
                        <div className="p-3 pt-0 border-t bg-muted/50">
                          <img 
                            src={`${API}/analytics/domain-chart/${encodeURIComponent(domain)}?token=${encodeURIComponent(localStorage.getItem('token')||'')}`} 
                            alt={`${domain} Tags Chart`} 
                            className="w-full max-w-2xl rounded border bg-card"
                          />
                        </div>
                      )}
                    </div>
                  ))}
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
                      <tr className="text-left text-muted-foreground">
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
                              <div className="h-2 bg-muted rounded"><div className="h-2 bg-blue-600 rounded" style={{ width: `${Math.round((p.progress||0)*100)}%` }}></div></div>
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

            <Card>
              <CardHeader><CardTitle>Per-User Document Progress</CardTitle></CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground mb-4">Progress bars showing each user's annotation completion per document</p>
                <div className="space-y-4">
                  {documentUserProgress.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No documents with assigned users found.</p>
                  ) : (
                    documentUserProgress.map((doc) => (
                      <div key={doc.document_id} className="border rounded-lg p-3">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium">{doc.filename}</span>
                          <span className="text-xs text-muted-foreground">{doc.total_sentences} sentences</span>
                        </div>
                        {doc.user_progress.length === 0 ? (
                          <p className="text-xs text-muted-foreground/60">No annotators assigned</p>
                        ) : (
                          <div className="space-y-2">
                            {doc.user_progress.map((up) => (
                              <div key={up.user_id} className="flex items-center gap-3">
                                <span className="text-sm w-32 truncate" title={up.user_name}>{up.user_name}</span>
                                <div className="flex-1 h-4 bg-muted rounded relative">
                                  <div 
                                    className={`h-4 rounded ${up.progress === 100 ? 'bg-green-500' : 'bg-blue-500'}`}
                                    style={{ width: `${up.progress}%` }}
                                  />
                                  <span className="absolute inset-0 flex items-center justify-center text-xs font-medium text-white mix-blend-difference">
                                    {up.annotated}/{up.total} ({up.progress}%)
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle>User Activity Log</CardTitle>
                  <div className="flex items-center gap-2">
                    <Select 
                      value={filterAnnotator} 
                      onValueChange={setFilterAnnotator}
                    >
                      <SelectTrigger className="w-48">
                        <SelectValue placeholder="All Users" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="all">All Users</SelectItem>
                        {users.map(u => (
                          <SelectItem key={u.id} value={u.id}>{u.full_name || u.email}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={async () => {
                        try {
                          let url = `${API}/admin/download/activity-log`;
                          if (filterAnnotator !== 'all') {
                            url += `?user_id=${filterAnnotator}`;
                          }
                          const token = localStorage.getItem('token');
                          const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
                          if (!res.ok) throw new Error(await res.text() || `HTTP ${res.status}`);
                          const blob = await res.blob();
                          const a = document.createElement('a');
                          const u = window.URL.createObjectURL(blob);
                          a.href = u;
                          const selectedUser = users.find(u => u.id === filterAnnotator);
                          const filename = filterAnnotator === 'all' 
                            ? `activity_log_all_users_${new Date().toISOString().split('T')[0]}.csv`
                            : `activity_log_${(selectedUser?.full_name || selectedUser?.email || 'user').replace(/[^a-z0-9]/gi, '_')}_${new Date().toISOString().split('T')[0]}.csv`;
                          a.setAttribute('download', filename);
                          document.body.appendChild(a);
                          a.click();
                          document.body.removeChild(a);
                          window.URL.revokeObjectURL(u);
                          showToast('Activity log downloaded', 'success');
                        } catch (e) {
                          showToast('Error downloading activity log: ' + (e.message || 'Please try again.'), 'error');
                        }
                      }}
                    >
                      <Download className="h-4 w-4 mr-1" /> Download Activity Log
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Download a comprehensive CSV log of user activities including page navigation, tag clicks, and sentence transitions with timestamps. 
                  Select a specific user from the dropdown to download their activities only, or choose "All Users" for the complete log.
                </p>
              </CardContent>
            </Card>
          </TabsContent>
        )}

        <TabsContent value="documents" className="space-y-4" id="documents">
          <div className="flex items-center justify-between">
            <CardTitle>Documents ({documents.length})</CardTitle>

            {user?.role === 'admin' && (
              <div className="flex items-center gap-2 p-2 bg-muted border rounded">
                <div className="flex items-center gap-2 mr-2">
                  <Checkbox id="selectAllDocs" checked={selectAllDocs} onCheckedChange={() => { if (selectAllDocs) { setSelectedDocIds([]); setSelectAllDocs(false); } else { setSelectedDocIds(documents.map(d => d.id)); setSelectAllDocs(true); } }} />
                  <Label htmlFor="selectAllDocs" className="text-foreground">Select all</Label>
                  <Button variant="outline" size="sm" onClick={() => { setSelectedDocIds([]); setSelectAllDocs(false); }}>Deselect all</Button>
                </div>
                <div className="flex items-center gap-2 pl-4 ml-4 border-l">
                  <input id="csvUploadInput" type="file" accept=".csv" multiple onChange={(e) => { setUploadFile(e.target.files?.length ? Array.from(e.target.files) : null); }} className="text-foreground" />
                  <Button variant="secondary" size="sm" disabled={!uploadFile} onClick={async () => { if (!uploadFile) return; const files = Array.isArray(uploadFile) ? uploadFile : [uploadFile]; let ok = 0; for (const f of files) { const form = new FormData(); form.append('file', f); try { await axios.post(`${API}/documents/upload`, form, { headers: { 'Content-Type': 'multipart/form-data' } }); ok++; } catch (err) { showToast(`Error uploading ${f.name}: ${err.response?.data?.detail || err.message}`, 'error'); } } setUploadFile(null); fetchDocuments(); fetchAnalytics(); if (ok > 0) showToast(`${ok} CSV${ok > 1 ? 's' : ''} uploaded`, 'success'); const el = document.getElementById('csvUploadInput'); if (el) el.value = ''; }}>
                    <Upload className="h-4 w-4 mr-1" /> Upload CSV{uploadFile && Array.isArray(uploadFile) && uploadFile.length > 1 ? `s (${uploadFile.length})` : ''}
                  </Button>
                </div>
                <Button variant="destructive" size="sm" onClick={async () => { if (!selectedDocIds.length) return; const ok = await confirmAction(`Delete ${selectedDocIds.length} documents?`); if (!ok) return; try { await axios.post(`${API}/admin/documents/bulk-delete`, { ids: selectedDocIds }); setDocuments(prev => prev.filter(d => !selectedDocIds.includes(d.id))); setSelectedDocIds([]); setSelectAllDocs(false); fetchAnalytics(); showToast('Documents deleted', 'success'); } catch (e) { showToast('Error bulk-deleting documents: ' + (e.response?.data?.detail || 'Please try again.'), 'error'); } }} disabled={!selectedDocIds.length}>Delete selected</Button>
              </div>
            )}
          </div>
          <div className="grid gap-4">
            {documents.length === 0 && (
              <Card>
                <CardContent className="text-center py-12">
                  <FileText className="h-12 w-12 text-muted-foreground/60 mx-auto mb-4" />
                  <p className="text-lg font-medium">No documents yet</p>
                  <p className="text-sm text-muted-foreground mt-1">{user?.role === 'admin' ? 'Upload a CSV file above to get started' : 'Ask an admin to upload documents for annotation'}</p>
                </CardContent>
              </Card>
            )}
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
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {doc.total_sentences} sentences • Uploaded {new Date(doc.upload_date || doc.created_at).toLocaleDateString()}
                      </p>
                      {doc.last_modified_by && Object.keys(doc.last_modified_by).length > 0 && (
                        <p className="text-xs text-muted-foreground mt-1">
                          Last edited: {Object.entries(doc.last_modified_by || {}).map(([userId, timestamp]) => {
                            const date = new Date(timestamp).toLocaleDateString();
                            const time = new Date(timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
                            return `${date} ${time} (User: ${userId.slice(-6)})`;
                          }).join(', ')}
                        </p>
                      )}
                      {doc.description && (<p className="text-xs text-muted-foreground mt-1">{doc.description}</p>)}
                      {doc.assigned_users && doc.assigned_users.length > 0 && (
                        <p className="text-xs text-muted-foreground mt-1">
                          <span className="font-medium">Assigned users:</span> {doc.assigned_users.map(uid => {
                            const u = users.find(user => user.id === uid);
                            return u ? u.full_name || u.email : uid.slice(-6);
                          }).join(', ')}
                        </p>
                      )}
                    </div>
                    <div className="flex items-center space-x-2">
                      <Button onClick={() => annotateDoc(doc.id)} variant="outline">Annotate</Button>
                      {user?.role === 'admin' && (
                        <>
                          <Button variant="outline" size="sm" onClick={() => { setSelectedDocForAssignment(doc); setSelectedUserIds(doc.assigned_users || []); setAssignUsersModalOpen(true); }}>
                            <User className="h-4 w-4 mr-1" /> Assign Users
                          </Button>
                          <Button variant="secondary" size="sm" onClick={() => downloadAnnotatedCsvInline(doc)}><Download className="h-4 w-4 mr-1" /> Download annotated CSV</Button>
                          <Button variant="outline" size="sm" onClick={async () => { try { const url = `${API}/admin/download/annotated-paragraphs/${doc.id}`; const token = localStorage.getItem('token'); let res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } }); if (!res.ok) throw new Error(await res.text() || `HTTP ${res.status}`); const blob = await res.blob(); const a = document.createElement('a'); const u = window.URL.createObjectURL(blob); a.href = u; a.setAttribute('download', `annotated_paragraphs_${doc.filename || 'document'}.csv`); document.body.appendChild(a); a.click(); document.body.removeChild(a); window.URL.revokeObjectURL(u); showToast('Paragraphs CSV generated', 'success'); } catch (e) { showToast('Error downloading annotated paragraphs: ' + (e.message || 'Please try again.'), 'error'); } }}><Download className="h-4 w-4 mr-1" /> Download annotated paragraphs</Button>
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
          <AssignedDocsPanel onOpenDoc={(id, opts) => annotateDoc(id, opts)} />
          <ActiveDocsPanel onOpenDoc={(id, opts) => annotateDoc(id, opts)} />
          {!selectedDocument ? (
            <Card>
              <CardContent className="text-center py-8">
                <Tag className="h-12 w-12 text-muted-foreground/60 mx-auto mb-4" />
                <p className="text-muted-foreground mb-2">Select a document from the Documents tab to start annotating</p>
                <Button variant="outline" onClick={() => setActiveTab('documents')}>Browse Documents</Button>
              </CardContent>
            </Card>
          ) : sentences.length === 0 ? (
            <Card>
              <CardContent className="text-center py-8">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="text-muted-foreground">Loading sentences for annotation...</p>
              </CardContent>
            </Card>
          ) : (
            <AnnotationInterface
              sentences={sentences}
              currentIndex={currentSentenceIndex}
              onIndexChange={setCurrentSentenceIndex}
              tagStructure={tagStructure}
              onAnnotate={createAnnotation}
              onDeleteAnnotation={deleteAnnotation}
              onBulkDeleteAnnotations={bulkDeleteAnnotations}
              currentDocName={(documents.find(d => d.id === selectedDocument) || {}).filename}
              documentId={selectedDocument}
              confirmAction={confirmAction}
              onClearAllAnnotations={clearAllDocumentAnnotations}
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
                <Input 
                  placeholder="Search by name" 
                  value={resourcesQuery} 
                  onChange={(e) => setResourcesQuery(e.target.value)} 
                  onKeyDown={(e) => { if (e.key === 'Enter') fetchResources(1); }}
                  className="w-48" 
                />
                <Select value={resourcesKind} onValueChange={(val) => { setResourcesKind(val); fetchResources(1, { kind: val }); }}>
                  <SelectTrigger className="w-40"><SelectValue placeholder="Kind" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All</SelectItem>
                    <SelectItem value="file">Files</SelectItem>
                    <SelectItem value="link">Links</SelectItem>
                  </SelectContent>
                </Select>
                <Select value={resourcesMime} onValueChange={(val) => { setResourcesMime(val); fetchResources(1, { mime: val }); }}>
                  <SelectTrigger className="w-40"><SelectValue placeholder="Type" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Types</SelectItem>
                    <SelectItem value="image">Images</SelectItem>
                    <SelectItem value="pdf">PDF</SelectItem>
                    <SelectItem value="office">Office Docs</SelectItem>
                  </SelectContent>
                </Select>
                <Button variant="outline" onClick={() => fetchResources(1)}>Search</Button>
                {resourcesFiltered && (
                  <Button 
                    variant="ghost" 
                    size="sm"
                    onClick={() => {
                      setResourcesQuery('');
                      setResourcesKind('all');
                      setResourcesMime('all');
                      fetchResources(1, { query: '', kind: 'all', mime: 'all' });
                    }}
                  >
                    <X className="h-4 w-4 mr-1" /> Clear Filters
                  </Button>
                )}
              </div>
              {resources.length === 0 ? (
                <p className="text-sm text-muted-foreground">No resources uploaded yet.</p>
              ) : (<>
                <div className="space-y-2">
                  {resources.map((r) => (
                    <div key={r.id} className="p-3 border rounded-md">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <p className="font-medium">{r.filename}</p>
                          <p className="text-xs text-muted-foreground">{r.kind === 'link' ? 'External link' : `${Math.round((r.size||0)/1024)} KB`} • uploaded {new Date(r.uploaded_at).toLocaleString()}</p>
                        </div>
                        <div className="flex items-center gap-2">
                          {r.kind === 'link' ? (
                            <Button asChild variant="outline" size="sm"><a href={r.link_url} target="_blank" rel="noreferrer">Open</a></Button>
                          ) : (
                            <>
                              {r.content_type && (r.content_type.startsWith('image/') || r.content_type === 'application/pdf' || r.content_type.includes('word') || r.content_type.includes('msword') || r.content_type.includes('spreadsheet') || r.content_type.includes('excel') || r.filename.endsWith('.doc') || r.filename.endsWith('.docx') || r.filename.endsWith('.xls') || r.filename.endsWith('.xlsx') || r.filename.endsWith('.png') || r.filename.endsWith('.jpg') || r.filename.endsWith('.jpeg')) && (
                                <Button 
                                  variant="outline" 
                                  size="sm" 
                                  onClick={() => setExpandedResourceId(expandedResourceId === r.id ? null : r.id)}
                                >
                                  {expandedResourceId === r.id ? 'Hide Preview' : 'Show Preview'}
                                </Button>
                              )}
                              <Button variant="outline" size="sm" onClick={async () => { 
                                try { 
                                  const url = `${API}/resources/${r.id}/download`; 
                                  const token = localStorage.getItem('token'); 
                                  const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } }); 
                                  if (!res.ok) throw new Error(await res.text() || `HTTP ${res.status}`); 
                                  const blob = await res.blob(); 
                                  const a = document.createElement('a'); 
                                  const u = window.URL.createObjectURL(blob); 
                                  a.href = u; 
                                  a.setAttribute('download', r.filename || 'resource'); 
                                  document.body.appendChild(a); 
                                  a.click(); 
                                  document.body.removeChild(a); 
                                  window.URL.revokeObjectURL(u); 
                                  showToast('Resource downloaded', 'success');
                                } catch (e) { 
                                  showToast('Error downloading: ' + (e.message || 'Please try again.'), 'error'); 
                                } 
                              }}>Download</Button>
                            </>
                          )}
                          {user?.role === 'admin' && (
                            <Button 
                              variant="destructive" 
                              size="sm" 
                              onClick={async () => { 
                                const confirmed = await new Promise((resolve) => {
                                  setConfirmState({
                                    open: true,
                                    message: `Delete resource "${r.filename}"?`,
                                    resolve
                                  });
                                });
                                if (!confirmed) return;
                                try { 
                                  await axios.delete(`${API}/admin/resources/${r.id}`); 
                                  showToast('Resource deleted', 'success');
                                  fetchResources(resourcesPage); 
                                } catch (e) { 
                                  showToast('Error deleting resource: ' + (e.response?.data?.detail || 'Please try again.'), 'error'); 
                                } 
                              }}
                            >
                              Delete
                            </Button>
                          )}
                        </div>
                      </div>
                      {/* Collapsible Preview for images, PDFs, Word docs, and Excel files */}
                      {expandedResourceId === r.id && r.kind !== 'link' && (
                        <div className="mt-3 pt-3 border-t">
                          {(r.content_type?.startsWith('image/') || r.filename?.match(/\.(png|jpg|jpeg|gif|svg)$/i)) && (
                            <img src={`${API}/resources/${r.id}/download?token=${encodeURIComponent(localStorage.getItem('token')||'')}`} alt={r.filename} className="max-h-64 rounded border" />
                          )}
                          {r.content_type === 'application/pdf' && (
                            <iframe title={r.filename} src={`${API}/resources/${r.id}/download?token=${encodeURIComponent(localStorage.getItem('token')||'')}`} className="w-full h-96 border rounded" />
                          )}
                          {(r.content_type?.includes('word') || r.content_type?.includes('msword') || r.filename?.match(/\.docx?$/i)) && (
                            <iframe title={r.filename} src={`${API}/resources/${r.id}/preview?token=${encodeURIComponent(localStorage.getItem('token')||'')}`} className="w-full h-96 border rounded bg-card" />
                          )}
                          {(r.content_type?.includes('spreadsheet') || r.content_type?.includes('excel') || r.filename?.match(/\.xlsx?$/i)) && (
                            <iframe title={r.filename} src={`${API}/resources/${r.id}/preview?token=${encodeURIComponent(localStorage.getItem('token')||'')}`} className="w-full h-96 border rounded bg-card" />
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
                <div className="flex items-center justify-between pt-2">
                  <div className="text-sm text-muted-foreground">Page {resourcesPage} of {Math.max(1, Math.ceil(resourcesTotal/20))} ({resourcesTotal} items)</div>
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
                <Button 
                  variant="outline" 
                  size="sm" 
                  disabled={filterAnnotator === 'all'}
                  onClick={async () => {
                    if (!manageAnnDoc || filterAnnotator === 'all') return;
                    try {
                      const url = `${API}/admin/download/annotated-csv-inline/${manageAnnDoc.id}?user_id=${filterAnnotator}`;
                      const token = localStorage.getItem('token');
                      const res = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
                      if (!res.ok) throw new Error(await res.text() || `HTTP ${res.status}`);
                      const blob = await res.blob();
                      const a = document.createElement('a');
                      const u = window.URL.createObjectURL(blob);
                      a.href = u;
                      const userName = userMap[filterAnnotator] || filterAnnotator;
                      a.setAttribute('download', `${userName}_annotations_${manageAnnDoc.filename}.csv`);
                      document.body.appendChild(a);
                      a.click();
                      document.body.removeChild(a);
                      window.URL.revokeObjectURL(u);
                      showToast(`Downloaded CSV for ${userName}`, 'success');
                    } catch (e) {
                      showToast('Error downloading CSV: ' + (e.message || 'Please try again.'), 'error');
                    }
                  }}
                >
                  <Download className="h-4 w-4 mr-1" /> Download for selected user
                </Button>
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
                        <span className="text-xs text-muted-foreground">by {userMap[a.user_id]?.slice(0, 20) || a.user_id?.slice(-6)}</span>
                        {a.subject_id && (<span className="text-xs text-muted-foreground">• Subject {a.subject_id}</span>)}
                        <span className="text-xs text-muted-foreground">• Index {a.sentence_index}</span>
                      </div>
                      {!a.skipped && (
                        <div className="flex flex-wrap gap-1 mb-1">
                          {(a.tags || []).map((t, idx) => (
                            <Badge key={idx} variant={t.valence === 'positive' ? 'default' : 'destructive'} className="text-xs">{t.domain}: {t.tag} ({t.valence})</Badge>
                          ))}
                        </div>
                      )}
                      <div className="text-sm text-foreground">{a.sentence_text}</div>
                      {a.notes && (<div className="text-xs text-muted-foreground mt-1">Notes: {a.notes}</div>)}
                    </div>
                    <div>
                      <Button size="sm" variant="destructive" onClick={() => bulkDeleteAnnotations([a.id])}><Trash2 className="h-4 w-4" /></Button>
                    </div>
                  </div>
                ))}
            </div>
          </DialogContent>
        </Dialog>

        {/* Assign Users Modal */}
        <Dialog open={assignUsersModalOpen} onOpenChange={setAssignUsersModalOpen}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Assign Users to Document</DialogTitle>
              <DialogDescription>Select users who can annotate this document: {selectedDocForAssignment?.filename}</DialogDescription>
            </DialogHeader>
            <div className="space-y-3">
              <Label>Select Users</Label>
              <div className="max-h-64 overflow-y-auto border rounded p-2 space-y-2">
                {users.filter(u => u.role !== 'admin').length === 0 ? (
                  <p className="text-sm text-muted-foreground">No annotators available to assign.</p>
                ) : (
                  users.filter(u => u.role !== 'admin').map((u) => (
                    <div key={u.id} className="flex items-center space-x-2">
                      <Checkbox 
                        checked={selectedUserIds.includes(u.id)} 
                        onCheckedChange={(checked) => {
                          if (checked) {
                            setSelectedUserIds(prev => [...prev, u.id]);
                          } else {
                            setSelectedUserIds(prev => prev.filter(id => id !== u.id));
                          }
                        }} 
                      />
                      <Label className="cursor-pointer">{u.full_name || u.email}</Label>
                    </div>
                  ))
                )}
              </div>
              <div className="flex items-center gap-2 justify-end pt-2">
                <Button variant="outline" onClick={() => { setAssignUsersModalOpen(false); setSelectedDocForAssignment(null); setSelectedUserIds([]); }}>Cancel</Button>
                <Button onClick={async () => {
                  if (!selectedDocForAssignment) return;
                  try {
                    await axios.post(`${API}/admin/documents/${selectedDocForAssignment.id}/assign-users`, { user_ids: selectedUserIds });
                    showToast('Users assigned successfully', 'success');
                    fetchDocuments();
                    setAssignUsersModalOpen(false);
                    setSelectedDocForAssignment(null);
                    setSelectedUserIds([]);
                  } catch (e) {
                    showToast('Error assigning users: ' + (e.response?.data?.detail || e.message || 'Please try again.'), 'error');
                  }
                }}>Save</Button>
              </div>
            </div>
          </DialogContent>
        </Dialog>

        {/* Global Confirm Dialog */}
        <Dialog open={confirmState.open} onOpenChange={(v) => { if (!v) { confirmState.resolve && confirmState.resolve(false); setConfirmState({ open: false, message: '', resolve: null }); } }}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Confirm</DialogTitle>
              <DialogDescription>{confirmState.message}</DialogDescription>
            </DialogHeader>
            <div className="flex items-center gap-2 justify-end pt-2">
              <Button variant="outline" onClick={() => { confirmState.resolve && confirmState.resolve(false); setConfirmState({ open: false, message: '', resolve: null }); }}>Cancel</Button>
              <Button onClick={() => { confirmState.resolve && confirmState.resolve(true); setConfirmState({ open: false, message: '', resolve: null }); }}>Confirm</Button>
            </div>
          </DialogContent>
        </Dialog>
      </Tabs>
      <ToastContainer toast={toast} onClose={() => setToast(null)} />
    </div>
  );
};

export default Dashboard;
