from flask import Flask, request, jsonify
from google.cloud import translate_v2 as translate
import requests

app = Flask(__name__)

# Initialize Google Translation Client
translate_client = translate.Client()

# Global variables to store language and topic
native_language = None
conversation_topic = None

# Function to translate text to the user's native language
def translate_text(text, target_language):
    
    try:
        result = translate_client.translate(text, target_language=target_language)
        return result['translatedText']
    except Exception as e:
        print(f"Translation Error: {str(e)}")
        return f"Error translating text: {str(e)}"

# Function to simulate GPT API call (Using Hugging Face's BlenderBot or GPT-3)
def get_gpt_response(prompt):
    try:
        headers = {"Authorization": f"Bearer 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"}
        # Modify the prompt to give better context for a grammar correction and conversational practice
        structured_prompt = (
            f"You are an English tutor. The topic of conversation is {conversation_topic}. "
            f"The user said: '{prompt}'. Correct their grammar if needed, explain the correction, and continue the conversation naturally."
        )

        data = {"inputs": structured_prompt}
        response = requests.post(
            "https://api-inference.huggingface.co/models/facebook/blenderbot-1B-distill",  # Using BlenderBot 1B model
            headers=headers,
            json=data
        )

        # Check for successful response
        if response.status_code != 200:
            return f"Error: {response.status_code}, {response.text}"

        response_json = response.json()
        if 'generated_text' in response_json[0]:
            return response_json[0]['generated_text']
        else:
            return f"Unexpected response format: {response_json}"

    except Exception as e:
        print(f"Hugging Face API Error: {str(e)}")
        return f"Error getting GPT response: {str(e)}"



# Route to set the user's native language
@app.route('/set_language', methods=['POST'])
def set_language():
    global native_language
    try:
        data = request.json
        native_language = data.get('language', 'en')
        return jsonify({"message": f"Language set to {native_language}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to set the conversation topic
@app.route('/set_topic', methods=['POST'])
def set_topic():
    global conversation_topic
    try:
        data = request.json
        conversation_topic = data.get('topic', 'general')  # Default to 'general' if no topic is provided
        return jsonify({"message": f"Topic set to {conversation_topic}"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to process user input (check grammar and have conversation)
@app.route('/process_input', methods=['POST'])
def process_input():
    try:
        data = request.json
        user_input = data.get('input', '')

        # Send the user's input to GPT model to get a response
        gpt_response = get_gpt_response(user_input)

        # Example grammar correction logic
        if "I plays" in user_input:
            correction = "I play"
            explanation = f"You should say '{correction}' instead of 'I plays'."

            # Translate explanation to the user's native language
            translated_explanation = translate_text(explanation, native_language)
            return jsonify({
                "response": translated_explanation, 
                "gpt_response": gpt_response
            })

        # If grammar is correct, just return GPT response
        return jsonify({"response": gpt_response})
    
    except Exception as e:
        print(f"Error processing input: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
