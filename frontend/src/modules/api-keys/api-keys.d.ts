export interface APIKey {
  id: number;
  name: string;
  key: string;
  is_active: boolean;
  last_used_at: string | null;
  created_at: string;
  updated_at: string;
}
