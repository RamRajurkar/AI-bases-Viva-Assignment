# LATEST UPDATES ARE BROUGHT HERE

import os
import random
from playsound import playsound
from gtts import gTTS
import speech_recognition as sr
import google.generativeai as genai
import pymongo
import time

file_name = 'Temp_audio/Question.mp3'

# Connect to MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client['Question_Generated']  # Use your database name
collection = db['Viva_Vista']  # Use your collection name


# Function to convert text to audio
def text_to_audio(text, file_name, language='en'):
    tts = gTTS(text=text, lang=language, slow=False)
    tts.save(file_name)
    print(f"Audio saved as {file_name}")

# Function to play an audio file
def play_audio(file_name):
    playsound(file_name)

# Fetch questions from MongoDB
def fetch_questions_from_mongodb():
    document = collection.find_one()
    
    # Extract questions from different categories
    understanding_questions = document.get('Understanding questions', [])
    remembering_questions = document.get('Remembering level questions', [])
    application_questions = document.get('Application level questions', [])
    mcqs = document.get('MCQs', [])
    
    # Combine all questions into one list
    all_questions = understanding_questions + remembering_questions + application_questions
    mcq_questions = [mcq.get('question', '') for mcq in mcqs]  # Extract MCQ questions
    all_questions += mcq_questions
    
    return all_questions

# Function to randomly select questions
def select_random_questions(all_questions, num_questions=5):
    if len(all_questions) < num_questions:
        print("Not enough questions available.")
        return []
    
    # Randomly select 5 unique questions
    selected_questions = random.sample(all_questions, num_questions)
    
    return selected_questions

# Generator function to yield questions one by one
def question_generator(selected_questions):
    total_score = 0
    for question in selected_questions:
        print(f"Current question: {question}")
        
        # Convert the question to audio
        text_to_audio(question, file_name)
        
        # Play the audio
        play_audio(file_name)
        
        # Prompt the user to repeat or move to the next question
        while True:
            choice = input("Do you want to repeat the question? [Y/n]: ").strip().lower()
            if choice == "y":
                play_audio(file_name)
            elif choice == "n":
                answer = recognize_response()
                score = compare_results(question, answer)
                print("Accuracy:", score)
                total_score += score
                print("Moving to the next question...\n")
                break
            else:
                print("Invalid choice, please enter 'Y' or 'N'.")
        
        # Remove the audio file after use
        if os.path.exists(file_name):
            os.remove(file_name)

    # Calculate and display average accuracy score
    avg_score = total_score / len(selected_questions)
    print(f"Average Accuracy Score: {avg_score}")
    time.sleep(1)

# Function to capture audio and recognize speech
def recognize_response():
    recognizer = sr.Recognizer()
    text = ""  # Initialize text to avoid undefined variable issues
    with sr.Microphone() as source:
        print("Adjusting for ambient noise... Please wait.")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("Listening for speech... Speak now.")
        audio_data = recognizer.listen(source, timeout=5)
        try:
            print("Processing audio...")
            text = recognizer.recognize_google(audio_data)
            print("You said:", text)
        except sr.WaitTimeoutError:
            print("No speech detected within the timeout duration.")
        except sr.UnknownValueError:
            print("Sorry, I could not understand the audio.")
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
    return text

# Function to compare the user's response with the query using Generative AI
def compare_results(query, user_response):
    api = "AIzaSyDbc4izW_sEFLkiqmQgym-_RtYUN3Rn0lw"  
    genai.configure(api_key=api)

    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction='''
        Context:
        You are an AI evaluator assigned to assess the quality of responses provided by a student during a viva exam. Your role is to evaluate each response based on several criteria and generate an accuracy score between 1 and 10.
        only return or give a accuracy score that is between 1 and 10 .and not any other information is needed.
        '''
    )
    prompt = f'''
    Question: {query}
    User's response: {user_response}
    '''
    response = model.generate_content(prompt)
    # Ensure the response is returned as a float for score calculation
    return float(response.text.strip())

# Main function to run the process
def main():
    # Fetch all questions from MongoDB
    all_questions = fetch_questions_from_mongodb()
    
    # Select random questions
    selected_questions = select_random_questions(all_questions)
    
    # Create a generator to iterate through the questions one by one
    if selected_questions:
        question_generator(selected_questions)

if __name__ == "__main__":
    main()
