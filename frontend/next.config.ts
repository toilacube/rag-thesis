/** @type {import('next').NextConfig} */
module.exports = {
  output: "standalone",
  experimental: {
    outputFileTracingRoot: undefined,
    outputStandalone: true,
    skipMiddlewareUrlNormalize: true,
    skipTrailingSlashRedirect: true,
    serverActions: {
       bodySizeLimit: '50mb',
    }
  },
  devIndicators: false,
};
