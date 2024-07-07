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

context_flags = [False, False]


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


def validate_and_extract(details_str):
    details_list = details_str.split(",")
    full_name = details_list[0].strip()
    phone_number = details_list[1].strip()
    email = details_list[2].strip()

    if not re.compile(r"[^@]+@[^@]+\.[^@]+").match(email):
        email = "None"

    return full_name, phone_number, email

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


    prompt = f"""ser Input: {user_input}\n\n
        Extract the following details from the user's input: full name, email, and phone number. 
        Your response should be formatted as: (<full_name>,<phone_number>,<email>).
        If any data is missing, write None where it should've been in the format. Do not use 'John Doe' (and the likes of it) if it's not the user_input. If you got two words that look like a name and that's it, assume the user has given you only their full name. If the answer is nothing but numbers, assume the user has given you only their phone number. If the answer doesn't contain spaces and does contain @ assume the user has given you only their email."""



    details = client.chat.completions.create(
        model="ft:gpt-3.5-turbo-0125:personal:rb:9gE63hlk",
        messages=[
            {"role": "system", "content": "You are an assistant that extracts and formats user details accurately."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=50,
        n=1,
        stop=None,
        temperature=0.5,
    )
    print(details)


    # Parsing the details

    details = details.choices[0].message.content
    if "Output" in details:
        details = details[9:-1]
    else:
        details = details[1:-1]
    print(f"after trim: {details}")

    full_name, phone_number, email = validate_and_extract(details)
    if "None" not in full_name and validate_full_name(full_name):
        state["full_name"] = full_name
    if "None" not in phone_number:
        state["phone_number"] = phone_number
    if "None" not in email:
        state["email"] = email




def validate_full_name(name):
    return len(name.split()) > 1

def generate_details_prompt(state):
    if not state['full_name']:
        return "Please provide your full name."
    elif "None" in state['full_name']:
        return "Please provide your full name."
    elif not state['email'] or "None" in state['email']:
        return "Please provide your email address."
    elif not state['phone_number'] or "None" in state['phone_number']:
        return "Please provide your phone number."
    else:
        return None

def chatbot_response(user_input):
    """This response is entirly chatgpt-3.5-turbo fine-tuned """

    # Classify the user input to determine the intent
    intent = classify_intent(user_input)

    if intent == "Intent: check_order_status" or intent == "check_order_status" or ("only_numbers" in intent and context_flags[0]==True) or ("order_id" in intent and context_flags[0]==True):
        context_flags[0] = True
        context_flags[1] = False
        table1_results = ""
        cnt = 0
        for x, y in query_database():
            cnt += 1
            table1_results += f"{cnt}.(Order ID: {x}, Status: {y}); "
        prompt = f"""
            User query: {user_input}\n\nIf a user asks to check an order or an order status, you ask them kindly for the order ID, unless they already gave it to you. Upon receiving an order ID of 5 numbers (or if you already received it while they were asking you), you should answer according to the following orders table: \n{table1_results}\nIf you didn't find the order ID, notify the user.
            """
        print(prompt)

    elif intent == "Intent: request_human_representative" or intent == "request_human_representative" or "book_appointmen"in intent:
        context_flags[0] = False
        context_flags[1] = True
        prompt = f"""
                        User query: {user_input}\n\nIf a user asks for a human representative you ask for their phone, email, and full name. 
                        """

    elif intent == "Intent: personal_details_for_human_representative_request" or intent == "personal_details_for_human_representative_request" or "name" in intent or "email" in intent or ("only_numbers" in intent and context_flags[1]==True):
        print(context_flags)
        update_state(user_input, state)

        prompt = generate_details_prompt(state)
        if not prompt:
            # All details are collected, generate CSV
            with open('user_details.csv', 'w', newline='') as csvfile:
                fieldnames = ['full_name', 'email', 'phone_number']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                # writer.writeheader()
                writer.writerow(state)
            return "Thank you! Your details have been saved successfully."
        else:
            return prompt


    else:
        context_flags[0] = False
        context_flags[1] = False
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
    Intent options: [only_numbers, only_order_id, only_email, only_name, request_human_representative, personal_details_for_human_representative_request, check_order_status, other]
    Don't pay attention to exclamation marks.
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

test_inputs = [
    "My phone is 1234873246, my email is sdf@dsfg.com and my name is Martha Peskety.",
    "My phone is 5555555555",
    "my email is vxciov@tryuitr.com and my name is Lincoln Junior.",
    "Email: sdfghf@rityrpoed.com, Phone: 4569330953, Name: Stanley",
    "name: luise phone:0546667899 mail:lula@loolie.com",
    "I'd Like to check my order ID",
    "Lucas Clearwood",
    "0923457659",
      "5555555555",
    "54321",
    "5a41d2SQ9",
    "rick125@boosters.com",
    "Book an appointment for me.",
    "please check the status for order ID 67890",
    "check my order",
    "Oh, that's right. It's 12345",
    "Oh, you are correct! It's 67890",
    "Oh! I didn't even notice! the email is w34gkh@gd89sxcgn.com"
]

for input_str in test_inputs:
    print(f"'{input_str}' -> {classify_intent(input_str)}")

def is_human_representative_request(user_input):
    classification = classify_intent(user_input)
    return "personal_details_for_human_representative_request" in classification

# # Test the function
# for input_str in test_inputs:
#     print(f"'{input_str}' -> {is_human_representative_request(input_str)}")


# # Example usage:
# user_input = input("User: ")
# while True:
#     bot_response = chatbot_response(user_input)
#     print("Bot:", bot_response)
#     if "Thank you! Your details have been saved successfully." in bot_response:
#         break
#     user_input = input("User: ")