import { queryOptions } from "@tanstack/react-query";

import { listAccounts } from "../api/accounts";

export const accountsQueryOptions = queryOptions({
  queryKey: ["accounts"],
  queryFn: listAccounts,
});
