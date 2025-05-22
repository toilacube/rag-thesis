"use client";

import Link from "next/link";
import { useState } from "react";
import { FaBars } from "react-icons/fa";
import Navigation from "../navigation";
import Logout from "../logout";

const Menu = () => {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <>
      <div className="lg:hidden fixed top-0 left-0 m-4 z-50">
        <button
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          className="p-2 rounded-md bg-primary text-primary-foreground"
        >
          <FaBars className="h-6 w-6" />
        </button>
      </div>

      <div
        className={`fixed inset-y-0 left-0 z-40 w-64 transform bg-card border-r transition-transform duration-200 ease-in-out lg:translate-x-0 ${
          isMobileMenuOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex h-full flex-col">
          <div className="flex h-16 items-center border-b pl-8">
            <Link
              href="/dashboard"
              className="flex items-center text-lg font-semibold hover:text-primary transition-colors"
            >
              RAG Web UI
            </Link>
          </div>
          <Navigation />
          <Logout />
        </div>
      </div>
    </>
  );
};

export default Menu;
