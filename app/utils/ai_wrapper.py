import requests
import json
from app.config.settings import configs

class AIWrapper:
    @staticmethod
    def summarize(text_content):
        if not configs.AI_API_KEY:
            return "AI Summary is disabled (Missing API Key)."

        headers = {
            "Authorization": f"Bearer {configs.AI_API_KEY}",
            "Content-Type": "application/json"
        }

        prompt = f"""Hãy tóm tắt nội dung cuộc trò chuyện dưới đây một cách tự nhiên và chính xác bằng tiếng Việt.
Yêu cầu:
1. Trình bày rõ ràng các ý chính, không dùng các ký tự lạ.
2. Nếu có quyết định hoặc mốc thời gian, hãy nêu rõ.
3. Không trả về các ký tự xuống dòng '\\n' dư thừa trong nội dung, hãy ngắt dòng bằng cách xuống dòng thật.
4. Xưng hô chuyên nghiệp.

Nội dung tin nhắn:
{text_content}"""

        payload = {
            "model": configs.AI_MODEL,
            "messages": [
                {"role": "system", "content": "You are a professional assistant that summarizes chat conversations."},
                {"role": "user", "content": prompt}
            ]
        }

        try:
            response = requests.post(
                configs.AI_API_URL,
                headers=headers,
                data=json.dumps(payload),
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            result = data['choices'][0]['message']['content']
            return result.strip()
        except Exception as e:
            return f"Error while calling AI Service: {str(e)}"

    @staticmethod
    def rag_query(context, question):
        if not configs.AI_API_KEY:
            return "AI Chatbot is disabled (Missing API Key)."

        headers = {
            "Authorization": f"Bearer {configs.AI_API_KEY}",
            "Content-Type": "application/json"
        }

        prompt = f"""Bạn là một trợ lý thông minh của công ty. Hãy dựa vào các thông tin (Context) dưới đây để trả lời câu hỏi của người dùng. 
Nếu thông tin dưới đây không có câu trả lời, hãy lịch sự thông báo rằng bạn không tìm thấy thông tin phù hợp trong cơ sở dữ liệu nội bộ.

Context:
{context}

Câu hỏi: {question}
Trả lời:"""

        payload = {
            "model": configs.AI_MODEL,
            "messages": [
                {"role": "system", "content": "Bạn chỉ trả lời dựa trên thông tin được cung cấp. Không tự ý bịa đặt thông tin ngoài."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3 # Thấp để tránh AI lan man
        }

        try:
            response = requests.post(
                configs.AI_API_URL,
                headers=headers,
                data=json.dumps(payload),
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content'].strip()
        except Exception as e:
            return f"Error while calling AI Service: {str(e)}"

    @staticmethod
    def analyze_toxicity(text):
        if not configs.AI_API_KEY:
            return False, "AI check disabled"

        headers = {
            "Authorization": f"Bearer {configs.AI_API_KEY}",
            "Content-Type": "application/json"
        }

        prompt = f"""Phân tích đoạn văn bản sau đây xem có chứa từ ngữ độc hại, xúc phạm hoặc thô tục không.
Chỉ trả về JSON theo mẫu: {{"isToxic": true/false, "reason": "Lý do bằng tiếng Việt"}}.

Văn bản: "{text}\"
JSON:"""

        payload = {
            "model": configs.AI_MODEL,
            "messages": [
                {"role": "system", "content": "Bạn là chuyên gia kiểm duyệt. Bạn LUÔN LUÔN trả về JSON."},
                {"role": "user", "content": prompt}
            ]
        }

        try:
            import json
            response = requests.post(
                configs.AI_API_URL,
                headers=headers,
                data=json.dumps(payload),
                timeout=15
            )
            data = response.json()
            content = data['choices'][0]['message']['content']
            result = json.loads(content)
            return result.get('isToxic', False), result.get('reason', "Không có lý do")
        except Exception as e:
            return False, f"Không thể phân tích bằng AI: {str(e)}"
