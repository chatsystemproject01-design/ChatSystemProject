from app import create_app
from app.services.ai_service import AIService
import traceback

app = create_app()

with app.app_context():
    try:
        print("Start scan")
        ai_service = AIService()
        res = ai_service.detect_toxic("alo tk cu")
        print("Toxicity result isToxic:", res['isToxic'])
        
    except Exception as e:
        print("Exception")
