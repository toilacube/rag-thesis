"use client";

import Link from "next/link";
import LoginForm from "./components/login-form";

const LoginPage = () => {
  return (
    <main className="min-h-screen bg-gray-50 flex items-center justify-center px-4 sm:px-6 lg:px-8">
      <div className="w-full max-w-md">
        <div className="bg-white rounded-lg shadow-md p-8 space-y-6">
          <div className="text-center">
            <h1 className="text-3xl font-bold text-gray-900">
              Welcome To RAG Web UI
            </h1>
            <p className="mt-2 text-sm text-gray-600">
              Please sign in to continue
            </p>
          </div>

          <LoginForm />

          <div className="text-center">
            <Link
              href="/register"
              className="text-sm font-medium text-gray-600 hover:text-gray-500"
            >
              Don't have an account? Create one now
            </Link>
          </div>
        </div>
      </div>
    </main>
  );
};

export default LoginPage;
