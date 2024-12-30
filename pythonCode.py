from flask import Flask, jsonify, request, send_from_directory
import os
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from werkzeug.security import generate_password_hash, check_password_hash



UPLOAD_FOLDER = 'uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


ADMIN_PASSWORD = ""

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key' 
db = SQLAlchemy(app)
CORS(app, resources={r"/*": {"origins": "*"}})
migrate = Migrate(app, db)
jwt = JWTManager(app)

ADMIN_PASSWORD_HASH = generate_password_hash("froodgah13881388", method='pbkdf2:sha256')


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    password = data.get('password')
    if check_password_hash(ADMIN_PASSWORD_HASH, password):

        access_token = create_access_token(identity='admin')  # ایجاد توکن JWT
        return jsonify({'message': 'Login Was Successful', 'status': 'success', 'access_token': access_token}), 200
    else:
        # ورود ناموفق
        return jsonify({'message': 'Login Was Failed', 'status': 'failed'}), 400

# مسیر برای تایید دسترسی
@app.route('/admin/protected', methods=['GET'])
@jwt_required()  # فقط کاربرانی که توکن دارند می‌توانند به این مسیر دسترسی پیدا کنند
def protected():
    return jsonify(message="این مسیر فقط برای کاربران لاگین شده قابل دسترسی است")

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(100), nullable=False)
    size = db.Column(db.String(200), nullable=False)
    size_availability = db.Column(db.JSON, nullable=True)  
    stock = db.Column(db.Integer, nullable=True, default=0)
    color = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(50), nullable=False)
    image = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)

    def __init__(self, name, type, size, size_availability, stock, color, gender, image, price):
        self.name = name
        self.type = type
        self.size = size
        self.size_availability = size_availability  
        self.stock = stock
        self.color = color
        self.gender = gender
        self.image = image
        self.price = price

# مسیر برای دسترسی به تصاویر
@app.route('/uploads/<filename>')
@jwt_required()
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# اضافه کردن محصول جدید
@app.route('/api/products', methods=['POST'])
@jwt_required()
def add_product():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file part'}), 200
    image_file = request.files['image']
    if image_file and allowed_file(image_file.filename):
        filename = secure_filename(image_file.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        image_file.save(image_path)
    else:
        return jsonify({'error': 'Invalid image file'}), 200
    
    data = request.form.to_dict()
    size_list = data['size'].split(",")
    size_stock = list(map(int, data['stock'].split(",")))

    size_availability = {size: stock for size, stock in zip(size_list, size_stock)}

    new_product = Product(
        name=data['name'],
        type=data['type'],
        size=",".join(size_list),
        size_availability=size_availability,  # ذخیره موجودی سایزها به صورت JSON
        stock=sum(size_stock),  # ذخیره جمع موجودی کلی
        color=data['color'],
        gender=data['gender'],
        image=filename,
        price=float(data['price'])
    )

    db.session.add(new_product)
    db.session.commit()
    return jsonify({
        'id': new_product.id,
        'name': new_product.name,
        'type': new_product.type,
        'size': new_product.size,
        'size_availability': new_product.size_availability,
        'color': new_product.color,
        'gender': new_product.gender,
        'image': new_product.image,
        'price': new_product.price
    }), 201

# دریافت محصولات
@app.route('/api/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    product_list = [
        {
            'id': product.id,
            'name': product.name,
            'type': product.type,
            'size': product.size,
            'size_availability': product.size_availability,
            'stock': product.stock,  # نمایش موجودی کلی
            'color': product.color,
            'gender': product.gender,
            'image': product.image,
            'price': product.price
        }
        for product in products
    ]
    return jsonify(product_list)

# حذف محصول با شناسه
@app.route('/api/products/<int:id>', methods=['DELETE'])
@jwt_required()
def delete_product(id):
    product = Product.query.get(id)
    if product:
        db.session.delete(product)
        db.session.commit()
        return jsonify({'message': 'Product deleted successfully'}), 200
    else:
        return jsonify({'error': 'Product not found'}), 404
    

@app.route('/api/products/updateSize/<int:id>', methods=['PUT'])
@jwt_required()
def update_size(id):
    product = Product.query.get(id)

    data = request.get_json()


    size = data.get('size')
    stock = int(data.get('stock'))

    size_to_add = product.size_availability
    size_to_add[size] = stock

    new_size_stock = product.size_availability

    try:

        product.size_availability = new_size_stock
        db.session.commit()
        print(product.size_availability)
        print(size_to_add)
        return jsonify({'message':'dada has sended', 'status':'SENDED'}), 200
    
    except:

        return jsonify({'message':'data has not sended', 'status':'NOT_SENDED'}), 400

    


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    app.run(debug=True, threaded=False)
