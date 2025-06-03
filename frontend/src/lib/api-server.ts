import { cookies } from "next/headers";

interface FetchOptions extends Omit<RequestInit, "body" | "headers"> {
  data?: any;
  headers?: Record<string, string>;
  token?: string;
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
    if (Error.captureStackTrace) {
      Error.captureStackTrace(this, ApiError);
    }
    Object.setPrototypeOf(this, ApiError.prototype);
  }
}

const backendServer = process.env.BACKEND_SERVER || "localhost";
const backendPort = process.env.BACKEND_PORT || "8000";
const baseUrl = `http://${backendServer}:${backendPort}`;

export async function fetchApi(path: string, options: FetchOptions = {}) {
  const url = new URL(path, baseUrl).href;

  const {
    data,
    headers: customHeaders = {},
    token: inputToken,
    ...restOptions
  } = options;

  let token = inputToken;

  if (!token && typeof cookies === "function") {
    try {
      const cookieStore = await cookies(); // Note: cookies() can only be called in Server Components or Route Handlers
      token = cookieStore.get("token")?.value;
    } catch (e) {
      // This can happen if fetchApi is called in a context where cookies() is not available (e.g. client component utility)
      // console.warn("cookies() not available in this context or failed:", e);
    }
  }

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
      config.body = data; // For other body types like raw string for text/plain
    }
  }

  try {
    const response = await fetch(url, config);

    if (response.status === 401) {
      // Handle 401 Unauthorized specifically
      // You might want to redirect to login or clear session here if appropriate
      throw new ApiError(401, "Unauthorized - Please log in again");
    }

    if (!response.ok) {
      // For any other non-successful response (4xx, 5xx client/server errors)
      let detailMessage = `Server error (${response.status})`;
      try {
        const errorData = await response.json(); // Attempt to parse error details
        detailMessage = errorData.detail || errorData.message || response.statusText || detailMessage;
      } catch (e) {
        // If parsing errorData fails, use statusText or the generic message
        detailMessage = response.statusText || detailMessage;
      }
      throw new ApiError(response.status, detailMessage);
    }

    // If we reach here, response.ok is TRUE (status 200-299)

    // Handle 204 No Content: successful, but no body to parse. Return the Response object.
    if (response.status === 204) {
      return response;
    }

    const contentType = response.headers.get("content-type");

    // If Content-Type is application/json, parse and return it.
    if (contentType && contentType.toLowerCase().includes("application/json")) {
      const contentLengthHeader = response.headers.get("content-length");
      // Handle cases where Content-Type is JSON but body is empty (e.g., Content-Length: 0)
      if (contentLengthHeader && parseInt(contentLengthHeader, 10) === 0) {
        return {}; // Or null, or an empty string, depending on expected behavior for empty JSON
      }
      return await response.json();
    } else {
      // For ALL OTHER successful content types (e.g., files, text/html, text/plain, application/octet-stream),
      // return the raw Response object. The caller can then use .blob(), .text(), etc.
      return response;
    }
  } catch (error) {
    if (error instanceof ApiError) {
      throw error; // Re-throw ApiErrors as they are already structured
    }
    // For network errors or other unexpected errors before/during fetch
    console.error("fetchApi unexpected error (will be wrapped in ApiError 500):", error);
    const message = error instanceof Error ? error.message : "Network error or server is unreachable";
    // Prepend context to make it clear this error is from the API utility layer
    throw new ApiError(500, `API Fetch Layer: ${message}`);
  }
}

// api object remains the same
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