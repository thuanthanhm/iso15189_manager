import axios from 'axios';

const api = axios.create({
    baseURL: 'http://127.0.0.1:8000'
});

// 1. Kẹp thẻ Token khi gửi đi (Code cũ)
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
}, (error) => Promise.reject(error));

// 2. [THÊM MỚI] - Bắt lỗi khi Backend từ chối Token
api.interceptors.response.use(
    (response) => response, 
    (error) => {
        // Nếu lỗi 401 (Hết hạn hoặc sai Token)
        if (error.response && error.response.status === 401) {
            localStorage.removeItem('access_token'); // Xóa thẻ hỏng
            window.location.href = '/auth/login';    // Đá văng ra trang đăng nhập
        }
        return Promise.reject(error);
    }
);

export default api;