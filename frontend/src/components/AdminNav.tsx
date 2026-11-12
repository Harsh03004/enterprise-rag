import { Link } from "react-router-dom";

const LINKS = [
  { to: "/admin", label: "Analytics" },
  { to: "/admin/content", label: "Content" },
  { to: "/admin/evaluations", label: "Evaluations" },
  { to: "/admin/settings", label: "RAG settings" },
];

export default function AdminNav({ active }: { active: string }) {
  return (
    <nav className="dashboard-nav" aria-label="Admin dashboards">
      {LINKS.map((link) => (
        <Link key={link.to} to={link.to} className={link.to === active ? "dashboard-nav-active" : undefined}>
          {link.label}
        </Link>
      ))}
    </nav>
  );
}
