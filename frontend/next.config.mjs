/** @type {import('next').NextConfig} */
const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
// En producción se proxya el API por el propio dominio (vercel.app) para que la
// cookie de sesión quede en el mismo origen y el middleware de Next pueda verla.
const proxyOrigin =
  process.env.API_PROXY_ORIGIN ||
  (apiUrl.startsWith("/") ? "" : new URL(apiUrl).origin);

const nextConfig = {
  async rewrites() {
    if (!proxyOrigin) return [];
    return [
      {
        source: "/api/:path*",
        destination: `${proxyOrigin}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
