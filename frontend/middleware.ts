import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

const PUBLIC_ROUTES = ["/login", "/register"];
const TOKEN_COOKIE = "llm_monitor_token";

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const token = request.cookies.get(TOKEN_COOKIE)?.value;

  // Root → redirect to login (or dashboard if already authed)
  if (pathname === "/") {
    const target = token ? "/dashboard" : "/login";
    return NextResponse.redirect(new URL(target, request.url));
  }

  // Protected routes without token → redirect to login
  if (!PUBLIC_ROUTES.includes(pathname) && !token) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("from", pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Already authenticated trying to access auth pages → dashboard
  if (PUBLIC_ROUTES.includes(pathname) && token) {
    return NextResponse.redirect(new URL("/dashboard", request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!api|_next/static|_next/image|favicon.ico).*)"],
};
