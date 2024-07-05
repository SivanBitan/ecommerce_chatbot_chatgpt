from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = '123456'  # Hardcoded secret key for development


    with app.app_context():
        import routes
        from database import create_tables, insert_sample_data
        create_tables()
        insert_sample_data()

    return app
