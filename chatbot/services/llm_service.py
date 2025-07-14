import os
import requests
from chatbot.utils.retriever import get_child_profile, get_knowledge_chunks
from django.conf import settings


class LLMService:
    def build_prompt(self, child_profile, expert_chunks, query):
        gender_str = "female" if child_profile.get("gender") == 1 else "male"
        attention_map = ["not clinically significant", "mild symptoms", "severe symptoms"]

        return f"""
    You are a parenting assistant helping parents raise emotionally resilient and well-regulated children.

    A parent asks: "{query}"

    About their child:
    - Name: {child_profile.get('name')}
    - Age: {child_profile.get('age')}
    - Gender: {gender_str}
    - Screen Access: {"Yes" if child_profile.get('screen_access') else "No"}
    - Access Level: {"High" if child_profile.get('access_level') else "Low"}
    - Screen Time Frequency: {"High" if child_profile.get('frequency_level') else "Low"}
    - Content Quality: {"Low (stimulating or intense)" if child_profile.get('content_level') else "High (calm/educational)"}
    - Interactivity: {"Low (passive use)" if child_profile.get('interactivity_level') else "High (interactive)"}
    - Inattentive Symptoms: {attention_map[child_profile.get('inattentive_result', 0)]}
    - Hyperactive/Impulsive Symptoms: {attention_map[child_profile.get('hyperactive_result', 0)]}
    - Oppositional/Defiant Symptoms: {attention_map[child_profile.get('oppositional_result', 0)]}

    Relevant parenting guidance:
    {expert_chunks}

    Respond with an age-appropriate, warm, and actionable suggestion. Keep the tone supportive, clear, and sensitive to the child's behavioral and emotional needs.
    """

    def call_deepseek(self, prompt):
        url = settings.DEEPSEEK_API_URL
        headers = {
            "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        body = {
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        response = requests.post(url, headers=headers, json=body)

        try:
            response.raise_for_status()
            content = response.json()
            print("DeepSeek Response:", content) 
        except Exception as e:
            print("DeepSeek API ERROR:", e)
            print("Raw Response:", response.text)
            return "Sorry, something went wrong with the AI service."

        return content["choices"][0]["message"]["content"]

    def handle_parent_query(self, user_id, query):
        try:
            child_profile = get_child_profile(user_id)
            expert_chunks = get_knowledge_chunks(query)
            prompt = self.build_prompt(child_profile, expert_chunks, query)
            return self.call_deepseek(prompt)
        except Exception as e:
            print("Error handling parent query:", e)
            return "Sorry, I couldn't find the child's profile. Please check if it's set up in the system."
