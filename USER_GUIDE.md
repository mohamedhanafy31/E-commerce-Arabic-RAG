# Arabic RAG System - User Guide

## 🌐 **Access Your System**

**Main Interface**: https://arabic-orchestrator-467535420147.us-central1.run.app/test

## 🔧 **Quick Setup**

### **1. Connect to the System**
- Click the **"Connect"** button
- The system will automatically use the correct Cloud Run URL
- Wait for "Connected successfully!" message

### **2. Configure Language**
- **Language**: Arabic (Egypt) - Default ✅
- **Voice Gender**: Male/Female/Auto
- **Speaking Rate**: Adjust as needed

### **3. Upload Documents**
- Drag and drop files into the **Document Upload** area
- Supported formats: PDF, TXT, DOCX, MD (Max 10MB)
- Click **"List Documents"** to see uploaded files

### **4. Query Documents**
- Type your question in Arabic in the **Query Text** field
- Click **"Query Documents"** to get AI responses
- Example: "ما هو محتوى المستندات المتاحة؟"

### **5. Voice Interaction**
- Click **"Start Recording"** to begin voice input
- Speak in Arabic
- Click **"Stop Recording"** when finished
- AI will respond with both text and audio

## 🚨 **Troubleshooting**

### **Connection Issues**
If you see connection errors:
1. **Check Server URL**: Should be `wss://arabic-orchestrator-467535420147.us-central1.run.app/ws/conversation`
2. **Clear Browser Cache**: Refresh the page (Ctrl+F5)
3. **Try Different Browser**: Chrome, Firefox, Safari, Edge

### **WebSocket Errors**
- **Error Code 1006**: Usually means wrong URL or network issue
- **Solution**: Ensure you're using the `wss://` URL (not `ws://localhost`)

### **Audio Issues**
- **Microphone Permission**: Allow microphone access when prompted
- **Browser Support**: Use modern browsers (Chrome, Firefox, Safari, Edge)
- **HTTPS Required**: Audio recording requires secure connection

## 📊 **System Status**

### **Health Check**
- Click **"Health Check"** to verify system status
- Should return: `{"status": "healthy"}`

### **System Stats**
- Click **"System Stats"** to see system information
- Shows vector store path and configuration

## 🎯 **Features Available**

✅ **Real-time WebSocket Communication**
✅ **Arabic Language Processing**
✅ **Document Upload and Management**
✅ **Voice Recognition (Arabic)**
✅ **Text-to-Speech (Arabic)**
✅ **Document Querying**
✅ **Conversational AI**
✅ **Session Management**
✅ **Error Recovery**

## 🌍 **Service URLs**

- **RAG System**: https://arabic-rag-system-467535420147.us-central1.run.app
- **ASR API**: https://arabic-asr-api-467535420147.us-central1.run.app
- **TTS API**: https://arabic-tts-api-467535420147.us-central1.run.app
- **Orchestrator**: https://arabic-orchestrator-467535420147.us-central1.run.app

## 📞 **Support**

If you encounter any issues:
1. Check the **Debug Console** for error messages
2. Try refreshing the page
3. Clear browser cache
4. Use a different browser

**Your Arabic RAG System is ready for production use!** 🚀
