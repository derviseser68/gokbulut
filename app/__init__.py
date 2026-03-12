from flask import Flask, redirect, url_for
from supabase import create_client, Client
from config import Config

supabase: Client = None

def create_app():
    global supabase
    app = Flask(__name__)
    app.config.from_object(Config)

    supabase = create_client(app.config['SUPABASE_URL'], app.config['SUPABASE_KEY'])

    # Auth modülünü ve diğerlerini kaydediyoruz
    from app.auth.routes import auth_bp
    from app.admin.routes import admin_bp
    from app.customer.routes import customer_bp
    from app.courier.routes import courier_bp

    app.register_blueprint(auth_bp) # Ön eki yok, direkt /login
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(customer_bp, url_prefix='/customer')
    app.register_blueprint(courier_bp, url_prefix='/courier')

    # Ana sayfaya girenleri direkt login sayfasına yönlendir
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    return app