import os
import json
import re
from huggingface_hub import InferenceClient
from .logging_config import logger

class HFAnalyzerError(Exception):
    pass

class MarketSentimentAnalyzer:
    """
    Implements a Parallel Multi-Agent Consensus Architecture.
    Simulates multiple specialized agents (Technical, Fundamental, Risk) 
    analyzing the market context in parallel to reach a weighted decision.
    """
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("HUGGINGFACE_API_KEY")
        self.client = InferenceClient(token=self.api_key)
        self.model = "meta-llama/Llama-3.1-8B-Instruct"

    def analyze_sentiment(self, text: str, symbol: str = "BTCUSDT") -> dict:
        logger.info(f"Initiating Multi-Agent Parallel Analysis for: '{text}'")
        
        messages = [
            {
                "role": "system",
                "content": "You are a Multi-Agent Trading System. Respond ONLY in valid JSON format."
            },
            {
                "role": "user",
                "content": f"""
                Perform a parallel analysis on the context below for {symbol}.
                
                CONTEXT: "{text}"
                
                WORKFLOW:
                1. Technical Analyst Agent: Analyze price action/trends.
                2. Fundamental Analyst Agent: Analyze news impact.
                3. Risk Manager Agent: Analyze downside risks.
                4. Consensus Aggregator: Synthesize final signal.
                
                OUTPUT JSON (STRICT FORMAT):
                {{
                    "technical_view": "...",
                    "fundamental_view": "...",
                    "risk_check": "...",
                    "signal": "BUY|SELL|HOLD",
                    "sentiment": "Bullish|Bearish|Neutral",
                    "reasoning": "Consensus explanation"
                }}
                """
            }
        ]
        
        try:
            response = self.client.chat_completion(
                messages=messages,
                model=self.model,
                max_tokens=600,
                temperature=0.1
            )
            
            content = response.choices[0].message.content.strip()
            
            # Robust JSON Extraction using Regex
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if not json_match:
                logger.error(f"Failed to find JSON in response: {content}")
                raise HFAnalyzerError("AI returned invalid data format.")
                
            json_str = json_match.group(0)
            data = json.loads(json_str)
            
            # Extract fields with safe defaults
            full_reasoning = f"T-Agent: {data.get('technical_view')} | F-Agent: {data.get('fundamental_view')} | R-Agent: {data.get('risk_check')}"
            
            return {
                "sentiment": data.get("sentiment", "Neutral"),
                "confidence": 1.0,
                "signal": data.get("signal", "HOLD").upper(),
                "reasoning": data.get("reasoning", "No consensus reached."),
                "agent_details": full_reasoning,
                "text": text
            }
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON Parsing failed: {e}. Content was: {content}")
            raise HFAnalyzerError("AI response parsing failed. Try a simpler context.")
        except Exception as e:
            logger.error(f"Multi-Agent Analysis failed: {e}")
            raise HFAnalyzerError(f"Parallel Consensus Engine failed: {e}")
