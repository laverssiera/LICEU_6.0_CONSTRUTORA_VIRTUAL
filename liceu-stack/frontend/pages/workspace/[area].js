import { useRouter } from "next/router";

import Workspace from "./index";

export default function WorkspaceArea() {
  const router = useRouter();
  const area = String(router.query.area || "dashboard");

  return <Workspace key={area} activeAreaKey={area} />;
}
