from wtforms import Form, StringField, validators, PasswordField

class LoginForm(Form):
    username = StringField('Username', [validators.Length(min=4, max=25)])
    password = PasswordField('Password')