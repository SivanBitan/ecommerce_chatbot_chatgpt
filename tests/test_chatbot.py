import unittest
from app.chatbot import chatbot_response
from app.database import create_tables, insert_sample_data


def test_order_status():
    """check order status without saying the word status"""
    response = chatbot_response("can you check the order ID 67890")
    expected_response = "Order 67890: processing"
    print("\n_____________test_order_status_____________")
    print(response)
    print(expected_response)

def test_order_status_wording():
    """check order status while saying the word status"""
    response = chatbot_response("can you check the status of order ID 12345")
    expected_response = "Order 12345: Shipped"
    print("\n_____________test_order_status_wording_____________")
    print(response)
    print(expected_response)

def test_order_status_last_record():
    """check order status with the last unchecked record"""
    response = chatbot_response("can you check the status of order ID 54321")
    expected_response = "Order 54321: Delivered"
    print("\n_____________test_order_status_last_record_____________")
    print(response)
    print(expected_response)

def test_non_existing_order_id():
    """check order status for non-existing ID"""
    response = chatbot_response("check order ID 99999")
    expected_response = "Order 99999 not found."
    print("\n_____________test_non_existing_order_id_____________")
    print(response)
    print(expected_response)

def test_invalid_order_id():
    """check order status for non-existing ID"""
    response = chatbot_response("check order ID 456")
    expected_response = "Order 456 not found."
    print("\n_____________test_invalid_order_id_____________")
    print(response)
    print(expected_response)


def test_request_human():
    """making sure the form response has been initiated upon customer service request"""
    user_input = "Can someone human answer me?"
    response = chatbot_response(user_input)
    expected_response = "Sure. I'll take your details so that someone can reach out to you. Please provide your contact details below."
    print("\n_____________test_request_human_____________")
    print(response)
    print(expected_response)

def test_request_human_personal_details():
    """making sure the form response has been initiated upon customer service request"""
    user_input = "Email: sdfghf@rityrpoed.com, Phone: 4569330953, Name: Stanley"
    response = chatbot_response(user_input)
    expected_response = "?"
    print("\n_____________test_request_human_personal_details_____________")
    print(response)
    print(expected_response)

def test_policy():
    """Checking the fine-tuning for the policy"""
    user_input = "What is the return policy for items purchased at our store?"
    response = chatbot_response(user_input)
    expected_response = "You can return most items within 30 days of purchase for a full refund or exchange. Items must be in their original condition, with all tags and packaging intact. Please bring your receipt or proof of purchase when returning items."
    print("\n_____________test_policy_____________")
    print(response)
    print(expected_response)

create_tables()
insert_sample_data()
# Run the tests
test_order_status()
test_order_status_wording()
test_order_status_last_record()
test_non_existing_order_id()
test_invalid_order_id()
test_request_human()
test_request_human_personal_details()
test_policy()
