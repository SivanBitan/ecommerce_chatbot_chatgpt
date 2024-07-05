from flask import request, jsonify, render_template, session
from chatbot import chatbot_response, save_to_csv, extract_order_ids, extract_user_details, check_order_status, handle_service_request
from __init__ import create_app

app = create_app()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/get", methods=["GET"])
def get_bot_response():
    user_text = request.args.get('msg')
    response = chatbot_response(user_text)
    return response


# Route to save contact information
@app.route("/save_contact_info", methods=["POST"])
def save_contact_info():
    full_name = request.form["full_name"]
    email = request.form["email"]
    phone_number = request.form["phone_number"]

    save_to_csv(full_name, email, phone_number)
    return f"\nWe have received the following information: full name: {full_name}, email: {email}, phone number: {phone_number}. a human representative will contact you soon.\n Is there anything else I can do for you?"


if __name__ == "__main__":
    app.run(host='0.0.0.0')
