"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import FuturisticCanvas from "@/components/FuturisticCanvas";

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (localStorage.getItem("token")) {
      router.push("/dashboard");
    }
  }, [router]);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      await api.post("/auth/register", {
        email,
        password,
        full_name: fullName,
      });

      const formData = new FormData();
      formData.append("username", email);
      formData.append("password", password);

      const response: { access_token: string } = await api.post("/auth/login", formData);
      localStorage.setItem("token", response.access_token);

      const userProfile = await api.get("/auth/me");
      localStorage.setItem("user", JSON.stringify(userProfile));

      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Failed to register. Please try again.");
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
            Create Account
          </h1>
          <p className="text-white/50 text-xs font-normal">
            Join your enterprise knowledge workspace
          </p>
        </div>

        {error && (
          <div className="p-3 rounded-lg border border-red-500/30 bg-red-500/10 text-red-300 text-xs text-center font-medium">
            {error}
          </div>
        )}

        <form onSubmit={handleRegister} className="space-y-4">
          <div>
            <label className="block text-white/60 text-xs font-medium uppercase tracking-wider mb-2" htmlFor="name">
              Full Name
            </label>
            <input
              id="name"
              type="text"
              required
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Aditya Sharma"
              className="w-full px-3.5 py-2.5 rounded-lg input-static text-xs font-medium"
            />
          </div>

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
              "Get Started"
            )}
          </button>
        </form>

        <div className="pt-4 border-t border-white/10 text-center text-xs text-white/50">
          Already registered?{" "}
          <Link href="/login" className="font-semibold text-white hover:underline transition-colors">
            Sign in
          </Link>
        </div>
      </div>
    </div>
  );
}
