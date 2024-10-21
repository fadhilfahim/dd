from flask import Flask, request, render_template
import pandas as pd
import random
from flask_sqlalchemy import SQLAlchemy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# Load files
trending_products = pd.read_csv("models/trending_products.csv")
train_data = pd.read_csv("models/clean_data.csv")

# Database configuration
app.secret_key = "alskdjfwoeieiurlskdjfslkdjf"
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://root:@localhost/ecom"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define your model class for the 'signup' table
class Signup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Define your model class for the 'signin' table
class Signin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

# Recommendations functions
def truncate(text, length):
    if len(text) > length:
        return text[:length] + "..."
    else:
        return text

def content_based_recommendations(train_data, item_name, top_n=10):
    if item_name not in train_data['Name'].values:
        print(f"Item '{item_name}' not found in the training data.")
        return pd.DataFrame()

    tfidf_vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix_content = tfidf_vectorizer.fit_transform(train_data['Tags'])
    cosine_similarities_content = cosine_similarity(tfidf_matrix_content, tfidf_matrix_content)

    item_index = train_data[train_data['Name'] == item_name].index[0]
    similar_items = list(enumerate(cosine_similarities_content[item_index]))
    similar_items = sorted(similar_items, key=lambda x: x[1], reverse=True)
    top_similar_items = similar_items[1:top_n+1]
    recommended_item_indices = [x[0] for x in top_similar_items]
    recommended_items_details = train_data.iloc[recommended_item_indices][['Name', 'ReviewCount', 'Brand', 'ImageURL', 'Rating']]

    return recommended_items_details

def get_content_based_recommendations(item_name='Sample Item'):
    return content_based_recommendations(train_data, item_name)

# Routes
random_image_urls = [
    "static/img/img_1.png",
    "static/img/img_2.jpeg",
    "static/img/img_3.jpg",
    "static/img/img_4.avif",
    "static/img/img_5.avif",
    "static/img/img_6.avif",
    "static/img/img_7.avif",
    "static/img/img_8.avif",
    "static/img/img_9.avif",
    "static/img/img_10.avif",
    "static/img/img_11.avif",
    "static/img/img_12.avif",
    "static/img/img_13.avif",
    "static/img/img_14.jpg",
    "static/img/img_15.jpg",
    "static/img/img_16.avif",
    "static/img/img_17.avif",
    "static/img/img_18.avif",
    "static/img/img_19.avif",
    "static/img/img_20.avif"
]

@app.route("/")
def index():
    # Ensure the number of images selected equals the number of trending products
    random_product_image_urls = random.sample(random_image_urls, len(trending_products.head(10)))

    # Prices 
    price = [5750, 340, 3400, 2430, 4310, 600, 765, 230, 120, 1000, 850, 940, 1700]
    random_prices = random.sample(price, 10)  # Select 8 unique prices
    
    # Render the template with 8 trending products, unique images, and prices
    return render_template('index.html',
                           trending_products=trending_products.head(10),
                           truncate=truncate,
                           random_product_image_urls=random_product_image_urls,
                           random_price=random_prices)


@app.route('/main')
def main():
    content_based_rec = get_content_based_recommendations()
    return render_template('main.html', content_based_rec=content_based_rec)

@app.route("/index")
def indexredirect():
    random_product_image_urls = [random.choice(random_image_urls) for _ in range(len(trending_products))]
    price = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]
    return render_template('index.html', trending_products=trending_products.head(15), truncate=truncate,
                           random_product_image_urls=random_product_image_urls,
                           random_price=random.choice(price))

@app.route("/signup", methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Add signup data to the database
        new_signup = Signup(username=username, email=email, password=password)
        db.session.add(new_signup)
        db.session.commit()

        # Generate random images and prices
        random_product_image_urls = [random.choice(random_image_urls) for _ in range(len(trending_products))]
        price = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]

        return render_template('index.html', trending_products=trending_products.head(8), truncate=truncate,
                               random_product_image_urls=random_product_image_urls, 
                               random_price=random.choice(price),
                               signup_message='User signed up successfully!')

@app.route('/signin', methods=['POST', 'GET'])
def signin():
    if request.method == 'POST':
        username = request.form['signinUsername']
        password = request.form['signinPassword']

        # Add sign-in data to the database
        new_signin = Signin(username=username, password=password)
        db.session.add(new_signin)
        db.session.commit()

        # Generate random images and prices
        random_product_image_urls = [random.choice(random_image_urls) for _ in range(len(trending_products))]
        price = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]

        return render_template('index.html', trending_products=trending_products.head(8), truncate=truncate,
                               random_product_image_urls=random_product_image_urls, 
                               random_price=random.choice(price),
                               signin_message='User signed in successfully!')

@app.route("/recommendations", methods=['POST', 'GET'])
def recommendations():
    if request.method == 'POST':
        prod = request.form.get('prod', '').strip()  # Get product and handle empty input
        nbr_str = request.form.get('nbr', '10').strip()  # Get the number of products, default to 1

        # Handle empty or invalid number input
        try:
            nbr = int(nbr_str) if nbr_str else 10
        except ValueError:
            nbr = 10  # Default to 1 if conversion fails

        # If product is empty, show a message
        if not prod:
            message = "Please enter a product name to get recommendations."
            return render_template('main.html', message=message, content_based_rec=None,
                                   random_product_image_urls=[], random_price=None)

        # Get content-based recommendations
        content_based_rec = content_based_recommendations(train_data, prod, top_n=nbr)

        # Generate random images and prices
        random_product_image_urls = [random.choice(random_image_urls) for _ in range(len(content_based_rec))]
        price = [40, 50, 60, 70, 100, 122, 106, 50, 30, 50]
        
        # Handle no recommendations scenario
        if content_based_rec.empty:
            message = f"No recommendations available for '{prod}'."
            return render_template('main.html', message=message, content_based_rec=None,
                                   random_product_image_urls=random_product_image_urls,
                                   random_price=random.choice(price))
        else:
            return render_template('main.html', content_based_rec=content_based_rec, truncate=truncate,
                                   random_product_image_urls=random_product_image_urls,
                                   random_price=random.choice(price))

if __name__ == '__main__':
    app.run(debug=True)
