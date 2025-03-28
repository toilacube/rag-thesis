import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen flex justify-center items-center bg-white text-black">
      <div className="text-center space-y-8">
        <h1 className="text-6xl sm:text-7xl font-bold tracking-tight text-black">
          RAG Web UI
        </h1>
        <p className="text-xl sm:text-2xl text-gray-500 max-w-3xl mx-auto font-light leading-relaxed">
          Experience the next generation of AI interaction.
          <br />
          Powerful. Intuitive. Revolutionary.
        </p>
        <div className="flex flex-col sm:flex-row gap-6 justify-center items-center mt-12">
          <Link
            href="/register"
            className="px-8 py-4 bg-blue-600 text-white rounded-full text-lg font-medium transition-all duration-300 hover:bg-blue-700 w-full sm:w-auto"
          >
            Get Started
          </Link>
          <Link
            href="/login"
            className="px-8 py-4 bg-gray-200 text-gray-800 rounded-full text-lg font-medium transition-all duration-300 hover:bg-gray-300 w-full sm:w-auto"
          >
            Sign In
          </Link>
        </div>
      </div>
    </main>
  );
}
