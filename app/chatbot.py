import re
from app.database import get_connection
from openai import OpenAI
import csv


client = OpenAI(api_key="sk-proj-SWiUtLtJYdMSq1LoOFPtT3BlbkFJI858QX1j6Ps0FlNRXqCU")

# Initialize a state dictionary to store user details
state = {
    "full_name": None,
    "email": None,
    "phone_number": None
}

context_flags = [False, False]


def query_database():
    """This function returns the orders table contents, namely order_id and status fields"""
    conn = get_connection()
    c = conn.cursor()

    # Query the table
    c.execute("SELECT order_id, status FROM orders")
    table1_results = c.fetchall()

    conn.close()
    return table1_results


def validate_and_extract(details_str):
    """This function validates the details for a human representative return request.
    Assuming input format is: <full_name>,<phone_number>,<email>"""
    # split the data and make sure it doesn't contain anything but the data
    details_list = details_str.split(",")
    full_name = details_list[0].strip()
    phone_number = details_list[1].strip()
    email = details_list[2].strip()

    # Regex check on the email, to ensure matching format
    if not re.compile(r"[^@]+@[^@]+\.[^@]+").match(email):
        email = "None"

    return full_name, phone_number, email


# # Function to save contact information to a CSV file
# def save_to_csv(full_name, email, phone_number):
#     # Generate a unique value using the current timestamp
#     unique_value = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
#     filename = f'contact_info_{unique_value}.csv'
#
#     # Check if the file already exists
#     file_exists = os.path.isfile(filename)
#
#     # Open the file in append mode
#     with open(filename, mode='a', newline='') as file:
#         fieldnames = ['Full Name', 'Email', 'Phone Number']
#         writer = csv.DictWriter(file, fieldnames=fieldnames)
#
#         # Write the data row
#         writer.writerow({'Full Name': full_name, 'Email': email, 'Phone Number': phone_number})

def update_state(user_input, state):
    """This function is the part of the bot that handles the input data of the user upon requesting a representative"""

    # The prompt is refined to the requirements of the assignment regarding details
    prompt = f"""User Input: {user_input}\n\n
        Extract the following details from the user's input: full name, email, and phone number. 
        Your response should be formatted as: (<full_name>,<phone_number>,<email>). 
        The format is your only response with no further additions or opening words.
        If any data is missing, write None where it should've been in the format. 
        Do not use 'John Doe' (and the likes of it) to fill a name you were not given. Only use it if it was the name in the User Input.
        If you got two words that look like a name and that's it, assume the user has given you only their full name. 
        If the answer is nothing but numbers, assume the user has given you only their phone number. 
        If the answer doesn't contain spaces and does contain @ assume the user has given you only their email."""

    # I use the same model but in different wiring/roles each time. This model is a little fine-tuned too.
    # Here, the usage of chatgpt is purely as details extractor
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

    # Parsing the details
    details = details.choices[0].message.content
    if "Output" in details:
        # handles the case that the response starts with "Output: (" and ends with ")"
        details = details[9:-1]
    else:
        # the response starts with "(" and ends with ")"
        details = details[1:-1]

    # after the trim, the details should be in this format:  <full_name>,<phone_number>,<email>
    # extract each detail separately
    full_name, phone_number, email = validate_and_extract(details)
    # update the state dictionary accordingly - this dict is needed to remember previous input
    if "None" not in full_name and validate_full_name(full_name):
        state["full_name"] = full_name
    if "None" not in phone_number:
        state["phone_number"] = phone_number
    if "None" not in email:
        state["email"] = email


def validate_full_name(name):
    """Validates that we have received a full name from the user"""
    return len(name.split()) > 1


def generate_details_prompt(state):
    """This function designs the output of the chatbot according to the missing details"""
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
    """This is the main function for the chatbot's response.
    It uses several adaptations of a fine-tuned chatgpt-3.5-turbo model."""

    # Classify the user input to determine the intent
    intent = classify_intent(user_input)

    if "check_order_status" in intent or (
            "only_numbers" in intent and context_flags[0] == True) or (
            "order_id" in intent and context_flags[0] == True) or (
            "phone_number" in intent and context_flags[0] == True) or (
            "order_id" in intent and context_flags[0] == False and context_flags[1] == False):
        # In this case, check the database for order ID or ask the user for order ID



        # fetch results from database and format.
        table1_results = ""
        cnt = 0
        for x, y in query_database():
            cnt += 1
            table1_results += f"{cnt}.(Order ID: {x}, Status: {y}); "

        # The prompt contains the content of the table, so the model really answers purely according to the database
        prompt = f"""
                    User query: {user_input}
                    
                    
                    You must answer according to the table only. Do not answer without providing the status unless the order is not found.
                
                    Instructions for checking an order status:
                    1. **Extracting Order ID:**
                       - If the user provides an order ID, extract it. Add the order ID you've extracted to your response.
                       - If no order ID is provided, kindly ask the user to provide a 5-digit order ID.
                       
                    2. **Validating Order ID:**
                       - Ensure the order ID is exactly 5 digits long. Not shorter, not longer. Spaces and letters are not digits.
                       - If the order ID is not a 5-digit number, notify the user that the order ID must be a 5-digit number.
                    
                    3. **Checking Order ID in the Table:**
                       - If a valid 5-digit order ID is received:
                         - Check the order ID against the provided orders table:
                           \n{table1_results}
                         - If the order ID is found in the table, provide the corresponding order details.
                         - If the order ID is not found in the table, notify the user that the order ID was not found.
                    
                    4. **Handling Missing Order ID:**
                       - If the user does not provide an order ID even after being asked:
                         - Notify the user that an order ID is required to check the order status.
                    
                    Additional rules:
                    - Treat an order ID as non-matching if it partially matches an entry in the table or if the format is incorrect.
                    """

        # mark that chatbot already asked for order ID
        context_flags[0] = True
        context_flags[1] = False

    elif ("human_representative" in intent and "personal_details" not in intent) or "appointment" in intent or "book" in intent:
        # In this case, ask for user details: full name, email and phone number.

        # mark that this is user-detail receiving mode
        context_flags[0] = False
        context_flags[1] = True
        # Let chatgpt choose the way to say this - It was fine-tuned to do that too,
        # this just makes sure since we're already here
        prompt = f"""
        User query: {user_input}\n\nthe user asks for a human representative. You must ask for their phone, email, and full name. 
                        """

    elif "personal_details_for_human_representative_request" in intent or "name" in intent or "email" in intent or (
            "only_numbers" in intent and context_flags[1] == True) or (
            "phone_number" in intent and context_flags[1] == True) or (
            "order_id" in intent and context_flags[1] == True):
        # This part handles anything related to taking the user's details upon requesting a human
        # Extract details from user_input and save them in case any data is missing
        update_state(user_input, state)
        # Generate the chatbot's response in case data is missing
        prompt = generate_details_prompt(state)

        if not prompt:
            # All details are collected, generate CSV and answer accordingly
            with open('user_details.csv', 'w', newline='') as csvfile:
                fieldnames = ['full_name', 'email', 'phone_number']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                # writer.writeheader()
                writer.writerow(state)
            return "Thank you! Your details have been saved successfully."
        else:
            return prompt
    elif "general_policy" in intent:
        prompt = (
            f"User query: {user_input}\n\nIntent: The user asks you to tell them the policy. Answer strictly "
            f"according to the following example. Use the same wording. Do not add to it. Do not leave information "
            f"out. Do not modify it.\n Example:"
            f"\n○ Q: What is the return policy for items purchased at our store?\n"
            f"■ A: You can return most items within 30 days of purchase for a full refund or "
            f"exchange. Items must be in their original condition, with all tags and "
            f"packaging intact. Please bring your receipt or proof of purchase when "
            f"returning items.")
    elif "cannot_return_policy" in intent or "can't_return_policy" in intent or "non_returnables_policy" in intent:
        prompt = (
            f"User query: {user_input}\n\nIntent: The user asks for information about the policy specifically for "
            f"item that can not be returned. Answer strictly according to the following example. Use the same wording. Do not add "
            f"to it. Do not leave information out. Do not modify it.\n Example:"
            f"\n2.○ Q: Are there any items that cannot be returned under this policy?\n"
            f"■ A: Yes, certain items such as clearance merchandise, perishable goods, and "
            f"personal care items are non-returnable. Please check the product description "
            f"or ask a store associate for more details.")
    elif "refund_method_policy" in intent:
        prompt = (
            f"User query: {user_input}\n\nIntent: The user asks for information specifically about the ways they can "
            f"get a refund according to the return policy. Answer strictly according to the following example. Use "
            f"the same wording. Do not add to it. Do not leave information out. Do not modify it.\n Example:"
            f"\n3. ○ Q: How will I receive my refund?\n"
            f"■ A: Refunds will be issued to the original form of payment. If you paid by "
            f"credit card, the refund will be credited to your card. If you paid by cash or "
            f"check, you will receive a cash refund.")


    # In any other case, we use purely the fine-tuned model with a boosting prompt and role.
    else:
        if "policy" in user_input or "Policy" in user_input or "policy." in user_input or "policy!" in user_input or "policy?" in user_input:
            prompt = (f"User query: {user_input}\n\nIntent: The user asks for information about the policy. Answer strictly according to the information you know.")
        elif context_flags[0]:
            prompt = (f"User query: {user_input}\n\nConsider that the user was asked for an order ID in order to check "
                      f"order.")
        elif context_flags[1]:
            prompt = (f"User query: {user_input}\n\nConsider that the user was asked for his personal details: full "
                      f"name, email and phone - because they have requested a human representative.")
        else:
            prompt = f"User query: {user_input}\n\nIntent: other. Please assist the user accordingly."

    response = client.chat.completions.create(
        model="ft:gpt-3.5-turbo-0125:personal:rb:9gE63hlk",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=200,
        n=1,
        stop=None,
        temperature=0.7,
    )

    return response.choices[0].message.content


def classify_intent(user_input):
    """Define the prompt to guide the model in classifying the user input"""
    prompt = f"""
    Classify the intent of the following user input:
    Input: "{user_input}"
    Intent options: [general_policy, non_returnables_policy, can't_return_policy, cannot_return_policy, refund_method_policy, only_numbers, phone_number, only_order_id, only_email, only_name, request_human_representative, personal_details_for_human_representative_request, check_order_status, other]
    Don't pay attention to exclamation marks.
    Do not add other classifications which are not in the Intent options listed. The format for your response is one of these Intent options exactly as written without any additions/modifications.
    Intent:
    
    """

    response = client.chat.completions.create(
        model="ft:gpt-3.5-turbo-0125:personal:rb:9gE63hlk",
        messages=[
            {"role": "system", "content": "You are an intent classification assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=15,
        n=1,
        stop=None,
        temperature=0.5,
    )

    classification = response.choices[0].message.content.replace("Intent: ", "").replace(".", "").replace("`", "")

    if classification.startswith("The intent of the user input is: "):
        classification = classification[34:]
        # Fallback mechanism
    if classification == "other":
        # Check for order ID pattern
        if re.search(r'\b\d{5}\b', user_input):
            classification = "only_order_id"
        # Check for phone number pattern
        elif re.search(r'\b\d{10}\b', user_input) or re.search(r'\b\d{3}[-\.\s]\d{3}[-\.\s]\d{4}\b', user_input):
            classification = "phone_number"

    return classification


# # Example usage:
# user_input = input("User: ")
# while True:
#     bot_response = chatbot_response(user_input)
#     print("Bot:", bot_response)
#     if "Thank you! Your details have been saved successfully." in bot_response:
#         break
#     user_input = input("User: ")
