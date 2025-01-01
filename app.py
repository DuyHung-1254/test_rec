from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
from tmdbv3api import TMDb, Movie



# Cấu hình TMDb API
tmdb = TMDb()
tmdb.api_key = 'c59338c9d94e537c1913422b5d9f7814'
tmdb.language = 'en'
movie_api = Movie()
# model = joblib.load("../assets/best_bagging_model.pkl")

# Tạo DataFrame giả lập (thay bằng dữ liệu thật của bạn)
# data = {
#     'userId': [1, 1, 1, 1, 1, 1, 1, 1,  2, 2, 2, 2, 2, 2, 2, 2, 2, 2,1],
#     'movieId': [
#         299534, 299574, 299514, 299524,  299535, 19995, 299536, 24428,  # User 1
#         597, 12445, 157336, 76341, 550, 19995, 299540, 299541, 299542, 299543, 299544 # User 2
#     ]
# }
# df = pd.DataFrame(data)
# df = pd.read_csv("../assets/data_train.csv")
df = pd.read_csv("./assets/data_train.csv")

movie_id = df['userId'].unique()
movie_id = movie_id[0:20]
df = df[df['userId'].isin(movie_id)]

# movies_popular_df = pd.read_csv("../assets/movie_recommend.csv")
movies_popular_df = pd.read_csv("./assets/movie_recommend_rate_like.csv")

# Khởi tạo Flask app

app = Flask(__name__)

def get_movie_details(movie_id):
    """Lấy thông tin phim từ TMDb API."""
    details = movie_api.details(movie_id)
    # Trích xuất thể loại dưới dạng danh sách tên
    genres = [genre['name'] for genre in details.genres] if details.genres else []

    return {
        'movie_id': movie_id,
        'title': details.title,
        'poster': f"https://image.tmdb.org/t/p/w500{details.poster_path}" if details.poster_path else None,
        'genres': ", ".join(genres),  # Chuyển danh sách thể loại thành chuỗi, cách nhau bởi dấu phẩy
        'overview': details.overview,
        'release': details.release_date,

    }



@app.route('/')
def home():
    """Trang chủ: Hiển thị danh sách user để chọn."""
    users = df['userId'].unique()
    popular_movies = [
        get_movie_details(mid) for mid in movies_popular_df['movieId'].head(10)
    ]
    popular_movies = [movie for movie in popular_movies if movie['poster'] is not None]
    print(popular_movies)
    return render_template('home.html', users=users , popular_movie = popular_movies)



    
# @app.route('/')
# def home():
#     """Trang chủ: Chuyển hướng đến trang movies với user mặc định."""
#     default_user_id = df['userId'].unique()[0]  # Lấy user đầu tiên
#     return redirect(url_for('movies', user_id=default_user_id))


@app.route('/movies/<int:user_id>')
def movies(user_id):
    """Trang hiển thị 10 bộ phim của user."""
    user_movies = df[df['userId'] == user_id]['userId_tmdb'].head(20).astype(int)
    print(user_movies)
    # Lấy thông tin phim và bỏ qua phim không có poster
    movies = [get_movie_details(mid) for mid in user_movies]

    # print(movies)

    # user_movies = df[df['userId'] == user_id]['userId_tmdb'].head(20)
    # movies = [
    #     {**get_movie_details(mid), 'userId_tmdb': mid} for mid in user_movies
    # ]
    # print(movies)
    



    recommended_movies_df = movies_popular_df.sort_values(by=f'Predict_user{user_id}_1', ascending=False)

    # recommended_movies_df = movies_popular_df[movies_popular_df[f'Predict_user{user_id}'] == 1]
    recommended_movies = [
        get_movie_details(mid) for mid in recommended_movies_df['movieId'].head(20)
    ]
    # print(movies_with_poster)****************************
    # recommended_with_poster = [
    #     movie for movie in recommended_movies if movie['poster'] is not None
    # ]


    return render_template('movies.html', user_id=user_id, movies=movies,recommended_movies=recommended_movies)

@app.route('/movie/<int:movie_id>')
def movie_details(movie_id):
    """Hiển thị chi tiết phim theo movie_id."""
    movie = get_movie_details(movie_id)
    return render_template('movie_details.html', movie=movie)

# Chạy Flask app
if __name__ == '__main__':
    app.run(debug=True)
