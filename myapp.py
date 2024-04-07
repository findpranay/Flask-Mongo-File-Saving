# from flask import Flask, render_template, request, redirect, url_for, send_file
# from flask_pymongo import PyMongo
# import base64
# import gridfs
# from bson import ObjectId

# app = Flask(__name__)
# app.config['MONGO_URI'] = 'mongodb://localhost:27017/filesuploadcopy'
# mongo = PyMongo(app)

# @app.route('/')
# def index():
#     return render_template('index.html')


# @app.route('/submit', methods=['POST'])
# def submit():
#     selection = request.form['selection']

#     if selection == 'name':
#         name = request.form['name']
#         names_collection = mongo.db.names
#         names_collection.insert_one({'name': name})
#         return redirect(url_for('show_names'))

#     elif selection == 'image':
#         image_file = request.files['image']
#         if not image_file or not image_file.filename:
#             return render_template('error.html', error="No image selected.")
#         image_data = image_file.read()
#         images_collection = mongo.db.images
#         images_collection.insert_one({'image': image_data})
#         return redirect(url_for('show_images'))

#     elif selection == 'video':
#         try:
#             video_file = request.files['video']
#             if not video_file or not video_file.filename:
#                 return render_template('error.html', error="No video selected.")
#             video_data = video_file.read()

#             fs = gridfs.GridFS(mongo.db)
#             video_id = fs.put(video_data, filename=video_file.filename)

#             videos_collection = mongo.db.videos
#             videos_collection.insert_one({'video_id': video_id, 'metadata': {'filename': video_file.filename}})

#             return redirect(url_for('show_videos'))
#         except Exception as e:
#             print(f"Error: {e}")
#             return render_template('error.html', error="An error occurred while uploading the video.")

#     # Handle invalid selection (optional)
#     return redirect(url_for('index'))  # Or display an error message


# @app.route('/names')
# def show_names():
#     names_collection = mongo.db.names
#     names = [name['name'] for name in names_collection.find()]
#     return render_template('names.html', names=names)


# @app.route('/images')
# def show_images():
#     try:
#         images_collection = mongo.db.images
#         images = []
#         for image in images_collection.find():
#             if 'image' in image:
#                 image_data = image['image']
#                 base64_data = base64.b64encode(image_data).decode('utf-8')
#                 images.append(base64_data)
#         return render_template('image.html', images=images)
#     except Exception as e:
#         print(f"Error: {e}")
#         return render_template('image.html', error="An error occurred while fetching images.")


# @app.route('/videos')
# def show_videos():
#     try:
#         fs = gridfs.GridFS(mongo.db)
#         videos_collection = mongo.db.videos
#         videos = []
#         for video in videos_collection.find():
#             if 'video_id' in video:
#                 video_id = video['video_id']
#                 video_data = fs.get(video_id)
#                 videos.append({
#                     'filename': video['metadata']['filename'],
#                     'video_id': str(video_data._id)  # Convert ObjectId to string
#                 })

#         return render_template('videos.html', videos=videos)
#     except Exception as e:
#         print(f"Error: {e}")
#         return render_template('error.html', error="An error occurred while fetching videos.")


# @app.route('/stream_video/<video_id>')
# def stream_video(video_id):
#     try:
#         fs = gridfs.GridFS(mongo.db)
#         video_data = fs.get(ObjectId(video_id))
#         return send_file(video_data, mimetype='video/mp4')
#     except Exception as e:
#         print(f"Error: {e}")
#         return "Video not found", 404


# if __name__ == '__main__':
#     app.run(debug=True)


from flask import Flask, render_template, request, redirect, url_for, send_file, session
from flask_pymongo import PyMongo
import base64
import gridfs
from bson import ObjectId
import bcrypt

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set your secret key for session management
app.config['MONGO_URI'] = 'mongodb://localhost:27017/filesuploadcopy'
mongo = PyMongo(app)

@app.route('/home')
def index():
    if 'username' in session:
        return render_template('index.html')
    return redirect(url_for('login'))

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        users = mongo.db.users
        login_user = users.find_one({'name': request.form['username']})
        if login_user and bcrypt.checkpw(request.form['pass'].encode('utf-8'), login_user['password']):
            session['username'] = request.form['username']
            session['user_id'] = str(login_user['_id'])  # Store user ID in session
            return redirect(url_for('index'))
        return "Invalid credentials"
    return render_template("login.html")

@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        users = mongo.db.users
        existing_user = users.find_one({'name': request.form['username']})
        if existing_user is None:
            hashpass = bcrypt.hashpw(request.form['pass'].encode('utf-8'), bcrypt.gensalt())
            users.insert_one({'name': request.form['username'], 'password': hashpass})
            return redirect(url_for('index'))
    return render_template("register.html")



@app.route('/submit', methods=['POST'])
def submit():
    selection = request.form['selection']
    user_id = session.get('user_id')

    if user_id is None:
        return redirect(url_for('login'))  # Redirect if user is not logged in

    if selection == 'name':
        name = request.form['name']
        names_collection = mongo.db.names
        names_collection.insert_one({'name': name, 'user_id': user_id})  # Store user ID with the name
        return redirect(url_for('show_names'))

    elif selection == 'image':
        image_file = request.files['image']
        if not image_file or not image_file.filename:
            return render_template('error.html', error="No image selected.")
        image_data = image_file.read()
        images_collection = mongo.db.images
        images_collection.insert_one({'image': image_data, 'user_id': user_id})  # Store user ID with the image
        return redirect(url_for('show_images'))

    elif selection == 'video':
        try:
            video_file = request.files['video']
            if not video_file or not video_file.filename:
                return render_template('error.html', error="No video selected.")
            video_data = video_file.read()

            fs = gridfs.GridFS(mongo.db)
            video_id = fs.put(video_data, filename=video_file.filename)

            videos_collection = mongo.db.videos
            videos_collection.insert_one({'video_id': video_id, 'metadata': {'filename': video_file.filename}, 'user_id': user_id})  # Store user ID with the video

            return redirect(url_for('show_videos'))
        except Exception as e:
            print(f"Error: {e}")
            return render_template('error.html', error="An error occurred while uploading the video.")

    # Handle invalid selection (optional)
    return redirect(url_for('index'))  # Or display an error message


# @app.route('/names')
# def show_names():
#     user_id = session.get('user_id')

#     if user_id is None:
#         return redirect(url_for('login'))  # Redirect if user is not logged in

#     names_collection = mongo.db.names
#     names = [name['name'] for name in names_collection.find({'user_id': user_id})]  # Only fetch names associated with the user
#     return render_template('names.html', names=names)


@app.route('/names')
def show_names():
    user_id = session.get('user_id')

    if user_id is None:
        return redirect(url_for('login'))  # Redirect if user is not logged in

    names_collection = mongo.db.names
    names = [{'_id': str(name['_id']), 'name': name['name']} for name in names_collection.find({'user_id': user_id})]
    return render_template('names.html', names=names)


@app.route('/images')
def show_images():
    user_id = session.get('user_id')

    if user_id is None:
        return redirect(url_for('login'))  # Redirect if user is not logged in

    try:
        images_collection = mongo.db.images
        images = []
        for image in images_collection.find({'user_id': user_id}):  # Only fetch images associated with the user
            if 'image' in image:
                image_data = image['image']
                base64_data = base64.b64encode(image_data).decode('utf-8')
                images.append(base64_data)
        return render_template('image.html', images=images)
    except Exception as e:
        print(f"Error: {e}")
        return render_template('image.html', error="An error occurred while fetching images.")




@app.route('/videos')
def show_videos():
    user_id = session.get('user_id')

    if user_id is None:
        return redirect(url_for('login'))  # Redirect if user is not logged in

    try:
        fs = gridfs.GridFS(mongo.db)
        videos_collection = mongo.db.videos
        videos = []
        for video in videos_collection.find({'user_id': user_id}):  # Only fetch videos associated with the user
            if 'video_id' in video:
                video_id = video['video_id']
                video_data = fs.get(video_id)
                videos.append({
                    'filename': video['metadata']['filename'],
                    'video_id': str(video_data._id)  # Convert ObjectId to string
                })

        return render_template('videos.html', videos=videos)
    except Exception as e:
        print(f"Error: {e}")
        return render_template('error.html', error="An error occurred while fetching videos.")

@app.route('/stream_video/<video_id>')
def stream_video(video_id):
    user_id = session.get('user_id')

    if user_id is None:
        return redirect(url_for('login'))  # Redirect if user is not logged in

    try:
        fs = gridfs.GridFS(mongo.db)
        video_data = fs.get(ObjectId(video_id))
        return send_file(video_data, mimetype='video/mp4')
    except Exception as e:
        print(f"Error: {e}")
        return "Video not found", 404


# @app.route('/delete_name/<name_id>', methods=['POST'])
# def delete_name(name_id):
#     user_id = session.get('user_id')

#     if user_id is None:
#         return redirect(url_for('login'))  # Redirect if user is not logged in

#     names_collection = mongo.db.names
#     names_collection.delete_one({'_id': ObjectId(name_id), 'user_id': user_id})  # Delete the name associated with the user
#     return redirect(url_for('show_names'))

@app.route('/delete_name/<name_id>', methods=['POST'])
def delete_name(name_id):
    user_id = session.get('user_id')
    if user_id is None:
        return redirect(url_for('login'))  # Redirect if user is not logged in
    
    # Delete the name associated with the logged-in user
    names_collection = mongo.db.names
    names_collection.delete_one({'_id': ObjectId(name_id), 'user_id': user_id})
    return redirect(url_for('show_names'))



# Assuming other necessary imports are already in place

@app.route('/delete_image/<image_id>', methods=['POST'])
def delete_image(image_id):
    user_id = session.get('user_id')

    if user_id is None:
        return redirect(url_for('login'))

    images_collection = mongo.db.images
    images_collection.delete_one({'_id': ObjectId(image_id), 'user_id': user_id})
    return redirect(url_for('show_images'))


@app.route('/delete_video/<video_id>', methods=['POST'])
def delete_video(video_id):
    user_id = session.get('user_id')

    if user_id is None:
        return redirect(url_for('login'))  # Redirect if user is not logged in

    videos_collection = mongo.db.videos
    videos_collection.delete_one({'_id': ObjectId(video_id), 'user_id': user_id})  # Delete the video associated with the user
    return redirect(url_for('show_videos'))


@app.route('/logout')
def logout():
    # Clear session data (customize as per your session management)
    session.clear()
    return redirect(url_for('index'))  # Redirect to your login page

if __name__ == '__main__':
    app.run(debug=True)
