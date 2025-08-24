/* eslint-disable */
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

// ... existing code remains ...

// Add projects analytics state and fetchers inside Dashboard component
// find markers and augment