import unittest
from app.chatbot import chatbot_response, classify_intent, generate_details_prompt, validate_full_name, update_state, \
    validate_and_extract, query_database
from app.database import create_tables, insert_sample_data
from unittest.mock import patch, MagicMock


class TestChatbotResponses(unittest.TestCase):

    def setUp(self):
        create_tables()
        insert_sample_data()

    def assertResponseContains(self, user_input, expected_phrases=None, optional_phrases=None):
        response = chatbot_response(user_input)
        if expected_phrases:
            for phrase in expected_phrases:
                self.assertIn(phrase, response)
        if optional_phrases:
            self.assertTrue(any(phrase in response for phrase in optional_phrases))

    def assertResponseNotContains(self, user_input, expected_phrases):
        response = chatbot_response(user_input)
        for phrase in expected_phrases:
            self.assertNotIn(phrase, response)

    def test_order_status(self):
        """Check order status without saying the word status"""
        user_input = "can you check the order ID 67890"
        optional_phrases = ["processing", "Processing", "processed"]
        self.assertResponseContains(user_input, None, optional_phrases)

    def test_order_status_wording(self):
        """Check order status while saying the word status"""
        user_input = "can you check the status of order ID 12345"
        optional_phrases = ["shipped", "Shipped"]
        self.assertResponseContains(user_input, None, optional_phrases)

    def test_order_status_last_record(self):
        """Check order status with the last unchecked record"""
        user_input = "can you check the status of order ID 54321"
        expected_phrases = ["elivered"]
        self.assertResponseContains(user_input, expected_phrases)

    def test_non_existing_order_id(self):
        """Check order status for non-existing ID"""
        user_input = "check order ID 99999"
        expected_phrases = ["elivered", "hipped", "ocessing", "placed"]
        self.assertResponseNotContains(user_input, expected_phrases)

    def test_invalid_order_id(self):
        """Check order status for invalid ID"""
        user_input = "check order 456"
        expected_phrases = ["elivered", "hipped", "rocessing", "placed"]
        self.assertResponseNotContains(user_input, expected_phrases)

    def test_request_human(self):
        """Ensure the form response is initiated upon customer service request"""
        user_input = "Can someone human answer me?"
        expected_phrases = ["phone number", "email", "full name"]
        self.assertResponseContains(user_input, expected_phrases)

    def test_request_human_personal_details(self):
        """Ensure the form response prompts for missing details"""
        user_input = "Email: sdfghf@rityrpoed.com, Phone: 4569330953, Name: Stanley"
        expected_phrases = ["Please provide your full name."]
        self.assertResponseContains(user_input, expected_phrases)

    def test_policy_general(self):
        """Check the fine-tuning for the policy"""
        user_input = "What is the return policy for items purchased at our store?"
        expected_phrases = [
            "You can return most items within 30 days of purchase for a full refund or exchange. Items must be in their original condition, with all tags and packaging intact. Please bring your receipt or proof of purchase when returning items."
        ]
        # optional_phrases = ["receipt", "proof", "Receipt", "receipts", "Receipts", "Proof"]
        self.assertResponseContains(user_input, expected_phrases)

    def test_policy_unreturnables(self):
        """Check the fine-tuning for the policy"""
        user_input = "Are there any items that cannot be returned under this policy?"
        expected_phrases = [
        "Yes, certain items such as clearance merchandise, perishable goods, and personal care items are non-returnable. Please check the product description or ask a store associate for more details."
        ]
        # optional_phrases = ["receipt", "proof", "Receipt", "receipts", "Receipts", "Proof"]
        self.assertResponseContains(user_input, expected_phrases)


    def test_policy_refund_ways(self):
        """Check the fine-tuning for the policy"""
        user_input = "How will I receive my refund?"
        expected_phrases = [
        "Refunds will be issued to the original form of payment. If you paid by credit card, the refund will be credited to your card. If you paid by cash or check, you will receive a cash refund."]
        # optional_phrases = ["receipt", "proof", "Receipt", "receipts", "Receipts", "Proof"]
        self.assertResponseContains(user_input, expected_phrases)


    def test_policy_general_different_wording(self):
        """Check the fine-tuning for the policy"""
        user_input = "Can you tell me what is the policy for returns in this store?"
        expected_phrases = [
            "You can return most items within 30 days of purchase for a full refund or exchange. Items must be in their original condition, with all tags and packaging intact. Please bring your receipt or proof of purchase when returning items."
        ]
        # optional_phrases = ["receipt", "proof", "Receipt", "receipts", "Receipts", "Proof"]
        self.assertResponseContains(user_input, expected_phrases)

    def test_policy_unreturnables_different_wording(self):
        """Check the fine-tuning for the policy"""
        user_input = "Is it true that we can't return some of the items as per return policy?"
        expected_phrases = [
        "certain items such as clearance merchandise, perishable goods, and personal care items are non-returnable. Please check the product description or ask a store associate for more details."
        ]
        # optional_phrases = ["receipt", "proof", "Receipt", "receipts", "Receipts", "Proof"]
        self.assertResponseContains(user_input, expected_phrases)

    def test_policy_unreturnables_different_wording_2(self):
        """Check the fine-tuning for the policy"""
        user_input = "Are there any items which are non-returnables?"
        expected_phrases = [
        "certain items such as clearance merchandise, perishable goods, and personal care items are non-returnable. Please check the product description or ask a store associate for more details."
        ]
        # optional_phrases = ["receipt", "proof", "Receipt", "receipts", "Receipts", "Proof"]
        self.assertResponseContains(user_input, expected_phrases)

    def test_policy_refund_ways_different_wording(self):
        """Check the fine-tuning for the policy"""
        user_input = "Please provide me details about the way I can receive a refund."
        expected_phrases = [
        "Refunds will be issued to the original form of payment. If you paid by credit card, the refund will be credited to your card. If you paid by cash or check, you will receive a cash refund."]
        # optional_phrases = ["receipt", "proof", "Receipt", "receipts", "Receipts", "Proof"]
        self.assertResponseContains(user_input, expected_phrases)



class TestChatbot(unittest.TestCase):

    def setUp(self):
        self.initial_state = {
            "full_name": None,
            "email": None,
            "phone_number": None
        }

    @patch('app.database.get_connection')
    def test_query_database(self, mock_get_connection):
        # Mocking database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_connection.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [('12345', 'Shipped'), ('67890', 'Processing'), ('54321', 'Delivered')]

        result = query_database()
        self.assertEqual(result, [('12345', 'Shipped'), ('67890', 'Processing'), ('54321', 'Delivered')])

    def test_validate_and_extract(self):
        valid_input = "John Doe, 1234567890, johndoe@example.com"
        invalid_input = "John, 1234567890, johndoe"

        valid_result = validate_and_extract(valid_input)
        invalid_result = validate_and_extract(invalid_input)

        self.assertEqual(valid_result, ('John Doe', '1234567890', 'johndoe@example.com'))
        self.assertEqual(invalid_result, ('John', '1234567890', 'None'))

    def test_update_state(self):
        user_input = "Here it is: John Doe, 1234567890, johndoe@example.com"
        update_state(user_input, self.initial_state)

        self.assertEqual(self.initial_state["full_name"], "John Doe")
        self.assertEqual(self.initial_state["phone_number"], "1234567890")
        self.assertEqual(self.initial_state["email"], "johndoe@example.com")

    def test_validate_full_name(self):
        valid_name = "John Doe"
        invalid_name = "John"

        self.assertTrue(validate_full_name(valid_name))
        self.assertFalse(validate_full_name(invalid_name))

    def test_generate_details_prompt(self):
        state_missing_name = {"full_name": None, "email": "test@exam.ple_.com", "phone_number": "054-4567890"}
        state_uncapitalized_letters_name = {"full_name": "jinn monroe", "email": "sdfghf@rityrpoed.com",
                                            "phone_number": "123-4567890"}
        state_missing_email = {"full_name": "Yosi Cohen", "email": None, "phone_number": "123-456-7890"}
        state_missing_phone = {"full_name": "John Doe", "email": "test123@example_n.ac.il", "phone_number": None}
        complete_state = {"full_name": "John Doe", "email": "rick125@boosters.com", "phone_number": "+972-34567890"}

        self.assertEqual(generate_details_prompt(state_missing_name), "Please provide your full name.")
        self.assertEqual(generate_details_prompt(state_missing_email), "Please provide your email address.")
        self.assertEqual(generate_details_prompt(state_missing_phone), "Please provide your phone number.")
        self.assertIsNone(generate_details_prompt(complete_state))
        self.assertIsNone(generate_details_prompt(state_uncapitalized_letters_name))

    @patch('app.database.get_connection')
    @patch('openai.OpenAI')
    def test_chatbot_response(self, mock_openai, mock_get_connection):
        # Mocking intent classification
        mock_openai.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Intent: check_order_status"))])

        user_input = "What is the status of my order?"
        result = chatbot_response(user_input)

        self.assertIn("rder ID", result)


class TestIntentClassification(unittest.TestCase):

    def setUp(self):
        # This method will run before each test
        self.test_cases = [
            ("My phone is 1234873246, my email is sdf@dsfg.com and my name is Martha Peskety.",
             ["personal_details_for_human_representative_request", "Personal_details_for_human_representative_request", "only_email", "Only_email", "only_numbers",
              "Only_numbers", "phone_number", "Phone_number", "only_name", "Only_name"]),
            ("My phone is 5555555555",
             ["phone_number", "Phone_number", "only_numbers", "Only_numbers", "only_order_id",
              "Only_order_id"]),
            ("my email is vxciov@tryuitr.com and my name is Lincoln Junior.",
             ["personal_details",
              "Personal_details", "only_email", "Only_email",
              "only_name", "Only_name"]),
            ("Email: sdfghf@rityrpoed.com, Phone: 4569330953, Name: Stanley",
             ["personal_details_for_human_representative_request",
              "Personal_details_for_human_representative_request", "only_email", "Only_email",
              "only_numbers", "Only_numbers", "phone_number", "Phone_number", "only_name",
              "Only_name"]),
            ("name: luise phone:0546667899 mail:lula@loolie.com", ["personal_details_for_human_representative_request",
                                                                   "Personal_details_for_human_representative_request",
                                                                   "only_email", "Only_email", "only_numbers",
                                                                   "Only_numbers", "phone_number",
                                                                   "Phone_number", "only_name",
                                                                   "Only_name"]),
            ("I'd Like to check my order ID",
             ["only_order_id", "Only_order_id", "check_order_status", "Check_order_status"]),
            ("Lucas Clearwood", ["only_name", "Only_name"]),
            ("0923457659", ["only_phone_number", "Only_phone_number", "phone_number", "Phone_number", "only_numbers", "Only_numbers"]),
            ("5555555555", ["phone_number", "Phone_number", "only_numbers", "Only_numbers"]),
            ("54321", ["check_order_status", "Check_order_status", "only_order_id", "Only_order_id",
                       "only_numbers", "Only_numbers"]),
            ("054-6612726",
             ["phone_number", "Phone_number", "only_order_id", "Only_order_id", "only_numbers",
              "Only_numbers"]),
            ("5a41d2SQ9",
             ['only_numbers', 'Only_numbers', "check_order_status", "Check_order_status", "other", "only_order_id", "Only_order_id",
              "Other"]),
            ("rick125@boosters.com", ["only_email", "Intent: only_email"]),
            ("Book an appointment for me.",
             ["request_human_representative", "Request_human_representative", "Book_appointment",
              "book_appointment", "other", "Other", "Book an appointment", "book an appointment",
              "Book appointment", "book appointment"]),
            ("I'd like to speak to a representative.",
             ["request_human_representative", "Request_human_representative", "Book_appointment",
              "book_appointment", "other", "Other", "Book an appointment", "book an appointment",
              "Book appointment", "book appointment"]),
            ("Can I speak to someone?",
             ["request_human_representative", "Request_human_representative", "Book_appointment",
              "book_appointment", "other", "Other", "Book an appointment", "book an appointment",
              "Book appointment", "book appointment"]),
            ("please check the status for order ID 67890",
             ["check_order_status", "Check_order_status", "only_order_id", "Only_order_id",
              "Only_numbers", "only_numbers"]),
            ("check my order", ["check_order_status", "Check_order_status"]),
            ("Oh, that's right. It's 12345",
             ["check_order_status", "Check_order_status", "only_order_id", "Only_order_id",
              "Only_numbers", "only_numbers"]),
            ("Oh, you are correct! It's 67890",
             ["check_order_status", "Check_order_status", "only_order_id", "Only_order_id",
              "only_numbers", "Only_numbers"]),
            ("Oh! I didn't even notice! the email is w34gkh@gd89sxcgn.com", ["Only_email", "only_email"]),
            ("032-47503",
             ["Phone_number", "phone_number", "only_order_id", "Only_order_id", "only_numbers",
              "Only_numbers"]),
            ("I see. My order ID is +972-83-23456",
             ["Check_order_status", "check_order_status", "Only_order_id", "only_order_id",
              "only_numbers", "Only_numbers"]),
            ("Oh sure, now that I look again it's probably 67890",
             ["Check_order_status", "check_order_status", "Only_order_id", "only_order_id",
              "only_numbers", "Only_numbers"]),
            ("What is the status of my order?", ["check_order_status","Check_order_status"]),
            ("Can someone human answer me?",
             ["request_human_representative", "Request_human_representative", "Book an appointment", "book an "
                                                                                                     "appointment",
              "Book appointment", "book appointment"
              "book_appointment","Book_appointment", "other", "Other"])
        ]

    def test_classify_intent(self):
        for user_input, expected_intents in self.test_cases:
            with self.subTest(user_input=user_input, expected_intents=expected_intents):
                # self.assertIn(classify_intent(user_input), expected_intents)

                self.assertTrue(any(phrase in classify_intent(user_input) for phrase in expected_intents))


if __name__ == "__main__":
    unittest.main()
