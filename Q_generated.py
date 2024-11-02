import csv

# Function to write the JSON data to a CSV file
def write_json_to_csv(json_data, csv_filename):
    try:
        with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)

            # Write the CSV header
            writer.writerow(['Category', 'Question', 'Options'])

            # Process understanding and remembering questions
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

            print("Data successfully written to CSV!")
    except Exception as e:
        print(f"Error writing to CSV: {e}")

# Sample JSON data
json_data = {
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
    {
      "question": "What is Sachin Tendulkar's nickname?",
      "options": [
        "The Master Blaster",
        "The Little Master",
        "The God of Cricket",
        "All of the above"
      ]
    },
    # ... (Other MCQs)
  ]
}

# Call the function with the sample data and desired CSV file name
write_json_to_csv(json_data, 'tendulkar_questions.csv')
