import os
import json
import PyPDF2
import google.generativeai as genai
import csv
import pymongo

csv_file_path = 'Generated_Questions/Questions.csv'  # Replace with path of output csv file
pdf_path = "Notes/JAVA_Notes.pdf"  # Replace with the actual path to your PDF
# Configure the Gemini API key,
genai.configure(api_key="AIzaSyDbc4izW_sEFLkiqmQgym-_RtYUN3Rn0lw")

# Set up the model configuration 
generation_config = {
    "temperature": 1,
    "top_p": 0.95,
    "top_k": 64,
    "max_output_tokens": 8192,
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
def generate_questions_gemini(pdf_text, num_understanding=10, num_remembering=15, num_mcqs=10, num_application=5):
    system_prompt = f"""
    Based on the provided document, generate the following types of questions:

    1. Understanding questions: Focus on key concepts, relationships, and ideas from the text, requiring the reader to explain or interpret. Generate {num_understanding} such questions.

    2. Remembering level questions: Fact-based questions, asking for specific details, definitions, or key facts from the document. Generate {num_remembering} such questions.

    3. Application level questions: Real-world scenario questions that apply the document's concepts. Generate {num_application} such questions.

    4. Multiple-choice questions (MCQs): Generate {num_mcqs} MCQs with 4 options.
    format for MCQs options :
    option1 option2 option3 option4
    provide no solutions for MCQs


    Ensure coverage across various sections of the document and test conceptual understanding, recall, and application.
    
    Document Text:
    {pdf_text}
    """

    # Start a chat session with the model
    chat_session = model.start_chat(history=[])

    # Send the prompt along with the PDF text to generate questions
    response = chat_session.send_message(system_prompt)
    return json.loads(response.text)

# Function to store JSON data in MongoDB
def store_json_in_mongodb(json_data, db_name="Question_Generated", collection_name="Viva_Vista"):
    try:
        # Establish a connection to MongoDB
        client = pymongo.MongoClient("mongodb://localhost:27017/")  # Replace with your MongoDB connection string if needed
        
        # Select the database and collection
        db = client[db_name]
        collection = db[collection_name]

        # Insert the JSON data into the collection
        collection.insert_one(json_data)
        print(f"Data successfully written to MongoDB in database '{db_name}', collection '{collection_name}'")
        
    except pymongo.errors.ConnectionError as e:
        print(f"Could not connect to MongoDB: {e}")

# Function to convert JSON to CSV
def json_to_csv(json_data, csv_file_path):
    try:
        # Open CSV file for writing
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # Write header row
            writer.writerow(['Question Type', 'Question', 'Options'])

            # Write Understanding questions
            for question in json_data.get('Understanding questions', []):
                writer.writerow(['Understanding', question, ''])

            # Write Remembering level questions
            for question in json_data.get('Remembering level questions', []):
                writer.writerow(['Remembering', question, ''])

            # Write MCQs
            for mcq in json_data.get('Multiple-choice questions', []):
                question = mcq.get('question', '')
                options = '; '.join(mcq.get('options', []))  # Ensures options are joined by semicolon
                writer.writerow(['MCQ', question, options])

            # Write Application level questions
            for question in json_data.get('Application level questions', []):
                writer.writerow(['Application', question, ''])

        print(f"Data successfully written to {csv_file_path}")

    except (json.JSONDecodeError, IOError) as e:
        print(f"Error: {e}")

# Main function
def main(pdf_path, num_questions):
    # Extract text from the PDF
    pdf_text = extract_text_from_pdf(pdf_path)

    # If text extraction was successful, proceed to question generation
    if pdf_text:
        print(f"Extracted text from {pdf_path}:\n{pdf_text[:100]}...")  # Print first 100 chars of the text

        # Generate questions using Gemini AI
        questions = generate_questions_gemini(pdf_text, num_understanding=10, num_remembering=15, num_mcqs=10, num_application=5)

        # Convert JSON output to CSV
        json_to_csv(questions, csv_file_path)

        # Store JSON output in MongoDB
        store_json_in_mongodb(questions)

    else:
        print("No text extracted from the PDF.")

if __name__ == "__main__":

    # Number of random questions to generate (parameters are used inside generate_questions_gemini)
    num_questions = 5  # This is not used directly but kept for reference

    # Run the main function
    main(pdf_path, num_questions)
