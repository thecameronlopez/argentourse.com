import { api } from "./http";

export type Account = {
  id: string;
  user_id: string;
  name: string;
  institution: string;
  account_type: string;
  current_balance_cents: number;
  created_at: string;
  updated_at: string;
};

export async function listAccounts() {
  const { data } = await api.get<Account[]>("/accounts");
  return data;
}
