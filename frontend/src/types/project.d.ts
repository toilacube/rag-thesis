interface Project {
  id: number;
  user_id: number;
  permission_ids: number[];
  project_name: string;
  description: string;
  created_at: string;
  updated_at?: string;
  documents_count?: number;
}
