from rest_framework.views import APIView
from rest_framework.response import Response
from chatbot.services.llm_service import LLMService

class ChatView(APIView):
    def post(self, request):
        message = request.data.get("message")
        user_id = request.data.get("user_id")  # Optional, use for personalization

        llm = LLMService()
        response = llm.handle_parent_query(user_id, message)
        return Response({"response": response})
