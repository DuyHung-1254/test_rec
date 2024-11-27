import requests
import pandas as pd
import numpy as np
import re
from nltk.corpus import stopwords
from nltk.sentiment import SentimentIntensityAnalyzer
from gensim.models import KeyedVectors
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfTransformer
import joblib
from tmdbv3api import TMDb, Movie

# Tải stopwords của NLTK
import nltk
nltk.download('stopwords')
nltk.download('vader_lexicon')


hiết lập API key và ngôn ngữ
tmdb = TMDb()
tmdb.api_key = 'c59338c9d94e537c1913422b5d9f7814'
tmdb.language = 'en'  # Ngôn ngữ tiếng Việt



import time

# API key của bạn
API_KEY = "c59338c9d94e537c1913422b5d9f7814"




def get_popular_movies(api_key, total_movies=1000):
    base_url = "https://api.themoviedb.org/3/movie/popular"
    movies = []
    page = 1

    while len(movies) < total_movies:
        # Gọi API
        response = requests.get(base_url, params={"api_key": api_key, "page": page})
        data = response.json()

        # Kiểm tra lỗi
        if "results" not in data:
            print("Error fetching data:", data.get("status_message", "Unknown error"))
            break

        # Trích xuất các cột quan trọng
        for movie in data["results"]:
            movies.append(movie['id'])

        # Dừng nếu không còn phim nào hoặc đã đủ số lượng yêu cầu
        if data["page"] >= data["total_pages"]:
            break

        page += 1

    # Chỉ lấy đúng số lượng yêu cầu
    return movies[:total_movies]

movie_id_df = get_popular_movies(API_KEY, total_movies=1000)
            


# Khởi tạo đối tượng Movie
movie_api = Movie()

# Hàm lấy thông tin phim từ TMDb
import pandas as pd

def get_movie_info(movie_id_df):
    """
    Lấy thông tin chi tiết của phim từ movie_id_df.
    Trả về một DataFrame chứa thông tin phim bao gồm tiêu đề, thể loại, từ khóa, rating, và đường dẫn poster.
    """
    movie_data = []  # Danh sách lưu trữ thông tin từng phim

    # Lặp qua từng ID phim
    for movie_id in movie_id_df:
        movie_details = movie_api.details(movie_id)  # Lấy thông tin chi tiết của phim

        # Lấy danh sách thể loại
        genres = [genre['name'] for genre in movie_details.genres]

        # Lấy danh sách từ khóa (tags)
        keywords = movie_api.keywords(movie_id)
        tags = [keyword['name'] for keyword in keywords['keywords']]

        # Lấy thông tin rating
        rating = movie_details.vote_average  # Rating trung bình từ dữ liệu phim

        # Tạo cấu trúc dữ liệu cho phim
        movie_info = {
            "title": movie_details.title,
            "genres": ", ".join(genres),  # Ghép các thể loại thành chuỗi
            "tags": ", ".join(tags),  # Ghép các từ khóa thành chuỗi
            "rating": rating,
            "poster_path": f"https://image.tmdb.org/t/p/w500{movie_details.poster_path}" if movie_details.poster_path else ""
        }

        movie_data.append(movie_info)  # Thêm thông tin phim vào danh sách

    # Chuyển danh sách thông tin phim thành DataFrame
    movie_df = pd.DataFrame(movie_data)
    return movie_df

# Gọi hàm để lấy DataFrame thông tin phim
movie_infor_df = get_movie_info(movie_id_df)

user_df= movie_infor_df.copy()

user_df["genres"] = user_df["genres"].str.replace("Science Fiction", "Sci-Fi", regex=False)


def clean_text(text):
    # Xóa dấu câu, ký tự đặc biệt và số
    text = re.sub(r'\[REC\]²|\[REC\]', '', text)
    text = re.sub(r'[()/"\'\*\-:.!?#&%+$;½¡xXxx]', '', text)  # Xóa dấu câu và ký tự đặc biệt
    text = re.sub(r'\d+', '', text)  # Xóa số


    # Xóa các từ chỉ có 1 ký tự
    text = re.sub(r'\b\w\b', '', text)
    # Xóa khoảng trắng thừa và dấu phẩy liên tiếp
    text = re.sub(r',\s+', ',', text.strip())  # Xóa khoảng trắng sau dấu phẩy
    text = re.sub(r'^,+', '', text)  # Xóa dấu phẩy đầu dòng
    text = re.sub(r',{2,}', ',', text)  # Xóa dấu phẩy liên tiếp

    # Xóa stopwords
    words = text.split(',')
    filtered_words = [word.strip() for word in words if word.strip().lower() not in stop_words]

    return ','.join(filtered_words)


def clean_space(text):
    text = re.sub(r',\s+', ',', text.strip())  # Xóa khoảng trắng sau dấu phẩy
    return text
    
user_df['title'] = user_df['title'].apply(clean_text)
user_df = user_df[user_df['title'].str.strip() != '']

user_df['tags'] = user_df['tags'].apply(clean_text)
user_df = user_df[user_df['tags'].str.strip() != '']


user_df['genres'] = user_df['genres'].apply(clean_space)
user_df = user_df[user_df['genres'].str.strip() != ''].reset_index(drop = True)



def add_binary_genre(user_df):
    genre_columns = ['unknown', 'Action', 'Adventure', 'Animation', 'Children', 'Comedy', 'Crime', 'Documentary',
                     'Drama', 'Fantasy', 'Film-Noir', 'Horror', 'Musical', 'Mystery', 'Romance', 'Sci-Fi', 'Thriller', 'War', 'Western']

    for genre in genre_columns:
        user_df[genre] = 0

    genre_df = user_df.loc[:, 'unknown':'Western']

    # Duyệt qua từng thể loại của người dùng và gán giá trị nhị phân
    for index, user_genres in enumerate(user_df['genres']):
        # Tách các thể loại phim dựa trên dấu phân cách "|"
        split_genres = user_genres.strip(",").split(",")

        # Đặt 1 vào cột tương ứng nếu thể loại phim xuất hiện
        for genre in split_genres:
            if genre in genre_df.columns:
                user_df.loc[index, genre] = 1

    return user_df

# Sử dụng hàm với DataFrame người dùng
user_df = add_binary_genre(user_df)




def load_glove_model(glove_file):
    glove_model = {}
    with open(glove_file, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.split()
            word = parts[0]
            vector = np.array(parts[1:], dtype='float32')
            glove_model[word] = vector
    return glove_model

glove_model = load_glove_model('D:/document/data_recommnedation_system/glove.6B.300d.txt')

def calculate_max_similarity(tags, titles):
    tag_phrases = tags.lower().split(',')
    title_phrases = titles.lower().split(',')
    print(tag_phrases)
    print(title_phrases)
    
    max_similarity = -1  # Khởi tạo giá trị nhỏ nhất để tìm max
    
    for tag in tag_phrases:
        tag_vectors = [glove_model[word] for word in tag.split() if word in glove_model]
        if tag_vectors:
            tag_vec = np.mean(tag_vectors, axis=0)
        else:
            continue  # Bỏ qua nếu không có từ nào trong từ điển
        
        for title in title_phrases:
            title_vectors = [glove_model[word] for word in title.split() if word in glove_model]
            if title_vectors:
                title_vec = np.mean(title_vectors, axis=0)
            else:
                continue  # Bỏ qua nếu không có từ nào trong từ điển
            
            # Tính độ tương đồng cosine
            similarity = cosine_similarity([tag_vec], [title_vec])[0][0]
            
            if similarity > max_similarity:
                max_similarity = similarity
                
    return max_similarity



user_df['max_similarity_tag_title'] = user_df.apply(lambda row: calculate_max_similarity(row['tags'], row['title']), axis=1)
user_df['max_similarity_tag_genres'] = user_df.apply(lambda row: calculate_max_similarity(row['tags'], row['genres']), axis=1)
user_df['max_similarity_genres_title'] = user_df.apply(lambda row: calculate_max_similarity(row['genres'], row['title']), axis=1)


user_df = user_df.reset_index(drop = True)




binary_genre = user_df.iloc[:,8:26]




transformer = TfidfTransformer(smooth_idf=True, norm ='l2')
tfidf = transformer.fit_transform(binary_genre)
tfidf_df = pd.DataFrame(tfidf.toarray(), columns=binary_genre.columns)

user_df.iloc[:,8:26] =tfidf_df



def delete_columns(df):

    del df['title']
    del df['tags']
    del df['genres']
    del df['unknown']
    del df['rating']
    del df['poster_path']

    return df 

user_df = delete_columns(user_df)   




import joblib

best_model = joblib.load("D:/document/data_recommnedation_system/best_bagging_model.pkl")


predictions = best_model.predict(user_df)

user_df['Predictions'] = predictions


    