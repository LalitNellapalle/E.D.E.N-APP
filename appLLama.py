from flask import Flask, request, jsonify
import requests
from transformers import pipeline
import random

# Grammar correction model from Hugging Face
grammar_checker = pipeline("text2text-generation", model="grammarly/coedit-large")

# Language model for chatbot feedback 
messages = [
    {"role": "user", "content": "Who are you?"},
]
chatbot_model = pipeline("text-generation", model="meta-llama/Meta-Llama-3-8B-Instruct")
chatbot_model(messages)

app = Flask(__name__)

# Your Google API key 
API_KEY = "AIzaSyAL2Y2IK7oJJ1TlZgRS0RIGo38dDrQ1p4s"

# Global variables for the user's native language and conversation topic
native_language = None
conversation_topic = None

# Save the native language and conversation topic
@app.route('/start_conversation', methods=['POST'])
def start_conversation():
    global native_language, conversation_topic

    data = request.json
    native_language = data.get('native_language')
    conversation_topic = data.get('conversation_topic')

    return jsonify({
        'message': f"Conversation started in English about {conversation_topic}"
    })

# Handle user responses during the conversation
@app.route('/conversation', methods=['POST'])
def conversation():
    global native_language, conversation_topic

    data = request.json
    user_response = data.get('user_response')

    # Step 1: Correct the grammar
    corrected_text = grammar_checker(user_response)[0]['generated_text']

    # If the user's grammar is correct, use the language model to generate varied compliments
    if user_response.strip().lower() == corrected_text.strip().lower():
        compliment_prompt = random.choice([
            "Give a friendly compliment to someone who just said something perfectly in English.",
            "Say something encouraging to someone practicing their English and doing well.",
            "Congratulate someone on using good grammar during an English conversation."
        ])
        chatbot_reply = chatbot_model(compliment_prompt, max_length=50)[0]['generated_text']
        
        # Continue the conversation naturally
        continue_prompt = f"Continue the conversation about {conversation_topic}."
        continuation = chatbot_model(continue_prompt, max_length=50)[0]['generated_text']

        return jsonify({
            'chatbot_reply': f"{chatbot_reply} {continuation}",
            'corrected_text': None,  # No correction needed
            'explanation': None  # No explanation needed
        })
    else:
        # Grammar mistake detected, provide a varied explanation
        explanation_prompt = f"Explain why the sentence '{user_response}' is incorrect and how to correct it: '{corrected_text}'"
        explanation = chatbot_model(explanation_prompt, max_length=50)[0]['generated_text']
        
        # Translate the explanation to the user's native language
        translated_explanation = translate_text(explanation, native_language)

        # Continue conversation in English, but explain the mistake in the native language
        continue_prompt = f"Continue the conversation about {conversation_topic}."
        continuation = chatbot_model(continue_prompt, max_length=50)[0]['generated_text']

        return jsonify({
            'chatbot_reply': continuation,  # Continue conversation in English
            'corrected_text': corrected_text,  # Corrected sentence in English
            'explanation': translated_explanation  # Explanation in native language
        })

# Function to translate text using Google API
def translate_text(text, target_language):
    url = f"https://translation.googleapis.com/language/translate/v2?key={API_KEY}"
    payload = {
        "q": text,
        "target": target_language
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        translation = response.json()

        return translation['data']['translations'][0]['translatedText']
    except requests.exceptions.RequestException as e:
        return "Error: Could not translate the text"

if __name__ == "__main__":
    app.run(debug=True)