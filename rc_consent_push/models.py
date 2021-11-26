from rc_consent_push import db

class Project(db.Model):
    # Primary Key
    pid = db.Column(db.Integer, primary_key=True,nullable=False, autoincrement=False)

    # Other attributes
    project_title = db.Column(db.String(256))
    stu = db.Column(db.String(128))
    api_token = db.Column(db.String(128))
    is_longitudinal = db.Column(db.Integer)
    has_repeating_instruments_or_events = db.Column(db.Integer)
    surveys_enabled = db.Column(db.Integer)

    # Relationships -- you have to use back_populates and not backref so you can have asymmetric cascades
    instruments = db.relationship('Instrument', back_populates='project', cascade = ['all', 'delete', 'delete-orphan'], order_by = 'Instrument.instrument_label')

class Instrument(db.Model):

    # Primary Keys (Composite)
    pid = db.Column(db.Integer, nullable=False )
    instrument_name = db.Column(db.String(128), nullable=False)

    # Other attributes
    instrument_label = db.Column(db.String(256))
    consent_date_var = db.Column(db.String(128))
    case_number_var = db.Column(db.String(128))

    # Constraints
    __table_args__ = (
        db.PrimaryKeyConstraint('pid','instrument_name'),
        db.ForeignKeyConstraint(['pid'], ['project.pid']),
    )

    # Relationships -- you have to use back_populates and not backref so you can have asymmetric cascades
    project = db.relationship('Project', back_populates = 'instruments' )



