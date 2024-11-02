from flask import Flask, render_template, request, jsonify
import os
import random
from gtts import gTTS
import pymongo
import google.generativeai as genai
from datetime import datetime

app = Flask(__name__)

# MongoDB connection
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client['Viva_Viva_Online_db']
collection = db['Question_Generated']

# Function to convert text to audio and return file path
def text_to_audio(text, file_name="Temp_audio/Question.mp3", language='en'):
    tts = gTTS(text=text, lang=language, slow=False)
    tts.save(file_name)
    return file_name

# Fetch questions from MongoDB
def fetch_questions_from_mongodb():
    document = collection.find_one()
    document = document['data']
    understanding_questions = document.get('Understanding questions', [])
    remembering_questions = document.get('Remembering level questions', [])
    application_questions = document.get('Application level questions', [])
    mcqs = document.get('Multiple-choice questions', [])
    all_questions = understanding_questions + remembering_questions + application_questions
    mcq_questions = [mcq.get('question', '') for mcq in mcqs]
    all_questions += mcq_questions
    return all_questions

# Select random questions
def select_random_questions(all_questions, num_questions=5):
    return random.sample(all_questions, num_questions) if len(all_questions) >= num_questions else []

# Compare results using Generative AI
def compare_results(query, user_response):
    api = "AIzaSyDbc4izW_sEFLkiqmQgym-_RtYUN3Rn0lw"  
    genai.configure(api_key=api)

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction='''Context:
        You are an AI evaluator assigned to assess the quality of responses provided by a student during a viva exam. Your role is to evaluate each response based on several criteria and generate an accuracy score between 1 and 10.
        Only return an accuracy score between 1 and 10.'''
    )
    prompt = f"Question: {query}\nUser's response: {user_response}"
    response = model.generate_content(prompt)
    return float(response.text.strip())

# Home page route
@app.route('/')
def index():
    all_questions = fetch_questions_from_mongodb()
    selected_questions = select_random_questions(all_questions)
    return render_template('index.html', questions=selected_questions)

# API to play audio
@app.route('/play-audio', methods=['POST'])
def play_audio():
    question = request.form['question']
    file_name = text_to_audio(question)
    return jsonify({'audio_file': file_name})

# API to evaluate the user's response
@app.route('/evaluate', methods=['POST'])
def evaluate():
    question = request.form['question']
    user_response = request.form['user_response']
    score = compare_results(question, user_response)
    return jsonify({'score': score})

if __name__ == "__main__":
    app.run(debug=True)
