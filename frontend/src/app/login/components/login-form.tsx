"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { loginAction } from "../utils/login";

const LoginForm = () => {
  const router = useRouter();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    const formData = new FormData(e.currentTarget);
    const res = await loginAction(formData);
    if (res.success && res.token) {
      // localStorage.setItem("token", res.token);
      router.push("/dashboard");
    } else {
      setError(res?.message || "Login failed. Please check your credentials.");
      setLoading(false);
    }
  };

  return (
    <form className="space-y-6" onSubmit={handleSubmit}>
      <div className="space-y-4">
        <div>
          <label
            htmlFor="email"
            className="block text-sm font-medium text-gray-700"
          >
            Email
          </label>
          <input
            id="email"
            name="email"
            type="text"
            required
            disabled={loading}
            className="mt-1 block w-full px-3 py-2 rounded-md border border-gray-300 shadow-sm focus:ring-2 focus:ring-gray-500 focus:border-gray-500"
            placeholder="Enter your email"
          />
        </div>

        <div>
          <label
            htmlFor="password"
            className="block text-sm font-medium text-gray-700"
          >
            Password
          </label>
          <input
            id="password"
            name="password"
            type="password"
            required
            disabled={loading}
            className="mt-1 block w-full px-3 py-2 rounded-md border border-gray-300 shadow-sm focus:ring-2 focus:ring-gray-500 focus:border-gray-500"
            placeholder="Enter your password"
          />
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-md bg-red-50 text-red-700 text-sm">
          {error}
        </div>
      )}

      <button
        type="submit"
        disabled={loading}
        className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-gray-600 hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {loading ? "Signing in..." : "Sign in"}
      </button>
    </form>
  );
};

export default LoginForm;
