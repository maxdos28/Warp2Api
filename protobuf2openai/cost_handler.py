"""
Cost and Usage Handler for Warp2Api
处理API调用成本和token使用情况的专用模块
"""

import json
import time
from typing import Dict, Optional, Any
from .logging import logger


class CostHandler:
    """成本和使用情况处理器"""
    
    def __init__(self):
        self.total_requests = 0
        self.total_cost = 0.0
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        
    def extract_cost_from_bridge_response(self, bridge_response: Dict[str, Any]) -> Optional[float]:
        """从bridge响应中提取成本信息"""
        try:
            if not isinstance(bridge_response, dict):
                return None
                
            # 尝试从parsed_events中提取cost
            parsed_events = bridge_response.get("parsed_events", [])
            for event in parsed_events:
                if isinstance(event, dict):
                    event_type = event.get("event_type", "")
                    if "FINISHED" in event_type:
                        parsed_data = event.get("parsed_data", {})
                        finished = parsed_data.get("finished", {})
                        if isinstance(finished, dict):
                            request_cost = finished.get("request_cost", {})
                            if isinstance(request_cost, dict):
                                exact_cost = request_cost.get("exact")
                                if exact_cost is not None:
                                    return float(exact_cost)
            
            # 如果没找到，尝试直接从响应中查找
            if "request_cost" in bridge_response:
                cost_info = bridge_response["request_cost"]
                if isinstance(cost_info, dict):
                    exact_cost = cost_info.get("exact")
                    if exact_cost is not None:
                        return float(exact_cost)
                elif isinstance(cost_info, (int, float)):
                    return float(cost_info)
                    
            return None
            
        except Exception as e:
            logger.warning(f"[CostHandler] Failed to extract cost: {e}")
            return None
    
    def extract_token_usage(self, bridge_response: Dict[str, Any]) -> Dict[str, int]:
        """从bridge响应中提取token使用信息"""
        try:
            input_tokens = 0
            output_tokens = 0
            
            # 尝试从parsed_events中提取token信息
            parsed_events = bridge_response.get("parsed_events", [])
            for event in parsed_events:
                if isinstance(event, dict):
                    event_type = event.get("event_type", "")
                    if "FINISHED" in event_type:
                        parsed_data = event.get("parsed_data", {})
                        finished = parsed_data.get("finished", {})
                        if isinstance(finished, dict):
                            # 检查context_window_info
                            context_info = finished.get("context_window_info", {})
                            if isinstance(context_info, dict):
                                usage_ratio = context_info.get("context_window_usage", 0.0)
                                if usage_ratio > 0:
                                    # 估算token数量（假设200k上下文窗口）
                                    estimated_tokens = int(usage_ratio * 200000)
                                    input_tokens = max(input_tokens, estimated_tokens)
            
            # 如果没有找到token信息，根据响应文本估算
            response_text = bridge_response.get("response", "")
            if response_text and output_tokens == 0:
                # 粗略估算：每4个字符约等于1个token
                output_tokens = max(1, len(response_text) // 4)
                
            # 如果input_tokens为0，设置一个合理的最小值
            if input_tokens == 0:
                input_tokens = max(1, len(str(bridge_response).get("request_size", 0)) // 4)
            
            return {
                "prompt_tokens": input_tokens,
                "completion_tokens": output_tokens, 
                "total_tokens": input_tokens + output_tokens
            }
            
        except Exception as e:
            logger.warning(f"[CostHandler] Failed to extract token usage: {e}")
            return {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}
    
    def format_cost_display(self, cost: Optional[float]) -> str:
        """格式化成本显示"""
        if cost is None or cost <= 0:
            return "Cost: unavailable"
        elif cost < 0.01:
            return f"Cost: <$0.01"
        else:
            return f"Cost: ${cost:.4f}"
    
    def record_request(self, bridge_response: Dict[str, Any]):
        """记录请求信息"""
        try:
            self.total_requests += 1
            
            cost = self.extract_cost_from_bridge_response(bridge_response)
            if cost is not None and cost > 0:
                self.total_cost += cost
                
            usage = self.extract_token_usage(bridge_response)
            self.total_input_tokens += usage.get("prompt_tokens", 0)
            self.total_output_tokens += usage.get("completion_tokens", 0)
            
            logger.info(f"[CostHandler] Request recorded - Cost: {self.format_cost_display(cost)}, "
                       f"Tokens: {usage.get('prompt_tokens', 0)}+{usage.get('completion_tokens', 0)}")
                       
        except Exception as e:
            logger.warning(f"[CostHandler] Failed to record request: {e}")
    
    def get_session_stats(self) -> Dict[str, Any]:
        """获取会话统计信息"""
        return {
            "total_requests": self.total_requests,
            "total_cost": self.total_cost,
            "total_cost_display": self.format_cost_display(self.total_cost) if self.total_cost > 0 else "No cost data",
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "average_cost_per_request": self.total_cost / max(1, self.total_requests) if self.total_cost > 0 else 0
        }
    
    def create_usage_response(self, bridge_response: Dict[str, Any]) -> Dict[str, Any]:
        """创建符合OpenAI格式的usage响应"""
        usage = self.extract_token_usage(bridge_response)
        cost = self.extract_cost_from_bridge_response(bridge_response)
        
        response = {
            "usage": usage
        }
        
        # 只有在有有效成本信息时才添加成本字段
        if cost is not None and cost > 0:
            response["cost"] = {
                "exact": cost,
                "display": self.format_cost_display(cost)
            }
        
        return response


# 全局成本处理器实例
cost_handler = CostHandler()


def get_cost_handler() -> CostHandler:
    """获取全局成本处理器"""
    return cost_handler


def extract_and_format_cost(bridge_response: Dict[str, Any]) -> Dict[str, Any]:
    """提取并格式化成本信息"""
    handler = get_cost_handler()
    return handler.create_usage_response(bridge_response)


def record_api_cost(bridge_response: Dict[str, Any]):
    """记录API成本"""
    handler = get_cost_handler()
    handler.record_request(bridge_response)


def get_cost_stats() -> Dict[str, Any]:
    """获取成本统计信息"""
    handler = get_cost_handler()
    return handler.get_session_stats()