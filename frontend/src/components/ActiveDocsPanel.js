import React, { useState, useEffect } from "react";
import axios from "axios";
import { API } from "../api";
import { useAuth } from "../context/AuthContext";
import { Button } from "./ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "./ui/card";
import { Badge } from "./ui/badge";

const ActiveDocsPanel = ({ onOpenDoc }) => {
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isExpanded, setIsExpanded] = useState(true);

  useEffect(() => {
    (async () => {
      try { setLoading(true); const res = await axios.get(`${API}/annotations/active-docs`, { params: { scope: "me" } }); setItems(res.data || []); } catch {} finally { setLoading(false); }
    })();
  }, []);

  if (!items.length && !loading) return null;

  return (
    <Card>
      <CardHeader className="cursor-pointer" onClick={() => setIsExpanded(!isExpanded)}>
        <div className="flex items-center gap-2">
          <span className="text-muted-foreground">{isExpanded ? "▼" : "▶"}</span>
          <CardTitle>My Active Documents</CardTitle>
          <Badge variant="secondary">{items.length}</Badge>
        </div>
      </CardHeader>
      {isExpanded && (
        <CardContent>
          {loading ? (
            <div className="space-y-2">
              {[1, 2].map((i) => (
                <div key={i} className="p-3 border rounded-md animate-pulse">
                  <div className="flex items-center justify-between">
                    <div><div className="h-4 w-32 bg-muted rounded mb-1" /><div className="h-3 w-20 bg-muted rounded" /></div>
                    <div className="h-2 w-64 bg-muted rounded" />
                    <div className="h-8 w-20 bg-muted rounded" />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-3">
              {items.map((it) => (
                <div key={it.document_id} className="p-3 border rounded-md">
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium">{it.filename}</div>
                      <div className="text-xs text-muted-foreground">{it.annotated_count}/{it.total_sentences} sentences</div>
                    </div>
                    <div className="w-64">
                      <div className="h-2 bg-muted rounded"><div className="h-2 bg-blue-600 rounded" style={{ width: `${Math.round(it.progress * 100)}%` }} /></div>
                    </div>
                    <div className="flex items-center gap-2">
                      {typeof it.last_annotation_index === "number" && (
                        <Button size="sm" variant="outline" onClick={() => onOpenDoc(it.document_id, { targetIndex: it.last_annotation_index })}>Resume</Button>
                      )}
                    </div>
                  </div>
                  {it.subjects && it.subjects.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-2">
                      {it.subjects.slice(0, 30).map((sub) => (
                        <span key={sub} className="px-2 py-1 text-xs rounded bg-muted border">{sub}</span>
                      ))}
                      {it.subjects.length > 30 && <span className="text-xs text-muted-foreground">+{it.subjects.length - 30} more</span>}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      )}
    </Card>
  );
};

export default ActiveDocsPanel;
