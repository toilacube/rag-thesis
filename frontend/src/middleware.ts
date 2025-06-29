import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import { getIsPrivateRoute, getNonLoginRoute } from "./utils/regex/routes";
import { checkLoggedIn } from "./utils/check-logged-in";

export const middleware = async (request: NextRequest) => {
  const token = request.cookies.get("token")?.value;
  const { pathname } = request.nextUrl;

  const isPrivateRoute = getIsPrivateRoute(pathname);
  const isAuthRoute = getNonLoginRoute(pathname);

  if (token) {
    const isLoggedIn = await checkLoggedIn(token);
    if (!isLoggedIn && isPrivateRoute) {
      return NextResponse.redirect(new URL("/login", request.url));
    }
    if (isLoggedIn && isAuthRoute) {
      return NextResponse.redirect(new URL("/dashboard", request.url));
    }
  }

  return NextResponse.next();
};

export const config = {
  matcher: ["/dashboard/:path*", "/login", "/register"],
};
