import { FaCommentAlt } from "react-icons/fa";
import { FaFolder } from "react-icons/fa";

export const navigation = [
  { name: "Projects", href: "/dashboard/project", icon: FaFolder },
  { name: "Chat", href: "/dashboard/chat", icon: FaCommentAlt },
];

export const dashboardConfig = {
  mainNav: [],
  sidebarNav: [
    {
      title: "Projects",
      href: "/dashboard/project",
      icon: "folder",
    },
    {
      title: "Chat",
      href: "/dashboard/chat",
      icon: "messageSquare",
    },
  ],
};
