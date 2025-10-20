"""
Generation Module
Handles text generation using Gemini API
"""

import asyncio
import logging
import time
import httpx
import json
from typing import Optional, Dict, Any
from core.config import config


class Generator:
    """Text generator using Gemini API"""
    
    def __init__(self, config_obj):
        self.config = config_obj
        self.gemini_api_key = config_obj.gemini_api_key
        self.is_ready = True
    
    async def generate(self, query: str, context: str) -> str:
        """
        Generate response using Gemini API
        
        Args:
            query: User query
            context: Retrieved context
            
        Returns:
            Generated response
        """
        return await self._generate_with_gemini(query, context)
    
    async def _generate_with_gemini(self, query: str, context: str) -> str:
        """Generate response using Gemini"""
        if not self.gemini_api_key:
            raise ValueError("Gemini API key not configured")
        
        try:
            t0 = time.perf_counter()
            prompt = self._build_prompt(query, context)
            
            # Log the prompt being sent to كيمو
            logging.getLogger("simple-rag.generator").info(
                "كيمو prompt prepared",
                extra={
                    'operation': 'kimo_prompt',
                    'query': query[:100] + "..." if len(query) > 100 else query,
                    'context_length': len(context),
                    'prompt_length': len(prompt),
                    'model': 'kimo_gemini'
                }
            )
            
            payload = {
                "contents": [{
                    "parts": [{
                        "text": prompt
                    }]
                }],
                "generationConfig": {
                    "temperature": self.config.temperature,
                    "maxOutputTokens": self.config.max_tokens
                }
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{self.config.gemini_model}:generateContent?key={self.gemini_api_key}",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    candidates = result.get("candidates", [])
                    if candidates:
                        content = candidates[0].get("content", {})
                        parts = content.get("parts", [])
                        if parts:
                            generated_text = parts[0].get("text", "معذرة، مش قادر أجاوب على السؤال ده.")
                            
                            # Log the actual response from كيمو
                            logging.getLogger("simple-rag.generator").info(
                                "كيمو response generated elapsed_ms=%d",
                                int((time.perf_counter()-t0)*1000),
                                extra={
                                    'operation': 'kimo_response',
                                    'query': query[:100] + "..." if len(query) > 100 else query,
                                    'response': generated_text,
                                    'response_length': len(generated_text),
                                    'model': 'kimo_gemini'
                                }
                            )
                            
                            return generated_text
                    
                    logging.getLogger("simple-rag.generator").warning(
                        "كيمو response empty - no valid content in Gemini response",
                        extra={
                            'operation': 'kimo_empty_response',
                            'query': query[:100] + "..." if len(query) > 100 else query,
                            'gemini_result': str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
                        }
                    )
                    return "معذرة، مش قادر أجاوب على السؤال ده."
                else:
                    raise Exception(f"Gemini API error: {response.status_code}")
                    
        except Exception as e:
            print(f"❌ Gemini generation failed: {e}")
            logging.getLogger("simple-rag.generator").exception("Gemini generation failed: %s", str(e))
            return f"معذرة، حصل خطأ في توليد الإجابة: {str(e)}"
    
    def _build_prompt(self, query: str, context: str) -> str:
        """Build the prompt for generation"""
        prompt = f"""أنت كيمو، مساعد ذكي مصري يتحدث باللهجة المصرية. مهمتك هي الإجابة على الأسئلة بناءً على المعلومات المتاحة فقط.

المعلومات المتاحة في قاعدة البيانات:
{context}

السؤال: {query}

قواعد الإجابة:
1. استخدم اللهجة المصرية في جميع إجاباتك
2. إذا كان السؤال عن معلومات متاحة في النص أعلاه، أجب بناءً عليها
3. إذا كان السؤال تحية عامة (مثل: عامل إيه، صباح الخير، إزيك، إلخ)، أجب بتحية مصرية ودودة
4. إذا كان السؤال خارج نطاق المعلومات المتاحة، قل بوضوح: "معذرة، مش عندي معلومات عن ده في قاعدة البيانات بتاعتي"
5. كن ودود ومصري في أسلوبك

الإجابة:"""
        
        return prompt
    
    async def check_gemini_health(self) -> bool:
        """Check if Gemini API is available"""
        if not self.gemini_api_key:
            return False
        
        try:
            payload = {
                "contents": [{
                    "parts": [{
                        "text": "مرحبا"
                    }]
                }]
            }
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{self.config.gemini_model}:generateContent?key={self.gemini_api_key}",
                    json=payload
                )
                return response.status_code == 200
        except Exception:
            return False
    
    async def get_available_models(self) -> Dict[str, Any]:
        """Get information about available models"""
        gemini_healthy = await self.check_gemini_health()
        
        return {
            "gemini": {
                "available": gemini_healthy,
                "model": self.config.gemini_model,
                "api_key_configured": bool(self.gemini_api_key)
            }
        }