from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, PasswordField, SelectField, HiddenField
from wtforms.validators import DataRequired, NumberRange, Length, ValidationError
from models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    role = SelectField('Role', choices=[('cashier','Cashier'), ('admin','Admin')], default='cashier')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already taken.')

class ProductForm(FlaskForm):
    code = StringField('Product Code', validators=[DataRequired(), Length(max=20)])
    name = StringField('Product Name', validators=[DataRequired(), Length(max=100)])
    price = FloatField('Price (KES)', validators=[DataRequired(), NumberRange(min=0)])
    category = StringField('Category', validators=[DataRequired(), Length(max=50)])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=0)])

class AddToCartForm(FlaskForm):
    code = HiddenField('Code', validators=[DataRequired()])
    quantity = IntegerField('Qty', validators=[DataRequired(), NumberRange(min=1)])