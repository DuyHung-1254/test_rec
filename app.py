from flask import Flask, render_template, request, redirect, url_for
import requests
import pandas as pd

from tmdbv3api import TMDb, Movie
app = Flask(__name__)

# API key cho TMDb
api_key = 'c59338c9d94e537c1913422b5d9f7814'
tmdb = TMDb()
tmdb.api_key = 'c59338c9d94e537c1913422b5d9f7814'
tmdb.language = 'en'  # Ngôn ngữ tiếng Việt

movie_api = Movie()
# DataFrame để lưu thông tin các bộ phim đã xem
movie_data = pd.DataFrame(columns=['Tag', 'Title', 'Genres'])

# Hàm lấy danh sách phim phổ biến
def get_popular_movies():
    url = f'https://api.themoviedb.org/3/movie/popular?api_key={api_key}&language=en-US&page=1'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('results', [])
    return []

# Hàm tìm kiếm phim theo tên
def search_movie(movie_name):
    url = f'https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={movie_name}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json().get('results', [])
    return []

# Hàm lấy chi tiết phim theo ID
def get_movie_details(movie_id):
    url = f'https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    return None

# @app.route("/", methods=["GET", "POST"])
# def index():
#     movies = []
#     search_result = None
#     if request.method == "POST":
#         movie_name = request.form.get("movie_name")
#         search_result = search_movie(movie_name)
#     else:
#         movies = get_popular_movies()
#     return render_template("index.html", movies=movies, search_result=search_result)


@app.route("/", methods=["GET", "POST"])
def index():
    movies = []  # Mảng phim sẽ được lấy ở đây
    search_result = None  # Biến lưu kết quả tìm kiếm

    if request.method == "POST":
        # Xử lý khi người dùng gửi form tìm kiếm
        movie_name = request.form.get("movie_name")
        search_result = search_movie(movie_name)  # Tìm kiếm phim
    else:
        # Nếu không phải là POST, lấy danh sách phim phổ biến
        movies = get_popular_movies()

    # Trả về template với dữ liệu phim hoặc kết quả tìm kiếm
    return render_template("index.html", movies=movies, search_result=search_result)


@app.route("/movie/<int:movie_id>", methods=["GET", "POST"])
def movie_details(movie_id):
    global movie_data
    movie = get_movie_details(movie_id)
    print(movie_id)

    if request.method == "POST":
        # Kiểm tra xem cột 'movie_id' có tồn tại trong DataFrame hay không
        if 'Movie_id' not in movie_data.columns:
            movie_data['Movie_id'] = []  # Tạo cột 'movie_id' nếu chưa có

        # Kiểm tra xem movie_id đã có trong DataFrame hay chưa
        if movie_id not in movie_data['Movie_id'].values:
            # Lấy thông tin từ API TMDb
            keywords = movie_api.keywords(movie_id)
            tag = [keyword['name'] for keyword in keywords['keywords']]

            title = movie.get('title')
            genres = ", ".join([genre['name'] for genre in movie.get('genres', [])])

            # Thêm dữ liệu vào DataFrame
            movie_data = pd.concat([movie_data, pd.DataFrame({'Movie_id': [movie_id], 'Tag': [tag], 'Title': [title], 'Genres': [genres]})], ignore_index=True)
            print(movie_data)
            # Ghi vào file CSV (nếu muốn lưu)
            movie_data.to_csv("watched_movies.csv", index=False)
        else:
            print(f"Movie ID {movie_id} has already been saved.")
    
    return render_template("movie_details.html", movie=movie)



if __name__ == "__main__":
    app.run(debug=True)
