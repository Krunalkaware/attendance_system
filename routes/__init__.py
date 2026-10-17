def register_blueprints(app):
    from .auth import bp as auth
    from .dashboard import bp as dashboard
    from .students import bp as students
    from .attendance import bp as attendance
    from .reports import bp as reports
    for b in (auth, dashboard, students, attendance, reports):
        app.register_blueprint(b)
