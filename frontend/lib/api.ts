// API client utility for interacting with the backend endpoints

const API_BASE = "/api"; // Appends /api prefix to route calls for proxy rewriting


export interface RequestOptions extends RequestInit {
  token?: string | null;
}

// FastAPI returns `detail` as a string for HTTP errors but as a list of
// {loc, msg} objects for validation errors (422); render both as readable text.
function formatDetail(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((d) => {
        const msg = typeof d === "string" ? d : d?.msg;
        if (!msg) return "";
        const field = Array.isArray(d?.loc) ? d.loc.filter((p: unknown) => p !== "body").join(".") : "";
        return field ? `${field}: ${msg}` : msg;
      })
      .filter(Boolean)
      .join("; ");
  }
  return "";
}

async function request<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  
  // Build headers
  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  
  // Inject JWT Token from localStorage if not explicitly passed
  let token = options.token;
  if (token === undefined && typeof window !== "undefined") {
    token = localStorage.getItem("token");
  }
  
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  
  let response: Response;
  try {
    response = await fetch(url, {
      ...options,
      headers,
    });
  } catch {
    throw new Error("Cannot reach the server. Check your connection and try again.");
  }
  
  if (response.status === 204) {
    return null as unknown as T;
  }
  
  if (!response.ok) {
    let errorDetail = "An error occurred";
    try {
      const errJson = await response.json();
      errorDetail = formatDetail(errJson.detail) || errorDetail;
    } catch {
      errorDetail = response.statusText || errorDetail;
    }
    
    if (response.status === 401 && typeof window !== "undefined") {
      // Clear expired credentials and redirect
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      if (window.location.pathname !== "/login" && window.location.pathname !== "/register") {
        window.location.href = "/login";
      }
    }
    
    throw new Error(errorDetail);
  }
  
  return response.json() as Promise<T>;
}

export const api = {
  get: <T>(endpoint: string, options?: RequestOptions) => 
    request<T>(endpoint, { ...options, method: "GET" }),
    
  post: <T>(endpoint: string, body: any, options?: RequestOptions) => 
    request<T>(endpoint, { 
      ...options, 
      method: "POST", 
      body: body instanceof FormData ? body : JSON.stringify(body) 
    }),
    
  put: <T>(endpoint: string, body: any, options?: RequestOptions) => 
    request<T>(endpoint, { ...options, method: "PUT", body: JSON.stringify(body) }),
    
  delete: <T>(endpoint: string, options?: RequestOptions) => 
    request<T>(endpoint, { ...options, method: "DELETE" }),
};
