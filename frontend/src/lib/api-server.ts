import { cookies } from "next/headers";

interface FetchOptions extends Omit<RequestInit, "body" | "headers"> {
  data?: any;
  headers?: Record<string, string>;
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";

    // Maintains proper stack trace for where our error was thrown (only available on V8)
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, ApiError);
    }

    // Set the prototype explicitly to ensure instanceof works correctly
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}

const backendServer = process.env.BACKEND_SERVER || "localhost";
const backendPort = process.env.BACKEND_PORT || "8000";
const baseUrl = `http://${backendServer}:${backendPort}`;

export async function fetchApi(path: string, options: FetchOptions = {}) {
  const url = new URL(path, baseUrl).href;

  const { data, headers: customHeaders = {}, ...restOptions } = options;

  const cookieStore = await cookies();
  const token = cookieStore.get("token")?.value;
  console.log("apisv", token);

  const headers: Record<string, string> = {
    ...(token && { Authorization: `Bearer ${token}` }),
    ...customHeaders,
  };

  if (!headers["Content-Type"] && data && !(data instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const config: RequestInit = {
    ...restOptions,
    headers,
  };

  if (data) {
    if (data instanceof FormData) {
      config.body = data;
    } else if (headers["Content-Type"] === "application/json") {
      config.body = JSON.stringify(data);
    } else if (
      headers["Content-Type"] === "application/x-www-form-urlencoded"
    ) {
      config.body =
        typeof data === "string" ? data : new URLSearchParams(data).toString();
    } else {
      config.body = data;
    }
  }

  try {
    const response = await fetch(url, config);

    if (response.status === 401) {
      if (typeof window !== "undefined") {
        cookieStore.delete("token");
        // window.location.href = "/login";
      }
      throw new ApiError(401, "Unauthorized - Please log in again");
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        response.status,
        errorData.message || errorData.detail || "An error occurred"
      );
    }

    // Check if the response has content before trying to parse it as JSON
    const contentType = response.headers.get("content-type");
    if (contentType && contentType.includes("application/json")) {
      return await response.json();
    } else {
      // For empty responses (common with DELETE requests)
      return { success: true, status: response.status };
    }
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(500, "Network error or server is unreachable");
  }
}

export const api = {
  get: (url: string, options?: Omit<FetchOptions, "method">) =>
    fetchApi(url, { ...options, method: "GET" }),

  post: (url: string, data?: any, options?: Omit<FetchOptions, "method">) =>
    fetchApi(url, { ...options, method: "POST", data }),

  put: (url: string, data?: any, options?: Omit<FetchOptions, "method">) =>
    fetchApi(url, { ...options, method: "PUT", data }),

  delete: (url: string, options?: Omit<FetchOptions, "method">) =>
    fetchApi(url, { ...options, method: "DELETE" }),

  patch: (url: string, data?: any, options?: Omit<FetchOptions, "method">) =>
    fetchApi(url, { ...options, method: "PATCH", data }),
};
