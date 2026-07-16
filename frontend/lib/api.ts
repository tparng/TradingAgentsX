/**
 * API client for TradingAgentsX backend
 */
import axios from "axios";
import type {
  AnalysisRequest,
  AnalysisResponse,
  ConfigResponse,
  HealthResponse,
  Ticker,
  TaskCreatedResponse,
  TaskStatusResponse,
  ChatMessageRequest,
  ChatMessageResponse,
  WatchlistItem,
  WatchlistStatus,
} from "./types";

const apiClient = axios.create({
  headers: {
    "Content-Type": "application/json",
  },
});

export const api = {
  /**
   * Get API health status
   */
  async health(): Promise<HealthResponse> {
    const response = await apiClient.get<HealthResponse>("/api/health");
    return response.data;
  },

  /**
   * Get configuration options
   */
  async getConfig(): Promise<ConfigResponse> {
    const response = await apiClient.get<ConfigResponse>("/api/config");
    return response.data;
  },

  /**
   * Start analysis (returns task ID)
   */
  async runAnalysis(request: AnalysisRequest): Promise<TaskCreatedResponse> {
    const response = await apiClient.post<TaskCreatedResponse>(
      "/api/analyze",
      request
    );
    return response.data;
  },

  /**
   * Get task status
   */
  async getTaskStatus(taskId: string): Promise<TaskStatusResponse> {
    const response = await apiClient.get<TaskStatusResponse>(
      `/api/task/${taskId}`
    );
    return response.data;
  },

  /**
   * Get list of popular tickers
   */
  async getTickers(): Promise<{ tickers: Ticker[] }> {
    const response = await apiClient.get<{ tickers: Ticker[] }>("/api/tickers");
    return response.data;
  },

  /**
   * Cleanup task from Redis storage after saving results
   * This helps keep Redis memory usage low
   */
  async cleanupTask(taskId: string): Promise<{ success: boolean; message: string }> {
    try {
      const response = await apiClient.delete<{ success: boolean; message: string; task_id: string }>(
        `/api/task/${taskId}/cleanup`
      );
      return response.data;
    } catch (error) {
      // Silently fail - cleanup is optional, task will auto-expire anyway
      console.warn("Task cleanup failed (will auto-expire in 10 minutes):", error);
      return { success: false, message: "Cleanup failed silently" };
    }
  },

  /**
   * Send a chat message about analysis reports
   */
  async sendChatMessage(request: ChatMessageRequest): Promise<ChatMessageResponse> {
    const response = await apiClient.post<ChatMessageResponse>(
      "/api/chat",
      request
    );
    return response.data;
  },

  // ── Watchlist ──────────────────────────────────────────────────────────────

  async getWatchlist(): Promise<WatchlistItem[]> {
    const response = await apiClient.get<WatchlistItem[]>("/api/watchlist");
    return response.data;
  },

  async addToWatchlist(ticker: string, market_type: string, notes?: string): Promise<WatchlistItem> {
    const response = await apiClient.post<WatchlistItem>("/api/watchlist", {
      ticker, market_type, notes: notes ?? "",
    });
    return response.data;
  },

  async removeFromWatchlist(ticker: string): Promise<void> {
    await apiClient.delete(`/api/watchlist/${ticker}`);
  },

  async syncWatchlistFromSheet(): Promise<{ message: string }> {
    const response = await apiClient.post<{ message: string }>("/api/watchlist/sync");
    return response.data;
  },

  async triggerWatchlistAnalysis(ticker?: string): Promise<{ message: string }> {
    const response = await apiClient.post<{ message: string }>("/api/watchlist/analyze", {
      ticker: ticker ?? null,
    });
    return response.data;
  },

  async getWatchlistStatus(): Promise<WatchlistStatus> {
    const response = await apiClient.get<WatchlistStatus>("/api/watchlist/status");
    return response.data;
  },
};
