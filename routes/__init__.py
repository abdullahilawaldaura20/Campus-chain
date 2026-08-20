def register_blueprints(app):
    from routes.auth import auth_bp
    from routes.products import products_bp
    from routes.messages import messages_bp
    from routes.admin import admin_bp
    from routes.reviews import reviews_bp
    from routes.notifications import notifications_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(reviews_bp)
    app.register_blueprint(notifications_bp)
