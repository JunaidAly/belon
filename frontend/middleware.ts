import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

export async function middleware(request: NextRequest) {
  let response = NextResponse.next({ request: { headers: request.headers } });

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        get(name: string) {
          return request.cookies.get(name)?.value;
        },
        set(name: string, value: string, options: Record<string, unknown>) {
          request.cookies.set({ name, value, ...(options as Record<string, string>) });
          response = NextResponse.next({ request: { headers: request.headers } });
          response.cookies.set({ name, value, ...(options as Record<string, string>) });
        },
        remove(name: string, options: Record<string, unknown>) {
          request.cookies.set({ name, value: "", ...(options as Record<string, string>) });
          response = NextResponse.next({ request: { headers: request.headers } });
          response.cookies.set({ name, value: "", ...(options as Record<string, string>) });
        },
      },
    }
  );

  const { data: { user } } = await supabase.auth.getUser();
  const path = request.nextUrl.pathname;

  // Protect all routes under /(protected)
  const protectedPaths = ["/control-center", "/workflow-builder", "/signals", "/integrations", "/billing"];
  const isProtected = protectedPaths.some((p) => path.startsWith(p));
  const isAuthPage = path.startsWith("/login") || path.startsWith("/signup");

  if (isProtected && !user) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("next", path);
    return NextResponse.redirect(loginUrl);
  }

  if (isAuthPage && user) {
    return NextResponse.redirect(new URL("/control-center", request.url));
  }

  return response;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)"],
};
