import { api } from "./http";

export type Category = {
  id: string;
  user_id: string;
  name: string;
  category_type: string;
  created_at: string;
  updated_at: string;
};

export async function listCategories() {
  const { data } = await api.get<Category[]>("/categories");
  return data;
}
