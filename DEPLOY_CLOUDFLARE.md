# Deploying Spark Audio Notebook to Cloudflare

This guide explains how to deploy your Spark Audio Notebook (OpenPod) app to Cloudflare using Cloudflare Pages (for the frontend) and Cloudflare Workers (for the backend API/WebSocket). This approach leverages Cloudflare's global edge network for fast, secure, and scalable deployments.

---

## 1. Prerequisites
- [Cloudflare account](https://dash.cloudflare.com/)
- [Wrangler CLI](https://developers.cloudflare.com/workers/wrangler/install-and-update/) installed (`npm install -g wrangler`)
- Node.js 18+
- Python 3.11+ (for local development)
- Git

---

## 2. Deploy the Frontend (Vite React) to Cloudflare Pages

### a. Push your code to a GitHub repository
Cloudflare Pages integrates with GitHub for automatic deployments.

### b. Create a Cloudflare Pages project
1. Go to the [Cloudflare Pages dashboard](https://dash.cloudflare.com/) and click **Create a Project**.
2. Connect your GitHub repository.
3. Set the following build settings:
   - **Framework preset:** `Vite`
   - **Build command:** `npm run build` (or `bun run build` if using Bun)
   - **Build output directory:** `static` (or `dist` if your build outputs there)
   - **Root directory:** `src` (if your frontend is in `src/`), otherwise leave blank
4. Set any required environment variables (API endpoints, etc.) in the Pages dashboard.
5. Deploy the project. Your frontend will be available at `https://<your-project>.pages.dev`.

---

## 3. Deploy the Backend (Flask API/Socket.IO) to Cloudflare Workers

Cloudflare Workers run JavaScript/TypeScript at the edge. Python is not natively supported, so you have two options:

### Option 1: Rewrite Backend in JavaScript/TypeScript for Workers
- Rewrite your Flask API and Socket.IO logic using [Hono](https://honojs.dev/), [itty-router](https://itty.dev/), or [Cloudflare Workers native APIs](https://developers.cloudflare.com/workers/).
- Use [socket.io-client](https://socket.io/docs/v4/client-api/) for the frontend, and [ws](https://github.com/websockets/ws) or [uWebSockets.js](https://github.com/uNetworking/uWebSockets.js) for the backend if you need WebSocket support.
- Deploy using Wrangler:
  ```bash
  wrangler init
  wrangler publish
  ```

### Option 2: Use a Cloudflare Tunnel to a Python Backend
- Host your Flask backend on a VM or service (e.g., Fly.io, Render, Railway).
- Use [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/) to expose your backend securely to the internet.
- Update your frontend API/WebSocket URLs to use the tunnel domain.

---

## 4. Environment Variables & Secrets
- Store API keys and secrets in Cloudflare Pages and Workers environment variable settings.
- Never commit secrets to your repository.

---

## 5. Example: Deploying a Static Frontend with API Proxy
If you only need to deploy the frontend to Cloudflare Pages and proxy API/WebSocket requests to an external backend:
1. In your `vite.config.ts`, set the proxy target to your backend's public URL (Cloudflare Tunnel or other host).
2. Deploy the frontend as above.

---

## 6. Useful Links
- [Cloudflare Pages Docs](https://developers.cloudflare.com/pages/)
- [Cloudflare Workers Docs](https://developers.cloudflare.com/workers/)
- [Wrangler CLI Docs](https://developers.cloudflare.com/workers/wrangler/)
- [Cloudflare Tunnel Docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)

---

## 7. Notes
- Cloudflare Workers do not natively support Python. For a pure Python backend, use a tunnel or migrate backend logic to JavaScript/TypeScript.
- For WebSocket support, ensure your backend and frontend are both compatible with Cloudflare's edge network.

---

## 8. Support
For help, see the official Cloudflare documentation or open an issue in your repository.
