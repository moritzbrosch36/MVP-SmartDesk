from source.db.database import get_model, db


def get_or_create(name: str):
    User = get_model("User")

    user = User.query.filter_by(name=name).first()

    if not user:
        user = User(name=name)
        db.session.add(user)
        db.session.commit()

    return user
