import json
import PyPDF2
import google.generativeai as genai
import csv
import pymongo


# Configure the Gemini API key,
genai.configure(api_key="AIzaSyDbc4izW_sEFLkiqmQgym-_RtYUN3Rn0lw")

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
    generation_config = generation_config,
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
    Based on the provided document, generate questions in the following categories. Ensure the questions are detailed and relevant, covering key concepts from across the document.
    1. **Understanding Questions**: 
    - These questions should focus on the key concepts, relationships, and ideas presented in the document.
    - They should require the reader to explain, describe, or interpret concepts.
    - Generate {num_understanding} such questions. Example format:
        - "Explain the concept of [key term]. How does it relate to [another concept]?"

    2. **Remembering Level Questions**: 
    - Fact-based questions that focus on specific details, definitions, or key facts.
    - The questions should be straightforward, focusing on recalling specific information from the document.
    - Generate {num_remembering} such questions. Example format:
        - "What is the definition of [term] mentioned in the text?"

    3. **Application Level Questions**: 
    - These questions should apply the concepts from the document to real-world scenarios or practical situations.
    - They should require problem-solving or the application of learned concepts.
    - Generate {num_application} such questions. Example format:
        - "How would you apply the concept of [theory] to solve [specific problem]?"

    4. **Multiple-Choice Questions (MCQs)**: 
    - Each question should have 4 options without answers. Focus on varying difficulty levels and ensure that the questions span across key sections of the document.
    - Generate {num_mcqs} MCQs. Use the following format:
        Question: [MCQ question text]
        Options: 
        - A. [option1]
        - B. [option2]
        - C. [option3]
        - D. [option4]

    Ensure that all questions test conceptual understanding, recall, and the ability to apply knowledge.
    Do not give answer for any format question and generate all questions in the specific number provided ,not less not more.
    Generate response in a way that can be easily parsed or converted into csv format
    Document Text:
    {pdf_text}
    """
    
    # Start a chat session with the model
    chat_session = model.start_chat(history=[])

    # Send the prompt along with the PDF text to generate questions
    response = chat_session.send_message(system_prompt)

    try:
        return json.loads(response.text)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        return None
    # return json.loads(response.text)

# Function to store JSON data in MongoDB
def store_json_in_mongodb(json_data, collection_name,db_name="Question_Generated"):
    try:

        # Establish a connection to MongoDB
        client = pymongo.MongoClient("mongodb://localhost:27017/")  # Replace with your MongoDB connection string if needed
        
        # Select the database and collection
        db = client[db_name]
        collection = db[collection_name]

        print(type(json_data) )
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
            understanding_questions = json_data.get('Understanding questions', [])
            print(f"Understanding questions: {understanding_questions}")
            for question in understanding_questions:
                writer.writerow(['Understanding', question, ''])

            # Write Remembering level questions
            remembering_questions = json_data.get('Remembering level questions', [])
            print(f"Remembering level questions: {remembering_questions}")
            for question in remembering_questions:
                writer.writerow(['Remembering', question, ''])

            # Write MCQs
            mcqs = json_data.get('Multiple-choice questions', [])
            print(f"MCQs: {mcqs}")
            for mcq in mcqs:
                question = mcq.get('question', '')
                options = '; '.join(mcq.get('options', []))  # Ensures options are joined by semicolon
                writer.writerow(['MCQ', question, options])

            # Write Application level questions
            application_questions = json_data.get('Application level questions', [])
            print(f"Application level questions: {application_questions}")
            for question in application_questions:
                writer.writerow(['Application', question, ''])

        print(f"Data successfully written to {csv_file_path}")

    except Exception as e:
        print(f"An error occurred: {e}")


# Main function
def main(pdf_path):
    # Extract text from the PDF
    pdf_text = extract_text_from_pdf(pdf_path)

    # If text extraction was successful, proceed to question generation
    if pdf_text:
        print(f"Extracted text from {pdf_path}:\n{pdf_text[:100]}...")  # Print first 100 chars of the text

        # Generate questions using Gemini AI
        questions = generate_questions_gemini(pdf_text, num_understanding=10, num_remembering=15, num_mcqs=10, num_application=5)

        # Input the name for collection here :
        collection_name=input("Enter Name of Collection : ")

        csv_file_path = f'Generated_Questions/{collection_name}.csv'  # Replace with path of output csv file
        # Convert JSON output to CSV
        json_to_csv(questions, csv_file_path)

        # Store JSON output in MongoDB
        store_json_in_mongodb(questions,collection_name)

    else:
        print("No text extracted from the PDF.")

if __name__ == "__main__":

    # Number of random questions to generate (parameters are used inside generate_questions_gemini)
    num_questions = 5  # This is not used directly but kept for reference
    
    pdf_name = input("Enter PDF name : ")
    pdf_path = f"Notes/{pdf_name}.pdf"  # Replace with the actual path to your PDF

    # Run the main function
    main(pdf_path)
