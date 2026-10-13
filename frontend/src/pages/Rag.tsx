import { Banner } from "../components/ui";

export function Rag() {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-slate-900">Research assistant</h1>
      <Banner kind="info">
        Coming in the next iteration: ask questions across trials and get answers with clickable
        source citations. The backend already serves it at <code>/api/rag/ask</code>.
      </Banner>
    </div>
  );
}
