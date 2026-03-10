"use client";

import { useState, useEffect } from "react";
import { Store, Package, Users, Receipt, BarChart2, ChevronDown, ChevronRight } from "lucide-react";

const fmt = (n: number) =>
  "Rp " + n.toLocaleString("id-ID");

const pct = (price: number, cost: number) =>
  price > 0 ? ((price - cost) / price * 100).toFixed(1) : "0.0";

type Store = { store_id: string; store_name: string; brand: string; location: string; currency: string; timezone: string };
type Product = { product_id: string; product_name: string; sku: string; store_id: string; category: string; price_idr: number; cost_idr: number; stock_qty: number };
type Employee = { employee_id: string; employee_name: string; email: string; role: string; store_id: string; status: string };
type TransactionItem = { product_name: string; qty: number; discount_idr: number; subtotal_idr: number };
type Transaction = { transaction_id: string; customer_name: string; date: string; time: string; employee_id: string; store_id: string; payment_method: string; total_idr: number; subtotal_idr: number; tax_idr: number; items: TransactionItem[]; notes?: string };
type DailySummary = { store_id: string; date: string; top_product: string; total_revenue_idr: number; total_transactions: number; total_items_sold: number; avg_transaction_value_idr: number; payment_methods: Record<string, number> };

type LoyverseData = {
  stores: Store[];
  products: Product[];
  employees: Employee[];
  transactions: Transaction[];
  daily_summary: DailySummary[];
};

type Tab = "summary" | "products" | "transactions" | "employees";

const TABS: { id: Tab; label: string; icon: React.ComponentType<{ className?: string }> }[] = [
  { id: "summary", label: "Daily Summary", icon: BarChart2 },
  { id: "products", label: "Products", icon: Package },
  { id: "transactions", label: "Transactions", icon: Receipt },
  { id: "employees", label: "Employees", icon: Users },
];

export default function LoyversePanel() {
  const [data, setData] = useState<LoyverseData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<Tab>("summary");
  const [storeFilter, setStoreFilter] = useState("all");
  const [expandedTxn, setExpandedTxn] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api-backend/loyverse")
      .then(r => r.json())
      .then(d => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="flex-1 flex items-center justify-center text-gray-500">
      <div className="text-center">
        <div className="w-8 h-8 border-2 border-indigo-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
        Loading Loyverse data...
      </div>
    </div>
  );

  if (!data) return (
    <div className="flex-1 flex items-center justify-center text-gray-500">
      Gagal memuat data. Pastikan backend berjalan.
    </div>
  );

  const stores = data.stores;
  const filteredProducts = storeFilter === "all" ? data.products : data.products.filter(p => p.store_id === storeFilter);
  const filteredTxns = storeFilter === "all" ? data.transactions : data.transactions.filter(t => t.store_id === storeFilter);
  const filteredEmployees = storeFilter === "all" ? data.employees : data.employees.filter(e => e.store_id === storeFilter);
  const filteredSummaries = storeFilter === "all" ? data.daily_summary : data.daily_summary.filter(s => s.store_id === storeFilter);

  const getStoreName = (id: string) => stores.find(s => s.store_id === id)?.store_name || id;
  const getEmployeeName = (id: string) => data.employees.find(e => e.employee_id === id)?.employee_name || id;

  const paymentColor: Record<string, string> = {
    cash: "bg-emerald-500/20 text-emerald-300 border-emerald-500/30",
    card: "bg-blue-500/20 text-blue-300 border-blue-500/30",
    "e-wallet": "bg-purple-500/20 text-purple-300 border-purple-500/30",
  };

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      {/* Header */}
      <div className="p-5 border-b border-gray-800 bg-gray-900/80 flex items-center justify-between gap-4 flex-wrap">
        <div>
          <h2 className="text-lg font-semibold text-white flex items-center gap-2">
            <Store className="w-5 h-5 text-indigo-400" /> Loyverse POS Data
          </h2>
          <p className="text-xs text-gray-400 mt-0.5">{stores.length} stores · {data.products.length} products · {data.transactions.length} transactions</p>
        </div>
        <select
          value={storeFilter}
          onChange={e => setStoreFilter(e.target.value)}
          className="bg-gray-800 border border-gray-700 text-sm text-gray-200 rounded-lg px-3 py-1.5 focus:outline-none focus:border-indigo-500"
        >
          <option value="all">All Stores</option>
          {stores.map(s => <option key={s.store_id} value={s.store_id}>{s.store_name}</option>)}
        </select>
      </div>

      {/* Store Cards */}
      <div className="px-5 py-4 flex gap-4 overflow-x-auto border-b border-gray-800/60">
        {(storeFilter === "all" ? stores : stores.filter(s => s.store_id === storeFilter)).map(s => (
          <div key={s.store_id} className="flex-shrink-0 bg-gray-800/50 border border-gray-700/50 rounded-xl p-4 min-w-[220px]">
            <div className="flex items-start justify-between mb-2">
              <span className="text-sm font-semibold text-white">{s.store_name}</span>
              <span className="text-[10px] px-2 py-0.5 bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 rounded-full font-medium">{s.brand}</span>
            </div>
            <p className="text-xs text-gray-400">{s.location}</p>
            <p className="text-xs text-gray-500 mt-1">{s.currency} · {s.timezone}</p>
          </div>
        ))}
      </div>

      {/* Inner Tabs */}
      <div className="flex gap-1 px-5 pt-4 border-b border-gray-800/60 overflow-x-auto">
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => setActiveTab(t.id)}
            className={`flex items-center gap-1.5 px-4 py-2 text-xs font-medium rounded-t-lg transition-all whitespace-nowrap ${activeTab === t.id ? "bg-gray-800 text-white border-t border-l border-r border-gray-700" : "text-gray-500 hover:text-gray-300"}`}
          >
            <t.icon className="w-3.5 h-3.5" />
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto p-5 space-y-6">

        {/* DAILY SUMMARY */}
        {activeTab === "summary" && (
          <div className="space-y-8">
            {filteredSummaries.map((s, i) => {
              const totalPay = Object.values(s.payment_methods as Record<string, number>).reduce((a, b) => a + b, 0);
              return (
                <div key={i} className="bg-gray-800/30 border border-gray-700/50 rounded-2xl p-5">
                  <div className="flex items-center justify-between mb-5">
                    <div>
                      <p className="font-semibold text-white">{getStoreName(s.store_id)}</p>
                      <p className="text-xs text-gray-400 mt-0.5">{s.date}</p>
                    </div>
                    <span className="text-xs px-2 py-1 bg-amber-500/15 text-amber-300 rounded-full border border-amber-500/20 font-medium">
                      ⭐ {s.top_product}
                    </span>
                  </div>

                  {/* Metric cards */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
                    {[
                      { label: "Total Revenue", value: fmt(s.total_revenue_idr), color: "text-emerald-400" },
                      { label: "Total Transaksi", value: s.total_transactions, color: "text-blue-400" },
                      { label: "Items Sold", value: s.total_items_sold, color: "text-purple-400" },
                      { label: "Avg Transaction", value: fmt(s.avg_transaction_value_idr), color: "text-indigo-400" },
                    ].map(m => (
                      <div key={m.label} className="bg-gray-900/60 border border-gray-700/30 rounded-xl p-3">
                        <p className="text-[10px] uppercase tracking-wider text-gray-500 mb-1">{m.label}</p>
                        <p className={`text-base font-bold ${m.color}`}>{m.value}</p>
                      </div>
                    ))}
                  </div>

                  {/* Payment breakdown */}
                  <div>
                    <p className="text-xs font-semibold uppercase text-gray-500 mb-3">Payment Methods</p>
                    <div className="space-y-2">
                      {Object.entries(s.payment_methods as Record<string, number>).map(([method, amt]) => {
                        const ratio = totalPay > 0 ? (amt / totalPay) * 100 : 0;
                        return (
                          <div key={method}>
                            <div className="flex justify-between text-xs mb-1">
                              <span className={`px-2 py-0.5 rounded border text-[10px] font-medium ${paymentColor[method] || "bg-gray-500/20 text-gray-300 border-gray-500/30"}`}>{method}</span>
                              <span className="text-gray-300">{fmt(amt)} <span className="text-gray-500">({ratio.toFixed(0)}%)</span></span>
                            </div>
                            <div className="h-1.5 bg-gray-700/50 rounded-full overflow-hidden">
                              <div className={`h-full rounded-full ${method === "cash" ? "bg-emerald-500" : method === "card" ? "bg-blue-500" : "bg-purple-500"}`} style={{ width: `${ratio}%` }} />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* PRODUCTS TABLE */}
        {activeTab === "products" && (
          <div className="rounded-xl border border-gray-700/50 overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-800/80 text-gray-400 text-xs uppercase">
                <tr>
                  {["Produk", "Store", "Kategori", "Harga Jual", "Cost", "Margin", "Stok"].map(h => (
                    <th key={h} className="px-4 py-3 text-left font-medium">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filteredProducts.map(p => {
                  const margin = parseFloat(pct(p.price_idr, p.cost_idr));
                  return (
                    <tr key={p.product_id} className="border-t border-gray-800/50 hover:bg-gray-800/30 transition-colors">
                      <td className="px-4 py-3">
                        <p className="font-medium text-gray-200">{p.product_name}</p>
                        <p className="text-xs text-gray-500 font-mono">{p.sku}</p>
                      </td>
                      <td className="px-4 py-3 text-xs text-gray-400">{getStoreName(p.store_id)}</td>
                      <td className="px-4 py-3">
                        <span className="text-xs px-2 py-0.5 bg-gray-700/60 rounded text-gray-300">{p.category}</span>
                      </td>
                      <td className="px-4 py-3 text-gray-200 font-medium">{fmt(p.price_idr)}</td>
                      <td className="px-4 py-3 text-gray-400">{fmt(p.cost_idr)}</td>
                      <td className="px-4 py-3">
                        <span className={`text-xs font-bold ${margin >= 60 ? "text-emerald-400" : margin >= 40 ? "text-amber-400" : "text-red-400"}`}>
                          {margin}%
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-300">{p.stock_qty.toLocaleString("id-ID")}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* TRANSACTIONS */}
        {activeTab === "transactions" && (
          <div className="space-y-3">
            {filteredTxns.sort((a, b) => b.date.localeCompare(a.date) || b.time.localeCompare(a.time)).map(txn => (
              <div key={txn.transaction_id} className="bg-gray-800/30 border border-gray-700/50 rounded-xl overflow-hidden">
                <button
                  onClick={() => setExpandedTxn(expandedTxn === txn.transaction_id ? null : txn.transaction_id)}
                  className="w-full flex items-center justify-between px-5 py-4 hover:bg-gray-800/40 transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <div className="text-left">
                      <p className="text-sm font-medium text-gray-200">{txn.customer_name}</p>
                      <p className="text-xs text-gray-500 mt-0.5">{txn.date} · {txn.time} · {getEmployeeName(txn.employee_id)}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className={`text-[10px] px-2 py-0.5 rounded border font-medium ${paymentColor[txn.payment_method] || "bg-gray-500/20 text-gray-300 border-gray-500/30"}`}>
                      {txn.payment_method}
                    </span>
                    <span className="font-bold text-emerald-400 text-sm">{fmt(txn.total_idr)}</span>
                    {expandedTxn === txn.transaction_id
                      ? <ChevronDown className="w-4 h-4 text-gray-500" />
                      : <ChevronRight className="w-4 h-4 text-gray-500" />
                    }
                  </div>
                </button>

                {expandedTxn === txn.transaction_id && (
                  <div className="px-5 pb-4 border-t border-gray-700/50 pt-4 space-y-2">
                    <p className="text-xs font-semibold uppercase text-gray-500 mb-3">Items</p>
                    {txn.items.map((item: TransactionItem, i: number) => (
                      <div key={i} className="flex justify-between items-center text-sm">
                        <div>
                          <span className="text-gray-200">{item.product_name}</span>
                          <span className="text-gray-500 ml-2">×{item.qty}</span>
                        </div>
                        <div className="text-right">
                          {item.discount_idr > 0 && <span className="text-xs text-red-400 mr-2">-{fmt(item.discount_idr)}</span>}
                          <span className="text-gray-300 font-medium">{fmt(item.subtotal_idr)}</span>
                        </div>
                      </div>
                    ))}
                    <div className="border-t border-gray-700/50 pt-2 mt-2 flex justify-between text-xs text-gray-400">
                      <span>Subtotal: {fmt(txn.subtotal_idr)} · Tax: {fmt(txn.tax_idr)}</span>
                      <span className="text-emerald-400 font-semibold">Total: {fmt(txn.total_idr)}</span>
                    </div>
                    {txn.notes && <p className="text-xs text-gray-500 italic">Note: {txn.notes}</p>}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {/* EMPLOYEES */}
        {activeTab === "employees" && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredEmployees.map(emp => (
              <div key={emp.employee_id} className="bg-gray-800/40 border border-gray-700/50 rounded-xl p-4">
                <div className="flex items-start justify-between mb-3">
                  <div className="w-10 h-10 rounded-full bg-indigo-600/30 border border-indigo-500/30 flex items-center justify-center text-sm font-bold text-indigo-300">
                    {emp.employee_name.charAt(0)}
                  </div>
                  <span className={`text-[10px] px-2 py-0.5 rounded-full border font-medium ${emp.status === "active" ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" : "bg-gray-500/20 text-gray-400 border-gray-500/30"}`}>
                    {emp.status}
                  </span>
                </div>
                <p className="font-semibold text-gray-200 text-sm">{emp.employee_name}</p>
                <p className="text-xs text-indigo-300 mt-0.5">{emp.role}</p>
                <p className="text-xs text-gray-500 mt-2">{getStoreName(emp.store_id)}</p>
                <p className="text-xs text-gray-600 mt-0.5">{emp.email}</p>
              </div>
            ))}
          </div>
        )}

      </div>
    </div>
  );
}
