import datetime
import re
import spacy
from app.database import get_connection
from flask import session
import openai
from openai import OpenAI
import csv
import os

client = OpenAI(api_key="sk-proj-SWiUtLtJYdMSq1LoOFPtT3BlbkFJI858QX1j6Ps0FlNRXqCU")

# # Load spaCy model
# nlp = spacy.load("en_core_web_sm")
# Initialize a state dictionary to store user details
state = {
    "full_name": None,
    "email": None,
    "phone_number": None
}

# def extract_order_ids(user_input):
#     # Regular expression to find phrases like "check order", "order status", etc.
#     pattern = re.compile(r'\b(?:check|status|order)\b.*?\b(\d+)\b', re.IGNORECASE)
#     matches = pattern.findall(user_input)
#     return matches

# def extract_user_details(user_input):
#     doc = nlp(user_input)
#     details = {}
#     for ent in doc.ents:
#         if ent.label_ == "PERSON":
#             details["name"] = ent.text
#         elif ent.label_ == "EMAIL":
#             details["email"] = ent.text
#         elif ent.label_ == "PHONE":
#             details["phone"] = ent.text
#     return details
#
#
# def is_human_representative_request(user_input):
#     doc = nlp(user_input.lower())
#     keywords = {"human", "person", "representative", "agent", "someone"}
#     request_phrases = {"talk to", "speak to", "need help from", "need assistance from", "answer me", "reply to me"}
#
#     words = {token.text for token in doc}
#     if any(phrase in user_input.lower() for phrase in request_phrases) and keywords.intersection(words):
#         return True
#     return False


def query_database():
    conn = get_connection()
    c = conn.cursor()

    # Query both tables
    c.execute("SELECT order_id, status FROM orders")
    table1_results = c.fetchall()
    c.execute("SELECT * FROM service_requests")
    table2_results = c.fetchall()

    conn.close()
    return table1_results

# def generate_prompt(user_input):
#     table1_results = ""
#     cnt = 0
#     for x, y in query_database():
#         cnt+=1
#         table1_results += f"{cnt}.(Order ID: {x}, Status: {y}); "
#
#     prompt = f"User query: {user_input}\n\nIf a user askes to check an order or an order status, you ask them kindly for order ID, unless they already gave it to you. Upon receiving an order ID of 5 numbers (or if you already received it while they were asking you), you should answer according to the following orders table: \n{table1_results}\n If you didn't find the order ID, notify the user. \n\nIf a user asks for a human representative you ask for their phone, email and full name. If one or more of the details are missing, ask for it."
#
#     return prompt

# Function to save contact information to a CSV file
def save_to_csv(full_name, email, phone_number):
    # Generate a unique value using the current timestamp
    unique_value = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f'contact_info_{unique_value}.csv'

    # Check if the file already exists
    file_exists = os.path.isfile(filename)

    # Open the file in append mode
    with open(filename, mode='a', newline='') as file:
        fieldnames = ['Full Name', 'Email', 'Phone Number']
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        # Do not write the header row
        # Write the data row
        writer.writerow({'Full Name': full_name, 'Email': email, 'Phone Number': phone_number})

def update_state(user_input, state):
    # # Use GPT-3.5 to extract details
    # details = client.chat.completions.create(
    #     model="ft:gpt-3.5-turbo-0125:personal:rb:9gE63hlk",
    #     messages=[
    #         {"role": "system", "content": "Extract full name, email, and phone number from the user's response."},
    #         {"role": "user", "content": user_input}
    #     ]
    # ).choices[0].message.content

    prompt = f"""
        The user should give you the following details: full name, email, and phone number. You need to extract this data from the user's input and format is like so (<full_name>, <email>, <phone_number>. If data is missing from the details, notify the user too, and in the formatted data put None where data is missing."
        """

    details = client.chat.completions.create(
        model="ft:gpt-3.5-turbo-0125:personal:rb:9gE63hlk",
        messages=[
            {"role": "system", "content": "You are a user details extraction assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=10,
        n=1,
        stop=None,
        temperature=0.5,
    )


    # Parsing the details
    for line in details.split('\n'):
        if "full name" in line.lower():
            state['full_name'] = line.split(":")[-1].strip()
        elif "email" in line.lower():
            state['email'] = line.split(":")[-1].strip()
        elif "phone number" in line.lower():
            state['phone_number'] = line.split(":")[-1].strip()

def validate_full_name(name):
    return len(name.split()) > 1

def generate_details_prompt(state):
    if not state['full_name']:
        return "Please provide your full name."
    elif not state['email']:
        return "Please provide your email address."
    elif not state['phone_number']:
        return "Please provide your phone number."
    else:
        return None

def chatbot_response(user_input):
    """This response is entirly chatgpt-3.5-turbo fine-tuned """
    # if is_human_representative_request(user_input):
    #     return "Sure. I'll take your details so that someone can reach out to you. Please provide your contact details below."
    #
    # prompt = generate_prompt(user_input)
    # response = client.chat.completions.create(
    #     model="ft:gpt-3.5-turbo-0125:personal:rb:9gE63hlk",
    #     messages=[
    #         {"role": "user", "content": prompt},
    #     ],
    #     temperature=0,
    # )
    # return response.choices[0].message.content

    # Classify the user input to determine the intent
    intent = classify_intent(user_input)

    if intent == "Intent: check_order_status":
        table1_results = ""
        cnt = 0
        for x, y in query_database():
            cnt += 1
            table1_results += f"{cnt}.(Order ID: {x}, Status: {y}); "
        prompt = f"""
            User query: {user_input}\n\nIf a user asks to check an order or an order status, you ask them kindly for the order ID, unless they already gave it to you. Upon receiving an order ID of 5 numbers (or if you already received it while they were asking you), you should answer according to the following orders table: \n{table1_results}\nIf you didn't find the order ID, notify the user.
            """

    elif intent == "Intent: request_human_representative":
        prompt = f"""
                        User query: {user_input}\n\nIf a user asks for a human representative you ask for their phone, email, and full name. 
                        """

    elif intent == "Intent: personal_details_for_human_representative_request":
        update_state(user_input, state)
        if state['full_name'] and not validate_full_name(state['full_name']):
            state['full_name'] = None  # Reset full name if not valid

        prompt = generate_details_prompt(state)
        if not prompt:
            # All details are collected, generate CSV
            with open('user_details.csv', 'w', newline='') as csvfile:
                fieldnames = ['full_name', 'email', 'phone_number']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow(state)
            return "Thank you! Your details have been saved successfully."


    else:
        prompt = f"User query: {user_input}\n\nIntent: other. Please assist the user accordingly."

    response = client.chat.completions.create(
             model="ft:gpt-3.5-turbo-0125:personal:rb:9gE63hlk",
             messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=150,
        n=1,
        stop=None,
        temperature=0.7,
    )

    return response.choices[0].message.content



def check_order_status(order_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT status FROM orders WHERE order_id = ?', (order_id,))
    result = c.fetchone()
    conn.close()
    if result:
        return f"Order {order_id}: {result[0]}"
    else:
        return f"Order {order_id} not found."

def handle_service_request(name, email, phone):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM service_requests WHERE email = ? AND status = "open"', (email,))
    existing_request = c.fetchone()
    if existing_request:
        conn.close()
        return "A request for service has already been received and is being processed."

    c.execute('''
        INSERT INTO service_requests (name, email, phone, status)
        VALUES (?, ?, ?, "open")
    ''', (name, email, phone))
    conn.commit()
    conn.close()
    return "Your request for human assistance has been received. We will get in touch with you shortly."


def classify_intent(user_input):
    # Define the prompt to guide the model in classifying the user input
    prompt = f"""
    Classify the intent of the following user input:
    Input: "{user_input}"
    Intent options: [request_human_representative, personal_details_for_human_representative_request, check_order_status, other]
    Intent:
    """

    response = client.chat.completions.create(
             model="ft:gpt-3.5-turbo-0125:personal:rb:9gE63hlk",
             messages=[
            {"role": "system", "content": "You are an intent classification assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=10,
        n=1,
        stop=None,
        temperature=0.5,
    )

    classification = response.choices[0].message.content
    return classification

# test_inputs = [
#     "My phone is 1234873246, my email is sdf@dsfg.com and my name is Martha Peskety.",
#     "My phone is 5555555555",
#     "my email is vxciov@tryuitr.com and my name is Lincoln Junior.",
#     "Email: sdfghf@rityrpoed.com, Phone: 4569330953, Name: Stanley",
#     "name: luise phone:0546667899 mail:lula@loolie.com",
#     "What is the weather today?",
#     "Order me a pizza.",
#     "Book an appointment for me."
# ]
#
# for input_str in test_inputs:
#     print(f"'{input_str}' -> {classify_intent(input_str)}")

def is_human_representative_request(user_input):
    classification = classify_intent(user_input)
    return classification == "Intent: personal_details_for_human_representative_request"

# # Test the function
# for input_str in test_inputs:
#     print(f"'{input_str}' -> {is_human_representative_request(input_str)}")


# Example usage:
user_input = input("User: ")
while True:
    bot_response = chatbot_response(user_input)
    print("Bot:", bot_response)
    if "Thank you! Your details have been saved successfully." in bot_response:
        break
    user_input = input("User: ")