import { queryOptions } from "@tanstack/react-query";
import { getCurrentUser } from "../api/auth";

export const currentUserQueryOptions = queryOptions({
  queryKey: ["currentUser"],
  queryFn: getCurrentUser,
});
