"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import FuturisticCanvas from "@/components/FuturisticCanvas";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (localStorage.getItem("token")) {
      router.push("/dashboard");
    }
  }, [router]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const formData = new FormData();
      formData.append("username", email);
      formData.append("password", password);

      const data = await api.post<{ access_token: string; token_type: string }>("/auth/login", formData);
      localStorage.setItem("token", data.access_token);
      
      const me = await api.get<{ id: number; email: string }>("/auth/me");
      localStorage.setItem("user", JSON.stringify(me));

      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Invalid email or password credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-[#000000] text-white font-sans relative overflow-hidden px-4 selection:bg-white selection:text-black">
      {/* Interactive 3D futuristic particle mesh background */}
      <FuturisticCanvas />

      {/* Background Static Grid */}
      <div className="absolute inset-0 bg-grid-static [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_70%,transparent_100%)] pointer-events-none" />

      {/* Auth Card (Black with White Line Border & Deep Shadow) */}
      <div className="black-card w-full max-w-md p-8 sm:p-10 rounded-2xl relative z-10 space-y-6">
        <div className="text-center space-y-2">
          <div className="w-10 h-10 mx-auto rounded-lg bg-white flex items-center justify-center font-black text-black text-lg shadow-sm mb-3">
            K
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-white">
            Welcome Back
          </h1>
          <p className="text-white/50 text-xs font-normal">
            Sign in to access your Enterprise AI Knowledge Platform
          </p>
        </div>

        {error && (
          <div className="p-3 rounded-lg border border-red-500/30 bg-red-500/10 text-red-300 text-xs text-center font-medium">
            {error}
          </div>
        )}

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-white/60 text-xs font-medium uppercase tracking-wider mb-2" htmlFor="email">
              Email Address
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="name@company.com"
              className="w-full px-3.5 py-2.5 rounded-lg input-static text-xs font-medium"
            />
          </div>

          <div>
            <label className="block text-white/60 text-xs font-medium uppercase tracking-wider mb-2" htmlFor="password">
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full px-3.5 py-2.5 rounded-lg input-static text-xs font-medium"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-lg btn-white font-bold text-xs flex items-center justify-center gap-2 cursor-pointer shadow-md mt-2"
          >
            {loading ? (
              <span className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin" />
            ) : (
              "Sign In"
            )}
          </button>
        </form>

        <div className="pt-4 border-t border-white/10 text-center text-xs text-white/50">
          New to Knowledge AI?{" "}
          <Link href="/register" className="font-semibold text-white hover:underline transition-colors">
            Create an account
          </Link>
        </div>
      </div>
    </div>
  );
}
