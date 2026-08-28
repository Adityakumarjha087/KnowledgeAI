"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";

interface SidebarProps {
  children: React.ReactNode;
}

export default function Sidebar({ children }: SidebarProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [userEmail, setUserEmail] = useState("");
  const [authenticated, setAuthenticated] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("token");
    const storedUser = localStorage.getItem("user");
    
    if (!token) {
      router.push("/login");
    } else {
      setAuthenticated(true);
      if (storedUser) {
        try {
          const parsed = JSON.parse(storedUser);
          setUserEmail(parsed.email);
        } catch {
          setUserEmail("user@company.com");
        }
      }
    }
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    router.push("/login");
  };

  if (!authenticated) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-[#000000] text-white font-sans">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-white/20 border-t-white rounded-full animate-spin" />
          <span className="text-xs font-mono text-white/50">Loading workspace...</span>
        </div>
      </div>
    );
  }

  const menuItems = [
    {
      name: "Dashboard",
      path: "/dashboard",
      icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
          <path strokeLinecap="round" strokeLinejoin="round" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2H6a2 2 0 01-2-2v-4zM14 16a2 2 0 012-2h2a2 2 0 012 2v4a2 2 0 01-2 2h-2a2 2 0 01-2-2v-4z" />
        </svg>
      ),
    },
    {
      name: "Documents",
      path: "/documents",
      icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
    },
    {
      name: "Chat Assistant",
      path: "/chat",
      icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
          <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
        </svg>
      ),
    },
    {
      name: "RAG Evaluation",
      path: "/evaluation",
      icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      ),
    },
  ];

  return (
    <div className="flex min-h-screen bg-[#000000] text-white font-sans">
      {/* Sidebar Panel */}
      <aside className="w-64 border-r border-white/10 bg-[#050505] flex flex-col justify-between p-6 shrink-0 h-screen sticky top-0 z-20">
        <div>
          {/* Logo Title */}
          <Link href="/dashboard" className="flex items-center gap-3 mb-8 px-2 group">
            <div className="w-8 h-8 rounded-lg bg-white flex items-center justify-center font-black text-black text-sm shadow-sm group-hover:bg-white/90 transition-colors">
              K
            </div>
            <span className="font-bold text-base tracking-tight text-white">
              Knowledge<span className="text-white/50">AI</span>
            </span>
          </Link>

          {/* Menu Options */}
          <nav className="space-y-1.5">
            {menuItems.map((item) => {
              const active = pathname.startsWith(item.path);
              return (
                <Link
                  key={item.name}
                  href={item.path}
                  className={`flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-xs font-semibold transition-all border ${
                    active
                      ? "bg-white text-black border-white shadow-sm font-bold"
                      : "border-transparent text-white/60 hover:bg-white/5 hover:text-white hover:border-white/10"
                  }`}
                >
                  <span className={active ? "text-black" : "text-white/40"}>
                    {item.icon}
                  </span>
                  {item.name}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* User Card */}
        <div className="pt-5 border-t border-white/10 flex flex-col gap-3">
          <div className="flex flex-col px-3 py-2 rounded-lg bg-[#0d0d0d] border border-white/10">
            <span className="text-white/40 text-[10px] font-bold uppercase tracking-wider">Account</span>
            <span className="text-white/90 text-xs font-medium truncate mt-0.5">{userEmail}</span>
          </div>

          <button
            onClick={handleLogout}
            className="flex items-center justify-center gap-2 px-3 py-2 rounded-lg border border-white/10 bg-[#0d0d0d] text-xs font-semibold text-white/60 hover:bg-red-950/30 hover:border-red-500/30 hover:text-red-400 transition-colors cursor-pointer"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="2">
              <path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 min-w-0 flex flex-col h-screen overflow-y-auto bg-[#000000] relative">
        <div className="p-8 md:p-12 flex-1 flex flex-col">{children}</div>
      </main>
    </div>
  );
}
