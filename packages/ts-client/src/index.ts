/**
 * @pearlflow/ts-client
 *
 * Typed API client for PearlFlow backend.
 * Generated from OpenAPI specification.
 */

export interface PearlFlowClientConfig {
  baseUrl: string;
  apiKey: string;
}

export interface Session {
  session_id: string;
  welcome_message: string;
}

export interface MessageRequest {
  session_id: string;
  text: string;
}

export interface MessageResponse {
  status: string;
}

/**
 * PearlFlow API Client
 */
export class PearlFlowClient {
  private baseUrl: string;
  private apiKey: string;

  constructor(config: PearlFlowClientConfig) {
    this.baseUrl = config.baseUrl;
    this.apiKey = config.apiKey;
  }

  /**
   * Create a new chat session.
   */
  async createSession(): Promise<Session> {
    const response = await fetch(`${this.baseUrl}/session`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ clinic_api_key: this.apiKey }),
    });

    if (!response.ok) {
      throw new Error(`Failed to create session: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Send a message to the chat.
   */
  async sendMessage(sessionId: string, text: string): Promise<MessageResponse> {
    const response = await fetch(`${this.baseUrl}/chat/message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ session_id: sessionId, text }),
    });

    if (!response.ok) {
      throw new Error(`Failed to send message: ${response.statusText}`);
    }

    return response.json();
  }

  /**
   * Create an SSE connection for streaming responses.
   */
  createStream(sessionId: string): EventSource {
    return new EventSource(`${this.baseUrl}/chat/stream/${sessionId}`);
  }
}

export default PearlFlowClient;
