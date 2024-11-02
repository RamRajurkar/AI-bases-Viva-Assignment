import json
import PyPDF2
import google.generativeai as genai
import csv
import pymongo
import os
from datetime import datetime

# Configure the Gemini API key
genai.configure(api_key="AIzaSyCEI1mwJSop93eUAvqURlGmo1bgvmR1KUA")

# Set up the model configuration
generation_config = {
    "temperature": 0.9,
    "top_p": 1,
    "top_k": 55,
    "max_output_tokens": 9000,
    "response_mime_type": "application/json",
}

# Initialize the Gemini model
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config,
)

# Function to extract text from a PDF
def extract_text_from_pdf(pdf_path):
    try:
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ""
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text()
        return text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        return ""

# Function to generate questions using Gemini AI
def generate_questions_gemini(pdf_text, num_understanding=20, num_remembering=15, num_mcqs=5, num_application=10):
    system_prompt = f"""
    Document : {pdf_text}

    Based on the provided document, generate questions in the following categories. Ensure the questions are detailed and relevant, covering key concepts from across the document.
    Structure the output in JSON format, where each question will have a category and a text field.
    Example structure for each question:
    {{
      "Understanding questions": [
        "What are the key factors that contributed to Sachin Tendulkar's early success in cricket?",
        # ... (Other questions)
      ],
      "Remembering level questions": [
        "When and where was Sachin Tendulkar born?",
        # ... (Other questions)
      ],
      "Application level questions": [
        "If you were to write a motivational speech for aspiring cricketers, how would you use Sachin Tendulkar's life as an example?",
        # ... (Other questions)
      ],
      "Multiple-choice questions": [
        {{
          "question": "What is Sachin Tendulkar's nickname?",
          "options": [
            "The Master Blaster",
            "The Little Master",
            "The God of Cricket",
            "All of the above"
          ]
        }},
        # ... (Other MCQs)
      ]
    }}

    1. **Understanding Questions**: 
    - These questions should focus on the key concepts, relationships, and ideas presented in the document.
    - Generate {num_understanding} such questions.

    2. **Remembering Level Questions**: 
    - Fact-based questions focusing on recalling specific information from the document.
    - Generate {num_remembering} such questions.

    3. **Application Level Questions**: 
    - Apply the concepts from the document to real-world scenarios or practical situations.
    - Generate {num_application} such questions.

    4. **Multiple-Choice Questions (MCQs)**: 
    - Each question should have 4 options. Generate {num_mcqs} MCQs.

    Generate not less not more questions than specified numbers.
    """

    # Start a chat session with the model
    chat_session = model.start_chat(history=[])
    response = chat_session.send_message(system_prompt)

    # Try to decode JSON response from Gemini
    try:
        return json.loads(response.text)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None

# Function to store JSON data in MongoDB
def store_json_in_mongodb(json_data, subject_name, collection_name="Question_Generated", db_name="Viva_Viva_Online_db"):
    try:
        # Establish connection to MongoDB
        client = pymongo.MongoClient("mongodb://localhost:27017/")
        db = client[db_name]
        collection = db[collection_name]

        # Add creation timestamp and subject name to the main document
        timestamp = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
        document = {
            "subject_name": subject_name,
            "Created_at": timestamp,
            "data": json_data  # Store the JSON data as is
        }

        # Insert the entire document in MongoDB
        collection.insert_one(document)

        print(f"Data successfully written to MongoDB in database '{db_name}', collection '{collection_name}'")
        
    except pymongo.errors.ConnectionError as e:
        print(f"Could not connect to MongoDB: {e}")

# Function to convert JSON to CSV
def write_json_to_csv(json_data, csv_filename):
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(csv_filename), exist_ok=True)
        
        with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Category', 'Question', 'Options'])

            # Iterate through each question in the JSON data
            for category, questions in json_data.items():
                if isinstance(questions, list):
                    # Check if it's a simple question list (Understanding/Remembering/Application)
                    if isinstance(questions[0], str):
                        for question in questions:
                            writer.writerow([category, question, None])
                    # Check if it's a multiple-choice questions list
                    elif isinstance(questions[0], dict):
                        for mcq in questions:
                            question = mcq.get('question', '')
                            options = ' | '.join(mcq.get('options', []))  # Join options with ' | '
                            writer.writerow([category, question, options])

        print(f"Data successfully written to CSV file: {csv_filename}")

    except Exception as e:
        print(f"Error writing to CSV: {e}")

# Main function
def main(pdf_path):
    # Extract text from the PDF
    pdf_text = extract_text_from_pdf(pdf_path)

    if pdf_text:
        print(f"Extracted text from {pdf_path}:\n{pdf_text[:100]}...")

        # Generate questions using Gemini AI
        questions = generate_questions_gemini(pdf_text, num_understanding=10, num_remembering=15, num_mcqs=10, num_application=5)
        
        if questions:
            subject_name = input("Enter Name of Subject/File: ")
            csv_file_path = f'Generated_Questions/{subject_name}.csv'

            # Convert JSON to CSV
            write_json_to_csv(questions, csv_file_path)

            # Store in MongoDB
            store_json_in_mongodb(questions, subject_name)
        else:
            print("No questions generated.")
    else:
        print("No text extracted from the PDF.")

if __name__ == "__main__":
    pdf = input("Enter the pdf Name: ")
    pdf_path = f"Notes/{pdf}.pdf"  # Replace with the actual path to your PDF
    main(pdf_path)
