from rc_consent_push import db

class Project(db.Model):
    pid = db.Column(db.Integer, primary_key=True,nullable=False, autoincrement=False)

    # Other attributes
    stu = db.Column(db.String(128))
    api_token = db.Column(db.String(128))

