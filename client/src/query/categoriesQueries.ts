import { queryOptions } from "@tanstack/react-query";

import { listCategories } from "../api/categories";

export const categoriesQueryOptions = queryOptions({
  queryKey: ["categories"],
  queryFn: listCategories,
});
