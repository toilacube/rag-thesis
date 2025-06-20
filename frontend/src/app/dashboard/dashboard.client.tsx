"use client";

import { useEffect, useState } from "react";
import {
  FaFolder,
  FaComment,
  FaArrowRight,
  FaPlus,
  FaUpload,
  FaBrain,
  FaMagic,
} from "react-icons/fa";
import { useProject } from "@/contexts/project-provider";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/select";
import Link from "next/link";

interface Stats {
  projects: number;
  chats: number;
}

const DashboardClient = () => {
  const [stats, setStats] = useState<Stats>({ projects: 0, chats: 0 });
  const { projects, selectedProject, setSelectedProject } = useProject();

  useEffect(() => {
    const fetchStats = async () => {
      // We can now use the projects from context to get stats
      if (projects.length > 0) {
        setStats({
          projects: projects.length,
          chats: 0, // This would require a separate API call
        });
      }
    };

    fetchStats();
  }, [projects]);

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <div className="mb-12 rounded-2xl bg-gradient-to-r from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800 p-8 shadow-sm">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
          <div className="space-y-4">
            <h1 className="text-4xl font-bold tracking-tight bg-clip-text">
              Project Q&A Assistant
            </h1>
            <p className="text-slate-600 dark:text-slate-300 max-w-xl">
              Your personal AI-powered project hub. Upload documents to
              projects, and get instant answers through natural conversations.
            </p>
          </div>
          <Link
            href="/dashboard/project/new"
            className="inline-flex items-center justify-center rounded-full bg-gray-600 px-6 py-3 text-sm font-medium text-white hover:bg-gray-700 transition-all shadow-lg shadow-gray-600/20"
          >
            <FaPlus className="mr-2 h-4 w-4" />
            New Project
          </Link>
        </div>

        {/* Project selector dropdown */}
        {projects.length > 0 && (
          <div className="mt-6 max-w-md">
            <label className="block text-sm font-medium text-slate-600 dark:text-slate-400 mb-2">
              Active Project
            </label>
            <Select
              value={selectedProject?.id.toString()}
              onValueChange={(value) => {
                const project = projects.find((p) => p.id.toString() === value);
                if (project) setSelectedProject(project);
              }}
            >
              <SelectTrigger className="bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700">
                <SelectValue placeholder="Select a project" />
              </SelectTrigger>
              <SelectContent>
                {projects.map((project) => (
                  <SelectItem key={project.id} value={project.id.toString()}>
                    {project.project_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        )}
      </div>

      <div className="grid gap-6 md:grid-cols-2 mb-12">
        <div className="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-8 shadow-sm hover:shadow-md transition-all">
          <div className="flex items-center gap-6">
            <div className="rounded-full bg-gray-100 dark:bg-gray-900/30 p-4">
              <FaFolder className="h-8 w-8 text-gray-600 dark:text-gray-400" />
            </div>
            <div>
              <h3 className="text-4xl font-bold text-slate-900 dark:text-white">
                {stats.projects}
              </h3>
              <p className="text-slate-500 dark:text-slate-400 mt-1">
                Projects
              </p>
            </div>
          </div>
          <Link
            href="/dashboard/project"
            className="mt-6 flex items-center text-gray-600 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 text-sm font-medium"
          >
            View all projects
            <FaArrowRight className="ml-2 h-4 w-4" />
          </Link>
        </div>

        <div className="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-8 shadow-sm hover:shadow-md transition-all">
          <div className="flex items-center gap-6">
            <div className="rounded-full bg-gray-100 dark:bg-gray-900/30 p-4">
              <FaComment className="h-8 w-8 text-gray-600 dark:text-gray-400" />
            </div>
            <div>
              <h3 className="text-4xl font-bold text-slate-900 dark:text-white">
                {stats.chats}
              </h3>
              <p className="text-slate-500 dark:text-slate-400 mt-1">
                Chat Sessions
              </p>
            </div>
          </div>
          <Link
            href="/dashboard/chat"
            className="mt-6 flex items-center text-gray-600 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 text-sm font-medium"
          >
            View all chat sessions
            <FaArrowRight className="ml-2 h-4 w-4" />
          </Link>
        </div>
      </div>

      <h2 className="text-2xl font-semibold text-slate-900 dark:text-white mb-6">
        Quick Actions
      </h2>
      <div className="grid gap-6 md:grid-cols-3 mb-12">
        <Link
          href="/dashboard/project/new"
          className="flex flex-col items-center justify-center rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-8 shadow-sm hover:shadow-md transition-all hover:border-gray-500 dark:hover:border-gray-500"
        >
          <div className="rounded-full bg-gray-100 dark:bg-gray-900/30 p-4 mb-4">
            <FaBrain className="h-8 w-8 text-gray-600 dark:text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-slate-900 dark:text-white mb-2">
            Create Project
          </h3>
          <p className="text-sm text-slate-500 dark:text-slate-400 text-center">
            Start a new project repository for documents
          </p>
        </Link>

        <Link
          href="/dashboard/project"
          className="flex flex-col items-center justify-center rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-8 shadow-sm hover:shadow-md transition-all hover:border-gray-500 dark:hover:border-gray-500"
        >
          <div className="rounded-full bg-gray-100 dark:bg-gray-900/30 p-4 mb-4">
            <FaUpload className="h-8 w-8 text-gray-600 dark:text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-slate-900 dark:text-white mb-2">
            Upload Documents
          </h3>
          <p className="text-sm text-slate-500 dark:text-slate-400 text-center">
            Add PDF, DOCX, MD or TXT files to your projects
          </p>
        </Link>

        <Link
          href="/dashboard/chat/new"
          className="flex flex-col items-center justify-center rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-8 shadow-sm hover:shadow-md transition-all hover:border-gray-500 dark:hover:border-gray-500"
        >
          <div className="rounded-full bg-gray-100 dark:bg-gray-900/30 p-4 mb-4">
            <FaMagic className="h-8 w-8 text-gray-600 dark:text-gray-400" />
          </div>
          <h3 className="text-lg font-medium text-slate-900 dark:text-white mb-2">
            Start Chatting
          </h3>
          <p className="text-sm text-slate-500 dark:text-slate-400 text-center">
            Get instant answers from your project documents with AI
          </p>
        </Link>
      </div>
    </div>
  );
};

export default DashboardClient;
