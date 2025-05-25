import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { getIsPrivateRoute } from "./utils/regex/routes";
import { checkLoggedIn } from "./utils/check-logged-in";

export const middleware = async (request: NextRequest) => {
  const token = request.cookies.get("token")?.value;
  const { pathname } = request.nextUrl;

  const isPrivateRoute = getIsPrivateRoute(pathname);

  if (isPrivateRoute) {
    const isLoggedIn = await checkLoggedIn(token);
    if (!isLoggedIn || !token) {
      const loginUrl = new URL("/login", request.url);
      return NextResponse.redirect(loginUrl);
    }
  }

  return NextResponse.next();
};

export const config = {
  matcher: ["/dashboard/:path*"],
};
