"use client";

import { useState } from "react";
import Dashboard from "./components/Dashboard";
import LoyversePanel from "./components/LoyversePanel";
import { Bot, Database } from "lucide-react";

const TABS = [
  { id: "agent", label: "Agent Dashboard", icon: Bot },
  { id: "loyverse", label: "Loyverse Data", icon: Database },
] as const;

type Tab = typeof TABS[number]["id"];

export default function Home() {
  const [activeTab, setActiveTab] = useState<Tab>("agent");

  return (
    <div className="h-screen bg-gray-950 text-white flex flex-col overflow-hidden">
      {/* Top Navigation */}
      <nav className="border-b border-gray-800 bg-gray-900/90 flex-none px-6 flex items-center gap-1 h-12">
        <span className="text-xs font-bold text-indigo-400 mr-4 tracking-widest uppercase">Klar PoC</span>
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            className={`flex items-center gap-1.5 px-4 py-1.5 rounded-lg text-xs font-medium transition-all ${
              activeTab === t.id
                ? "bg-indigo-600 text-white"
                : "text-gray-400 hover:text-gray-200 hover:bg-gray-800"
            }`}
          >
            <t.icon className="w-3.5 h-3.5" />
            {t.label}
          </button>
        ))}
      </nav>

      {/* Tab Content */}
      <div className="flex flex-1 overflow-hidden min-h-0">
        {activeTab === "agent" && <Dashboard />}
        {activeTab === "loyverse" && <LoyversePanel />}
      </div>
    </div>
  );
}
