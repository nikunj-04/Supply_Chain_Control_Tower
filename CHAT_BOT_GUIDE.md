# SNAPai Chat Bot - Quick Start Guide

## ✅ What Was Built

A beautiful floating chat bot that appears in the **bottom right corner** of your dashboard!

### Features:
- 🤖 **Floating Button** - Click to open/close chat
- 💬 **Chat Window** - Clean, modern interface
- 💡 **Suggested Questions** - Quick-start buttons for common queries
- ⌨️ **Smart Input** - Type questions, press Enter to send
- 📱 **Responsive** - Works on desktop and mobile
- ✨ **Animations** - Smooth transitions and typing indicators
- 🎨 **Beautiful UI** - Gradient purple theme matching your brand

## 🚀 How to Use

### 1. Make Sure Backend is Running

The chat connects to your backend API. Ensure:

```bash
# In backend directory
.\venv\Scripts\python.exe main.py
```

Backend should be running on `http://localhost:8000`

### 2. Configure Your LLM API

Edit `backend/.env`:

```env
CHAT_API_URL=https://your-actual-ngrok-url.ngrok-free.app/v1/chat/completions
CHAT_MODEL_NAME=blank
```

**Important**: Replace with your actual ngrok URL!

### 3. Start the Frontend

```bash
# In frontend directory
npm run dev
```

### 4. Open the Dashboard

Navigate to `http://localhost:3000` (or your frontend URL)

### 5. Look for the Chat Button

You'll see a **purple circular button** with a chat icon in the **bottom right corner** of the screen.

### 6. Click to Open

- Click the button to open the chat window
- You'll see a welcome message and 5 suggested questions
- Click any suggested question or type your own

## 💬 Example Questions

Click the suggested questions or try:

- "Why is my shipment delayed?"
- "Show me recent orders"
- "What items are low in inventory?"
- "Are there any exceptions?"
- "What's the status of shipment SHIP-20002?"
- "How many orders were placed today?"
- "Which carriers have delays?"
- "Show me high-priority orders"

## 🎨 Visual Features

### Chat Button
- Purple gradient circular button
- Hover effect (grows slightly)
- Chat icon in the center
- Always visible in bottom right

### Chat Window
- 380px wide × 550px tall
- Smooth slide-up animation
- Header with SNAPai branding
- Scrollable message area
- Input box with send button

### Messages
- User messages: Purple gradient (right side)
- AI messages: White background (left side)
- Avatar icons (🤖 for AI, 👤 for user)
- Timestamps below each message
- Smooth fade-in animations

### Typing Indicator
- Animated dots while AI is "thinking"
- Shows SNAPai is processing your question

## 🔧 Troubleshooting

### Chat button doesn't appear?
- Check browser console for errors
- Ensure frontend compiled successfully
- Look for the purple button in bottom right corner

### "Failed to get response" error?
1. **Check backend is running**: `http://localhost:8000/api/docs`
2. **Check LLM API URL**: Edit `.env` with correct ngrok URL
3. **Test backend directly**:
   ```bash
   curl -X POST http://localhost:8000/api/v1/chat/message \
     -H "Content-Type: application/json" \
     -d '{"message": "test", "include_context": true}'
   ```

### Suggested questions don't load?
- Backend must be running
- Check `/api/v1/chat/suggestions` endpoint

### LLM not responding?
- Verify your LLM server is running on ngrok
- Check `CHAT_API_URL` in `.env`
- Test LLM directly with curl to your ngrok URL

## 📱 Mobile Support

The chat is fully responsive:
- On mobile devices, chat window expands to full screen
- Touch-friendly buttons
- Smooth animations

## 🎯 Next Steps

Once everything is working:

1. **Test with real questions** - Ask about your actual shipments/orders
2. **Customize styling** - Edit `Chat.css` to match your brand colors
3. **Add features** - Voice input, file attachments, etc.
4. **Train LLM** - Improve responses with more specific supply chain knowledge

## 🎨 Customization

Want to change the purple theme? Edit `Chat.css`:

```css
/* Change gradient colors */
background: linear-gradient(135deg, #YOUR_COLOR1 0%, #YOUR_COLOR2 100%);
```

Change button position? Edit `.chat-widget`:

```css
.chat-widget {
  bottom: 20px;  /* Distance from bottom */
  right: 20px;   /* Distance from right */
}
```

---

**Enjoy your new AI assistant! 🚀**
