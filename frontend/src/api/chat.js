/**
 * Chat API functions for 8NAP AI
 */

const API_BASE_URL = 'http://localhost:8000/api/v1';

/**
 * Send a message to 8NAP AI and get response
 * @param {string} message - User's message
 * @param {boolean} includeContext - Whether to include operational context
 * @returns {Promise<Object>} - AI response
 */
export async function sendChatMessage(message, includeContext = true) {
  const response = await fetch(`${API_BASE_URL}/chat/message`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      message,
      include_context: includeContext,
    }),
  });

  if (!response.ok) {
    throw new Error(`Chat API error: ${response.statusText}`);
  }

  return response.json();
}

/**
 * Get suggested questions from SNAPai
 * @returns {Promise<Object>} - List of suggested questions
 */
export async function getSuggestedQuestions() {
  const response = await fetch(`${API_BASE_URL}/chat/suggestions`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error(`Chat API error: ${response.statusText}`);
  }

  return response.json();
}
