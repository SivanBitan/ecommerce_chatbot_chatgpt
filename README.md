# Ecommerce Chatbot Project

This project demonstrates a simple chatbot integrated with a database to handle order status checks and service requests.

## Features

- Check the status of an order by providing the order ID.
- Request human assistance by providing full name, email address, and phone number.
- Get information about the store's return policy by asking about it.
- Stores and retrieves orders data from a SQLite database.

## Setup

### Requirements

- Python 3.10
- Flask

### How to run
1. Run the application:
   ```bash
   python app/routes.py
   ```
2. Open your browser and go to http://localhost:5000.
3. Interact with the chatbot by typing messages in the input box.

   
### Running with Docker

1. Build and run the Docker container:
   ```bash
   docker-compose up --build
   ```
2. Open your browser and go to http://localhost:5000.
3. Interact with the chatbot by typing messages in the input box.


### Testing
Unit-testing is avalable for the chatbot and its database in files **test-chatbot.py** and **test-database.py** under folder tests.

### License
This project is licensed under the MIT License.
