"use client";
import Link from "next/link";
import { navigation } from "../constants";
import { usePathname } from "next/navigation";

const Navigation = () => {
  const pathname = usePathname();
  return (
    <nav className="flex-1 space-y-2 px-4 py-6">
      {navigation.map((item) => {
        const isActive = pathname.startsWith(item.href);
        return (
          <Link
            key={item.name}
            href={item.href}
            className={`group flex items-center rounded-lg px-4 py-3 text-sm font-medium transition-all duration-200 ${
              isActive
                ? "bg-gradient-to-r from-primary/10 to-primary/5 text-primary shadow-sm"
                : "text-muted-foreground hover:bg-accent/50 hover:text-foreground hover:shadow-sm"
            }`}
          >
            <item.icon
              className={`mr-3 h-5 w-5 transition-transform duration-200 ${
                isActive ? "text-primary scale-110" : "group-hover:scale-110"
              }`}
            />
            <span className="font-medium">{item.name}</span>
            {isActive && (
              <div className="ml-auto h-1.5 w-1.5 rounded-full bg-primary" />
            )}
          </Link>
        );
      })}
    </nav>
  );
};

export default Navigation;
