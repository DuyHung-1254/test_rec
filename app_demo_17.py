import streamlit as st
import pandas as pd
import requests

# Hàm gọi TMDb API để lấy thông tin về bộ phim
def get_tmdb_movie_info(movie_name):
    api_key = 'c59338c9d94e537c1913422b5d9f7814'  # Thay YOUR_TMDB_API_KEY bằng API key của bạn
    url = f'https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={movie_name}'
    response = requests.get(url)
    movie_data = response.json()
    
    if movie_data['results']:
        return movie_data['results'][0]  # Trả về bộ phim đầu tiên trong kết quả tìm kiếm
    else:
        return None

# Đọc dữ liệu từ file CSV
df = pd.read_csv("D:/document/data_recommnedation_system/data_26_12.csv")
user_df = df.loc[:, ['userId', 'title', 'tag', 'genres']]

# Giới hạn danh sách user
user_list = user_df['userId'].unique()
user_list = user_list[:2]
df = user_df[user_df['userId'].isin(user_list)]

# Tiêu đề trang web
st.title("Danh sách bộ phim đã xem")

# Tạo dropdown để người dùng chọn userID
user_list = df['userId'].unique()
selected_user = st.selectbox("Chọn người dùng", user_list)

# Lọc danh sách bộ phim theo user đã chọn
movies = df[df['userId'] == selected_user]['title'].tolist()

# Hiển thị tên bộ phim
if movies:
    st.write(f"Người dùng {selected_user} đã xem các bộ phim sau:")
    posters = []  # Danh sách poster để hiển thị
    for movie in movies[:10]:  # Chỉ lấy tối đa 10 bộ phim
        # st.write(f"- {movie}")

        # Gọi TMDb API để lấy thông tin về bộ phim
        movie_info = get_tmdb_movie_info(movie)

        if movie_info and movie_info.get('poster_path'):
            posters.append(f"https://image.tmdb.org/t/p/w500{movie_info['poster_path']}")
        else:
            posters.append(None)  # Nếu không có thông tin poster

    # Hiển thị poster thành nhiều hàng, mỗi hàng tối đa 5 poster
    for row_start in range(0, len(posters), 5):  # Duyệt theo nhóm 5 poster
        cols = st.columns(5)  # Tạo 5 cột ngang
        for i, poster in enumerate(posters[row_start:row_start + 5]):
            if poster:
                with cols[i]:
                    st.image(poster, use_container_width=True)
            else:
                with cols[i]:
                    st.write("Không tìm thấy poster.")
else:
    st.write(f"Không có bộ phim nào cho người dùng {selected_user}.")


    
