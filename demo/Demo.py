import os
import numpy as np
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.font import Font
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import cv2
from scipy.ndimage import gaussian_filter
import threading
import time

class UngDungXuLyAnh:
    def __init__(self, root):
        self.root = root
        self.root.title("Ứng dụng Nâng cao Chất lượng Ảnh Từ Ảnh Cũ")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        
        # Thiết lập màu sắc chủ đề
        self.bg_color = "#f0f0f0"
        self.accent_color = "#3498db"
        self.text_color = "#2c3e50"
        self.root.configure(bg=self.bg_color)
        
        # Trạng thái ứng dụng
        self.original_image = None
        self.current_image = None
        self.processed_image = None
        self.image_path = None
        self.is_grayscale = False
        self.processing_history = []
        self.history_position = -1
        self.zoom_level = 100  # phần trăm
        
        # Tham số mặc định
        self.clahe_clip_limit = tk.DoubleVar(value=40.0)
        self.clahe_grid_size = tk.IntVar(value=8)
        self.gaussian_kernel_size = tk.IntVar(value=5)
        self.gaussian_sigma = tk.DoubleVar(value=1.0)
        
        # Tạo giao diện
        self.create_menu()
        self.create_main_layout()
        
        # Thanh trạng thái
        self.status_var = tk.StringVar()
        self.status_var.set("Sẵn sàng")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Gán phím tắt
        self.root.bind("<Control-o>", lambda e: self.open_image())
        self.root.bind("<Control-s>", lambda e: self.save_image())
        self.root.bind("<Control-z>", lambda e: self.undo())
        self.root.bind("<Control-y>", lambda e: self.redo())
        
        # Thông báo chào mừng
        self.show_welcome_message()

    def create_menu(self):
        menubar = tk.Menu(self.root)
        
        # Menu Tệp
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Mở ảnh", command=self.open_image, accelerator="Ctrl+O")
        file_menu.add_command(label="Lưu ảnh đã xử lý", command=self.save_image, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="Thoát", command=self.root.quit)
        menubar.add_cascade(label="Tệp", menu=file_menu)
        
        # Menu Chỉnh sửa
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Hoàn tác", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Làm lại", command=self.redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Đặt lại ảnh", command=self.reset_image)
        menubar.add_cascade(label="Chỉnh sửa", menu=edit_menu)
        
        # Menu Xem
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Phóng to", command=lambda: self.zoom(10))
        view_menu.add_command(label="Thu nhỏ", command=lambda: self.zoom(-10))
        view_menu.add_command(label="Đặt lại thu phóng", command=lambda: self.zoom(reset=True))
        menubar.add_cascade(label="Xem", menu=view_menu)
        
        # Menu Trợ giúp
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Giới thiệu", command=self.show_about)
        help_menu.add_command(label="Trợ giúp", command=self.show_help)
        menubar.add_cascade(label="Trợ giúp", menu=help_menu)
        
        self.root.config(menu=menubar)

    def create_main_layout(self):
        # Khung chính
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Panel bên trái để hiển thị ảnh
        self.left_panel = ttk.Frame(main_frame)
        self.left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Tab cho ảnh gốc và ảnh đã xử lý
        self.image_tabs = ttk.Notebook(self.left_panel)
        self.image_tabs.pack(fill=tk.BOTH, expand=True)
        
        # Tab ảnh gốc
        self.original_tab = ttk.Frame(self.image_tabs)
        self.image_tabs.add(self.original_tab, text="Ảnh gốc")
        
        # Tab ảnh đã xử lý
        self.processed_tab = ttk.Frame(self.image_tabs)
        self.image_tabs.add(self.processed_tab, text="Ảnh đã xử lý")
        
        # Tab so sánh
        self.comparison_tab = ttk.Frame(self.image_tabs)
        self.image_tabs.add(self.comparison_tab, text="So sánh trước/sau")
        
        # Canvas cho ảnh gốc
        self.original_canvas = tk.Canvas(self.original_tab, bg="white")
        self.original_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Canvas cho ảnh đã xử lý
        self.processed_canvas = tk.Canvas(self.processed_tab, bg="white")
        self.processed_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Khung so sánh
        self.comparison_frame = ttk.Frame(self.comparison_tab)
        self.comparison_frame.pack(fill=tk.BOTH, expand=True)
        
        self.comp_original_canvas = tk.Canvas(self.comparison_frame, bg="white")
        self.comp_original_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.comp_processed_canvas = tk.Canvas(self.comparison_frame, bg="white")
        self.comp_processed_canvas.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Panel bên phải cho điều khiển và histogram
        self.right_panel = ttk.Frame(main_frame, width=300)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        self.right_panel.pack_propagate(False)
        
        # Notebook cho các tùy chọn xử lý khác nhau
        self.control_notebook = ttk.Notebook(self.right_panel)
        self.control_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Tab thông tin
        self.info_tab = ttk.Frame(self.control_notebook)
        self.control_notebook.add(self.info_tab, text="Thông tin")
        
        # Tab histogram
        self.histogram_tab = ttk.Frame(self.control_notebook)
        self.control_notebook.add(self.histogram_tab, text="Histogram")
        
        # Tab cân bằng histogram
        self.he_tab = ttk.Frame(self.control_notebook)
        self.control_notebook.add(self.he_tab, text="Cân bằng Histogram")
        
        # Tab CLAHE
        self.clahe_tab = ttk.Frame(self.control_notebook)
        self.control_notebook.add(self.clahe_tab, text="CLAHE")
        
        # Tab làm mờ Gaussian
        self.gaussian_tab = ttk.Frame(self.control_notebook)
        self.control_notebook.add(self.gaussian_tab, text="Làm mờ Gaussian")
        
        # Tạo nội dung cho mỗi tab
        self.create_info_tab()
        self.create_histogram_tab()
        self.create_he_tab()
        self.create_clahe_tab()
        self.create_gaussian_tab()
        
        # Thanh công cụ
        self.create_toolbar()

    def create_toolbar(self):
        toolbar = ttk.Frame(self.left_panel)
        toolbar.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))
        
        # Nút mở
        open_btn = ttk.Button(toolbar, text="Mở ảnh", command=self.open_image)
        open_btn.pack(side=tk.LEFT, padx=2)
        
        # Nút lưu
        save_btn = ttk.Button(toolbar, text="Lưu kết quả", command=self.save_image)
        save_btn.pack(side=tk.LEFT, padx=2)
        
        # Dấu phân cách
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        # Nút hoàn tác
        undo_btn = ttk.Button(toolbar, text="Hoàn tác", command=self.undo)
        undo_btn.pack(side=tk.LEFT, padx=2)
        
        # Nút làm lại
        redo_btn = ttk.Button(toolbar, text="Làm lại", command=self.redo)
        redo_btn.pack(side=tk.LEFT, padx=2)
        
        # Nút đặt lại
        reset_btn = ttk.Button(toolbar, text="Đặt lại", command=self.reset_image)
        reset_btn.pack(side=tk.LEFT, padx=2)
        
        # Dấu phân cách
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, padx=5, fill=tk.Y)
        
        # Điều khiển thu phóng
        zoom_out_btn = ttk.Button(toolbar, text="−", width=2, command=lambda: self.zoom(-10))
        zoom_out_btn.pack(side=tk.LEFT, padx=2)
        
        self.zoom_label = ttk.Label(toolbar, text="100%", width=5)
        self.zoom_label.pack(side=tk.LEFT, padx=2)
        
        zoom_in_btn = ttk.Button(toolbar, text="+", width=2, command=lambda: self.zoom(10))
        zoom_in_btn.pack(side=tk.LEFT, padx=2)

    def create_info_tab(self):
        # Hiển thị thông tin ảnh
        info_frame = ttk.LabelFrame(self.info_tab, text="Thông tin ảnh")
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Thông tin tệp
        self.file_info = ttk.Label(info_frame, text="Chưa tải ảnh")
        self.file_info.pack(anchor=tk.W, padx=5, pady=2)
        
        # Kích thước ảnh
        self.dim_info = ttk.Label(info_frame, text="Kích thước: -")
        self.dim_info.pack(anchor=tk.W, padx=5, pady=2)
        
        # Loại ảnh
        self.type_info = ttk.Label(info_frame, text="Loại: -")
        self.type_info.pack(anchor=tk.W, padx=5, pady=2)
        
        # Kích thước tệp
        self.size_info = ttk.Label(info_frame, text="Kích thước tệp: -")
        self.size_info.pack(anchor=tk.W, padx=5, pady=2)
        
        # Khung thống kê
        stats_frame = ttk.LabelFrame(self.info_tab, text="Thống kê ảnh")
        stats_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Giá trị nhỏ nhất
        self.min_info = ttk.Label(stats_frame, text="Giá trị nhỏ nhất: -")
        self.min_info.pack(anchor=tk.W, padx=5, pady=2)
        
        # Giá trị lớn nhất
        self.max_info = ttk.Label(stats_frame, text="Giá trị lớn nhất: -")
        self.max_info.pack(anchor=tk.W, padx=5, pady=2)
        
        # Giá trị trung bình
        self.mean_info = ttk.Label(stats_frame, text="Giá trị trung bình: -")
        self.mean_info.pack(anchor=tk.W, padx=5, pady=2)
        
        # Độ lệch chuẩn
        self.std_info = ttk.Label(stats_frame, text="Độ lệch chuẩn: -")
        self.std_info.pack(anchor=tk.W, padx=5, pady=2)

    def create_histogram_tab(self):
        # Tạo hình cho histogram
        self.hist_figure = plt.Figure(figsize=(4, 6), dpi=100)
        self.hist_canvas = FigureCanvasTkAgg(self.hist_figure, self.histogram_tab)
        self.hist_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Điều khiển cho histogram
        controls_frame = ttk.Frame(self.histogram_tab)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Hộp kiểm cho thang logarit
        self.log_scale_var = tk.BooleanVar(value=False)
        log_check = ttk.Checkbutton(controls_frame, text="Thang logarit", 
                                    variable=self.log_scale_var, 
                                    command=self.update_histogram)
        log_check.pack(side=tk.LEFT, padx=5)
        
        # Nút làm mới histogram
        refresh_btn = ttk.Button(controls_frame, text="Làm mới", 
                                command=self.update_histogram)
        refresh_btn.pack(side=tk.RIGHT, padx=5)

    def create_he_tab(self):
        # Điều khiển cân bằng histogram
        he_frame = ttk.Frame(self.he_tab)
        he_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Mô tả
        desc = ttk.Label(he_frame, text="Cân bằng Histogram nâng cao độ tương phản\n"
                                      "bằng cách phân phối lại các giá trị cường độ\n"
                                      "trên toàn bộ dải giá trị có sẵn.", 
                        wraplength=280, justify=tk.LEFT)
        desc.pack(anchor=tk.W, padx=5, pady=10)
        
        # Nút áp dụng
        apply_he_btn = ttk.Button(he_frame, text="Áp dụng cân bằng Histogram", 
                                command=self.apply_histogram_equalization)
        apply_he_btn.pack(pady=10)
        
        # Hộp kiểm cho xử lý ảnh màu
        self.process_color_var = tk.BooleanVar(value=True)
        color_check = ttk.Checkbutton(he_frame, text="Xử lý riêng các kênh màu", 
                                    variable=self.process_color_var)
        color_check.pack(anchor=tk.W, padx=5, pady=5)
        
        # So sánh histogram trước/sau
        ttk.Label(he_frame, text="So sánh Histogram trước/sau:").pack(anchor=tk.W, padx=5, pady=5)
        
        # Tạo hình cho so sánh
        self.he_comp_figure = plt.Figure(figsize=(4, 4), dpi=100)
        self.he_comp_canvas = FigureCanvasTkAgg(self.he_comp_figure, he_frame)
        self.he_comp_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def create_clahe_tab(self):
        # Điều khiển CLAHE
        clahe_frame = ttk.Frame(self.clahe_tab)
        clahe_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Mô tả
        desc = ttk.Label(clahe_frame, text="Cân bằng Histogram Thích ứng có Giới hạn Độ tương phản\n"
                                        "nâng cao độ tương phản cục bộ đồng thời hạn chế\n"
                                        "khuếch đại nhiễu.", 
                        wraplength=280, justify=tk.LEFT)
        desc.pack(anchor=tk.W, padx=5, pady=10)
        
        # Thanh trượt giới hạn cắt
        ttk.Label(clahe_frame, text="Giới hạn cắt:").pack(anchor=tk.W, padx=5)
        clip_slider = ttk.Scale(clahe_frame, from_=1.0, to=100.0, 
                              variable=self.clahe_clip_limit, 
                              orient=tk.HORIZONTAL)
        clip_slider.pack(fill=tk.X, padx=5, pady=5)
        
        # Hiển thị giá trị giới hạn cắt
        clip_frame = ttk.Frame(clahe_frame)
        clip_frame.pack(fill=tk.X, padx=5)
        
        ttk.Label(clip_frame, text="Giá trị:").pack(side=tk.LEFT)
        clip_value = ttk.Label(clip_frame, textvariable=tk.StringVar(
            value=str(self.clahe_clip_limit.get())))
        clip_value.pack(side=tk.LEFT, padx=5)
        
        # Cập nhật giá trị khi thanh trượt thay đổi
        def update_clip_value(*args):
            clip_value.config(text=f"{self.clahe_clip_limit.get():.1f}")
        
        self.clahe_clip_limit.trace_add("write", update_clip_value)
        
        # Thanh trượt kích thước lưới
        ttk.Label(clahe_frame, text="Kích thước lưới:").pack(anchor=tk.W, padx=5, pady=(10, 0))
        grid_slider = ttk.Scale(clahe_frame, from_=2, to=16, 
                              variable=self.clahe_grid_size, 
                              orient=tk.HORIZONTAL)
        grid_slider.pack(fill=tk.X, padx=5, pady=5)
        
        # Hiển thị giá trị kích thước lưới
        grid_frame = ttk.Frame(clahe_frame)
        grid_frame.pack(fill=tk.X, padx=5)
        
        ttk.Label(grid_frame, text="Giá trị:").pack(side=tk.LEFT)
        grid_value = ttk.Label(grid_frame, textvariable=tk.StringVar(
            value=str(self.clahe_grid_size.get())))
        grid_value.pack(side=tk.LEFT, padx=5)
        
        # Cập nhật giá trị khi thanh trượt thay đổi
        def update_grid_value(*args):
            grid_value.config(text=str(self.clahe_grid_size.get()))
        
        self.clahe_grid_size.trace_add("write", update_grid_value)
        
        # Nút áp dụng
        apply_clahe_btn = ttk.Button(clahe_frame, text="Áp dụng CLAHE", 
                                   command=self.apply_clahe)
        apply_clahe_btn.pack(pady=10)
        
        # Nút xem trước
        preview_clahe_btn = ttk.Button(clahe_frame, text="Xem trước", 
                                     command=lambda: self.preview_effect("clahe"))
        preview_clahe_btn.pack(pady=5)

    def create_gaussian_tab(self):
        # Điều khiển làm mờ Gaussian
        gaussian_frame = ttk.Frame(self.gaussian_tab)
        gaussian_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Mô tả
        desc = ttk.Label(gaussian_frame, text="Làm mờ Gaussian làm mịn ảnh bằng cách áp dụng\n"
                                           "bộ lọc Gaussian, giảm nhiễu và chi tiết.", 
                        wraplength=280, justify=tk.LEFT)
        desc.pack(anchor=tk.W, padx=5, pady=10)
        
        # Thanh trượt kích thước kernel
        ttk.Label(gaussian_frame, text="Kích thước kernel:").pack(anchor=tk.W, padx=5)
        kernel_slider = ttk.Scale(gaussian_frame, from_=1, to=21, 
                                variable=self.gaussian_kernel_size, 
                                orient=tk.HORIZONTAL)
        kernel_slider.pack(fill=tk.X, padx=5, pady=5)
        
        # Hiển thị giá trị kích thước kernel
        kernel_frame = ttk.Frame(gaussian_frame)
        kernel_frame.pack(fill=tk.X, padx=5)
        
        ttk.Label(kernel_frame, text="Giá trị:").pack(side=tk.LEFT)
        kernel_value = ttk.Label(kernel_frame, textvariable=tk.StringVar(
            value=str(self.gaussian_kernel_size.get())))
        kernel_value.pack(side=tk.LEFT, padx=5)
        
        # Cập nhật giá trị khi thanh trượt thay đổi
        def update_kernel_value(*args):
            # Đảm bảo kích thước kernel là số lẻ
            size = self.gaussian_kernel_size.get()
            if size % 2 == 0:
                self.gaussian_kernel_size.set(size + 1)
            kernel_value.config(text=str(self.gaussian_kernel_size.get()))
        
        self.gaussian_kernel_size.trace_add("write", update_kernel_value)
        
        # Thanh trượt sigma
        ttk.Label(gaussian_frame, text="Sigma:").pack(anchor=tk.W, padx=5, pady=(10, 0))
        sigma_slider = ttk.Scale(gaussian_frame, from_=0.1, to=5.0, 
                               variable=self.gaussian_sigma, 
                               orient=tk.HORIZONTAL)
        sigma_slider.pack(fill=tk.X, padx=5, pady=5)
        
        # Hiển thị giá trị sigma
        sigma_frame = ttk.Frame(gaussian_frame)
        sigma_frame.pack(fill=tk.X, padx=5)
        
        ttk.Label(sigma_frame, text="Giá trị:").pack(side=tk.LEFT)
        sigma_value = ttk.Label(sigma_frame, textvariable=tk.StringVar(
            value=str(self.gaussian_sigma.get())))
        sigma_value.pack(side=tk.LEFT, padx=5)
        
        # Cập nhật giá trị khi thanh trượt thay đổi
        def update_sigma_value(*args):
            sigma_value.config(text=f"{self.gaussian_sigma.get():.1f}")
        
        self.gaussian_sigma.trace_add("write", update_sigma_value)
        
        # Nút áp dụng
        apply_gaussian_btn = ttk.Button(gaussian_frame, text="Áp dụng làm mờ Gaussian", 
                                      command=self.apply_gaussian_blur)
        apply_gaussian_btn.pack(pady=10)
        
        # Nút xem trước
        preview_gaussian_btn = ttk.Button(gaussian_frame, text="Xem trước", 
                                        command=lambda: self.preview_effect("gaussian"))
        preview_gaussian_btn.pack(pady=5)

    def open_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Tệp ảnh", "*.jpg *.jpeg *.png *.bmp *.tif *.tiff")])
        
        if not file_path:
            return
        
        try:
            # Tải ảnh
            self.image_path = file_path
            img = Image.open(file_path)
            
            # Chuyển đổi sang mảng numpy
            img_array = np.array(img)
            
            # Kiểm tra xem có phải ảnh xám không
            if len(img_array.shape) == 2:
                self.is_grayscale = True
            elif len(img_array.shape) == 3 and img_array.shape[2] == 1:
                self.is_grayscale = True
                img_array = img_array.squeeze()
            else:
                self.is_grayscale = False
            
            # Lưu trữ ảnh gốc
            self.original_image = img_array
            self.current_image = img_array.copy()
            self.processed_image = None
            
            # Đặt lại lịch sử
            self.processing_history = [img_array.copy()]
            self.history_position = 0
            
            # Cập nhật giao diện
            self.display_image(self.original_image, self.original_canvas)
            self.update_info()
            self.update_histogram()
            
            # Cập nhật trạng thái
            self.status_var.set(f"Đã tải ảnh: {os.path.basename(file_path)}")
            
            # Chuyển đến tab ảnh gốc
            self.image_tabs.select(0)
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể mở ảnh: {str(e)}")

    def display_image(self, img_array, canvas, is_processed=False):
        if img_array is None:
            return
        
        # Lấy kích thước canvas
        canvas_width = canvas.winfo_width()
        canvas_height = canvas.winfo_height()
        
        # Nếu canvas chưa được khởi tạo, sử dụng kích thước mặc định
        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width = 600
            canvas_height = 400
        
        # Chuyển đổi mảng numpy sang ảnh PIL
        if self.is_grayscale and len(img_array.shape) == 2:
            img = Image.fromarray(img_array.astype(np.uint8), 'L')
        else:
            img = Image.fromarray(img_array.astype(np.uint8))
        
        # Tính toán hệ số thu phóng
        zoom_factor = self.zoom_level / 100.0
        
        # Tính toán kích thước mới dựa trên thu phóng
        img_width = int(img.width * zoom_factor)
        img_height = int(img.height * zoom_factor)
        
        # Thay đổi kích thước ảnh để vừa với canvas trong khi giữ nguyên tỷ lệ khung hình
        if img_width > canvas_width or img_height > canvas_height:
            ratio = min(canvas_width / img_width, canvas_height / img_height)
            img_width = int(img_width * ratio)
            img_height = int(img_height * ratio)
        
        # Thay đổi kích thước ảnh
        if img_width > 0 and img_height > 0:  # Đảm bảo kích thước hợp lệ
            img_resized = img.resize((img_width, img_height), Image.LANCZOS)
            
            # Chuyển đổi sang PhotoImage
            photo = ImageTk.PhotoImage(img_resized)
            
            # Xóa canvas và hiển thị ảnh
            canvas.delete("all")
            canvas.create_image(canvas_width // 2, canvas_height // 2, anchor=tk.CENTER, image=photo)
            
            # Giữ tham chiếu để tránh thu gom rác
            if is_processed:
                self.processed_photo = photo
            else:
                self.original_photo = photo
            
            # Cập nhật chế độ xem so sánh nếu cần
            if is_processed and self.processed_image is not None:
                self.update_comparison_view()

    def update_comparison_view(self):
        if self.original_image is None or self.processed_image is None:
            return
        
        # Lấy kích thước canvas
        canvas_width = self.comp_original_canvas.winfo_width()
        canvas_height = self.comp_original_canvas.winfo_height()
        
        # Nếu canvas chưa được khởi tạo, sử dụng kích thước mặc định
        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width = 300
            canvas_height = 400
        
        # Chuyển đổi mảng numpy sang ảnh PIL
        if self.is_grayscale and len(self.original_image.shape) == 2:
            orig_img = Image.fromarray(self.original_image.astype(np.uint8), 'L')
            proc_img = Image.fromarray(self.processed_image.astype(np.uint8), 'L')
        else:
            orig_img = Image.fromarray(self.original_image.astype(np.uint8))
            proc_img = Image.fromarray(self.processed_image.astype(np.uint8))
        
        # Tính toán hệ số thu phóng
        zoom_factor = self.zoom_level / 100.0
        
        # Tính toán kích thước mới dựa trên thu phóng
        img_width = int(orig_img.width * zoom_factor)
        img_height = int(orig_img.height * zoom_factor)
        
        # Thay đổi kích thước ảnh để vừa với canvas trong khi giữ nguyên tỷ lệ khung hình
        if img_width > canvas_width or img_height > canvas_height:
            ratio = min(canvas_width / img_width, canvas_height / img_height)
            img_width = int(img_width * ratio)
            img_height = int(img_height * ratio)
        
        # Thay đổi kích thước ảnh
        if img_width > 0 and img_height > 0:  # Đảm bảo kích thước hợp lệ
            orig_resized = orig_img.resize((img_width, img_height), Image.LANCZOS)
            proc_resized = proc_img.resize((img_width, img_height), Image.LANCZOS)
            
            # Chuyển đổi sang PhotoImage
            orig_photo = ImageTk.PhotoImage(orig_resized)
            proc_photo = ImageTk.PhotoImage(proc_resized)
            
            # Xóa canvas và hiển thị ảnh
            self.comp_original_canvas.delete("all")
            self.comp_processed_canvas.delete("all")
            
            self.comp_original_canvas.create_image(canvas_width // 2, canvas_height // 2, 
                                                anchor=tk.CENTER, image=orig_photo)
            self.comp_processed_canvas.create_image(canvas_width // 2, canvas_height // 2, 
                                                 anchor=tk.CENTER, image=proc_photo)
            
            # Thêm nhãn
            self.comp_original_canvas.create_text(10, 20, anchor=tk.NW, 
                                               text="Ảnh gốc", fill="black", 
                                               font=("Arial", 12, "bold"))
            self.comp_processed_canvas.create_text(10, 20, anchor=tk.NW, 
                                                text="Ảnh đã xử lý", fill="black", 
                                                font=("Arial", 12, "bold"))
            
            # Giữ tham chiếu để tránh thu gom rác
            self.comp_orig_photo = orig_photo
            self.comp_proc_photo = proc_photo

    def update_info(self):
        if self.original_image is None:
            return
        
        # Cập nhật thông tin tệp
        self.file_info.config(text=f"Tệp: {os.path.basename(self.image_path)}")
        
        # Cập nhật kích thước
        if self.is_grayscale:
            h, w = self.original_image.shape
            self.dim_info.config(text=f"Kích thước: {w} × {h}")
        else:
            h, w, c = self.original_image.shape
            self.dim_info.config(text=f"Kích thước: {w} × {h} × {c}")
        
        # Cập nhật thông tin loại
        img_type = "Ảnh xám" if self.is_grayscale else "Ảnh màu (RGB)"
        self.type_info.config(text=f"Loại: {img_type}")
        
        # Cập nhật kích thước tệp
        file_size = os.path.getsize(self.image_path)
        size_str = self.format_size(file_size)
        self.size_info.config(text=f"Kích thước tệp: {size_str}")
        
        # Cập nhật thống kê
        if self.is_grayscale:
            min_val = np.min(self.original_image)
            max_val = np.max(self.original_image)
            mean_val = np.mean(self.original_image)
            std_val = np.std(self.original_image)
        else:
            # Tính toán thống kê cho mỗi kênh
            min_val = [np.min(self.original_image[:,:,i]) for i in range(3)]
            max_val = [np.max(self.original_image[:,:,i]) for i in range(3)]
            mean_val = [np.mean(self.original_image[:,:,i]) for i in range(3)]
            std_val = [np.std(self.original_image[:,:,i]) for i in range(3)]
            
            # Định dạng để hiển thị
            min_val = f"R:{min_val[0]}, G:{min_val[1]}, B:{min_val[2]}"
            max_val = f"R:{max_val[0]}, G:{max_val[1]}, B:{max_val[2]}"
            mean_val = f"R:{mean_val[0]:.2f}, G:{mean_val[1]:.2f}, B:{mean_val[2]:.2f}"
            std_val = f"R:{std_val[0]:.2f}, G:{std_val[1]:.2f}, B:{std_val[2]:.2f}"
        
        self.min_info.config(text=f"Giá trị nhỏ nhất: {min_val}")
        self.max_info.config(text=f"Giá trị lớn nhất: {max_val}")
        self.mean_info.config(text=f"Giá trị trung bình: {mean_val}")
        self.std_info.config(text=f"Độ lệch chuẩn: {std_val}")

    def format_size(self, size_bytes):
        """Định dạng kích thước tệp theo định dạng dễ đọc"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"

    def update_histogram(self):
        if self.original_image is None:
            return
        
        # Xóa hình
        self.hist_figure.clear()
        
        # Tạo histogram
        if self.is_grayscale:
            # Một histogram cho ảnh xám
            ax = self.hist_figure.add_subplot(111)
            hist, bins = np.histogram(self.original_image.flatten(), bins=256, range=[0, 256])
            
            if self.log_scale_var.get():
                ax.set_yscale('log')
                # Thêm 1 để tránh log(0)
                hist = hist + 1
            
            ax.bar(bins[:-1], hist, width=1, color='gray')
            ax.set_xlim(0, 255)
            ax.set_title('Histogram ảnh xám')
            ax.set_xlabel('Giá trị điểm ảnh')
            ax.set_ylabel('Tần suất')
            
        else:
            # Histogram RGB
            colors = ('r', 'g', 'b')
            for i, color in enumerate(colors):
                ax = self.hist_figure.add_subplot(3, 1, i+1)
                hist, bins = np.histogram(self.original_image[:,:,i].flatten(), 
                                        bins=256, range=[0, 256])
                
                if self.log_scale_var.get():
                    ax.set_yscale('log')
                    # Thêm 1 để tránh log(0)
                    hist = hist + 1
                
                ax.bar(bins[:-1], hist, width=1, color=color, alpha=0.7)
                ax.set_xlim(0, 255)
                ax.set_title(f'Kênh {color.upper()}')
                
                # Chỉ thêm nhãn x cho biểu đồ dưới cùng
                if i == 2:
                    ax.set_xlabel('Giá trị điểm ảnh')
                ax.set_ylabel('Tần suất')
        
        self.hist_figure.tight_layout()
        self.hist_canvas.draw()

    def histogram_equalization(self, img):
        """Áp dụng cân bằng histogram cho ảnh"""
        if len(img.shape) == 2:
            # Ảnh xám
            flat = img.flatten()
            hist = np.bincount(flat, minlength=256)
            cdf = hist.cumsum()
            # Tránh chia cho 0
            cdf_m = np.ma.masked_equal(cdf, 0)
            cdf_m = (cdf_m - cdf_m.min()) * 255 / (cdf_m.max() - cdf_m.min())
            cdf = np.ma.filled(cdf_m, 0).astype(np.uint8)
            img_eq = cdf[flat].reshape(img.shape)
            return img_eq
        else:
            # Ảnh màu
            if self.process_color_var.get():
                # Xử lý từng kênh riêng biệt
                img_eq = np.zeros_like(img)
                for i in range(3):
                    img_eq[:,:,i] = self.histogram_equalization(img[:,:,i])
                return img_eq
            else:
                # Chuyển đổi sang HSV, cân bằng kênh V, chuyển đổi trở lại RGB
                hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
                hsv[:,:,2] = self.histogram_equalization(hsv[:,:,2])
                return cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

    def apply_histogram_equalization(self):
        if self.current_image is None:
            messagebox.showinfo("Thông tin", "Vui lòng mở ảnh trước.")
            return
        
        # Hiển thị chỉ báo xử lý
        self.status_var.set("Đang xử lý: Áp dụng cân bằng histogram...")
        self.root.update()
        
        # Áp dụng cân bằng histogram
        try:
            result = self.histogram_equalization(self.current_image)
            
            # Cập nhật ảnh đã xử lý
            self.processed_image = result
            self.display_image(result, self.processed_canvas, is_processed=True)
            
            # Thêm vào lịch sử
            self.add_to_history(result)
            
            # Cập nhật ảnh hiện tại
            self.current_image = result.copy()
            
            # Chuyển đến tab ảnh đã xử lý
            self.image_tabs.select(1)
            
            # Cập nhật trạng thái
            self.status_var.set("Đã áp dụng cân bằng histogram thành công.")
            
            # Cập nhật so sánh histogram
            self.update_he_comparison()
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể áp dụng cân bằng histogram: {str(e)}")
            self.status_var.set("Lỗi khi áp dụng cân bằng histogram.")

    def update_he_comparison(self):
        """Cập nhật so sánh histogram trước/sau"""
        if self.original_image is None or self.processed_image is None:
            return
        
        # Xóa hình
        self.he_comp_figure.clear()
        
        if self.is_grayscale:
            # Histogram gốc
            ax1 = self.he_comp_figure.add_subplot(211)
            hist1, bins1 = np.histogram(self.original_image.flatten(), bins=256, range=[0, 256])
            ax1.bar(bins1[:-1], hist1, width=1, color='gray')
            ax1.set_xlim(0, 255)
            ax1.set_title('Histogram gốc')
            
            # Histogram đã xử lý
            ax2 = self.he_comp_figure.add_subplot(212)
            hist2, bins2 = np.histogram(self.processed_image.flatten(), bins=256, range=[0, 256])
            ax2.bar(bins2[:-1], hist2, width=1, color='blue')
            ax2.set_xlim(0, 255)
            ax2.set_title('Histogram đã cân bằng')
            ax2.set_xlabel('Giá trị điểm ảnh')
            
        else:
            # Đối với ảnh màu, chỉ hiển thị histogram độ sáng
            # Chuyển đổi sang ảnh xám để so sánh histogram
            if len(self.original_image.shape) == 3:
                orig_gray = cv2.cvtColor(self.original_image, cv2.COLOR_RGB2GRAY)
            else:
                orig_gray = self.original_image
                
            if len(self.processed_image.shape) == 3:
                proc_gray = cv2.cvtColor(self.processed_image, cv2.COLOR_RGB2GRAY)
            else:
                proc_gray = self.processed_image
            
            # Histogram gốc
            ax1 = self.he_comp_figure.add_subplot(211)
            hist1, bins1 = np.histogram(orig_gray.flatten(), bins=256, range=[0, 256])
            ax1.bar(bins1[:-1], hist1, width=1, color='gray')
            ax1.set_xlim(0, 255)
            ax1.set_title('Histogram gốc')
            
            # Histogram đã xử lý
            ax2 = self.he_comp_figure.add_subplot(212)
            hist2, bins2 = np.histogram(proc_gray.flatten(), bins=256, range=[0, 256])
            ax2.bar(bins2[:-1], hist2, width=1, color='blue')
            ax2.set_xlim(0, 255)
            ax2.set_title('Histogram đã cân bằng')
            ax2.set_xlabel('Giá trị điểm ảnh')
        
        self.he_comp_figure.tight_layout()
        self.he_comp_canvas.draw()

    def clahe(self, img, clip_limit=40.0, grid_size=(8,8)):
        """Áp dụng CLAHE cho ảnh"""
        if len(img.shape) == 2:
            # Ảnh xám
            h, w = img.shape
            gh, gw = grid_size
            out = np.zeros_like(img)
            h_step = h // gh
            w_step = w // gw
            
            for i in range(gh):
                for j in range(gw):
                    y0 = i * h_step
                    x0 = j * w_step
                    y1 = h if i == gh-1 else (i+1)*h_step
                    x1 = w if j == gw-1 else (j+1)*w_step
                    
                    tile = img[y0:y1, x0:x1]
                    flat = tile.flatten()
                    hist = np.bincount(flat, minlength=256)
                    
                    # Cắt histogram
                    excess = np.clip(hist - clip_limit, 0, None)
                    n_excess = excess.sum()
                    hist = np.minimum(hist, clip_limit)
                    
                    # Phân phối lại phần dư
                    if n_excess > 0:
                        redistrib = n_excess // 256
                        hist += redistrib
                    
                    # Tính CDF
                    cdf = hist.cumsum()
                    
                    # Tránh chia cho 0
                    if cdf[-1] > 0:
                        cdf_normalized = cdf * 255 / cdf[-1]
                        tile_eq = cdf_normalized[flat].reshape(tile.shape).astype(np.uint8)
                        out[y0:y1, x0:x1] = tile_eq
                    else:
                        out[y0:y1, x0:x1] = tile
            
            return out
        else:
            # Ảnh màu
            if self.process_color_var.get():
                # Xử lý từng kênh riêng biệt
                img_eq = np.zeros_like(img)
                for i in range(3):
                    img_eq[:,:,i] = self.clahe(img[:,:,i], clip_limit, grid_size)
                return img_eq
            else:
                # Chuyển đổi sang HSV, áp dụng CLAHE cho kênh V, chuyển đổi trở lại RGB
                hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
                hsv[:,:,2] = self.clahe(hsv[:,:,2], clip_limit, grid_size)
                return cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

    def apply_clahe(self):
        if self.current_image is None:
            messagebox.showinfo("Thông tin", "Vui lòng mở ảnh trước.")
            return
        
        # Hiển thị chỉ báo xử lý
        self.status_var.set("Đang xử lý: Áp dụng CLAHE...")
        self.root.update()
        
        # Lấy tham số
        clip_limit = self.clahe_clip_limit.get()
        grid_size = (self.clahe_grid_size.get(), self.clahe_grid_size.get())
        
        # Áp dụng CLAHE
        try:
            # Sử dụng CLAHE của OpenCV để hiệu suất tốt hơn
            if self.is_grayscale:
                # Cho ảnh xám
                clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=grid_size)
                result = clahe.apply(self.current_image.astype(np.uint8))
            else:
                # Cho ảnh màu
                if self.process_color_var.get():
                    # Xử lý từng kênh riêng biệt
                    result = np.zeros_like(self.current_image)
                    for i in range(3):
                        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=grid_size)
                        result[:,:,i] = clahe.apply(self.current_image[:,:,i].astype(np.uint8))
                else:
                    # Chuyển đổi sang LAB, áp dụng CLAHE cho kênh L, chuyển đổi trở lại RGB
                    lab = cv2.cvtColor(self.current_image, cv2.COLOR_RGB2LAB)
                    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=grid_size)
                    lab[:,:,0] = clahe.apply(lab[:,:,0])
                    result = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
            
            # Cập nhật ảnh đã xử lý
            self.processed_image = result
            self.display_image(result, self.processed_canvas, is_processed=True)
            
            # Thêm vào lịch sử
            self.add_to_history(result)
            
            # Cập nhật ảnh hiện tại
            self.current_image = result.copy()
            
            # Chuyển đến tab ảnh đã xử lý
            self.image_tabs.select(1)
            
            # Cập nhật trạng thái
            self.status_var.set("Đã áp dụng CLAHE thành công.")
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể áp dụng CLAHE: {str(e)}")
            self.status_var.set("Lỗi khi áp dụng CLAHE.")

    def apply_gaussian_blur(self):
        if self.current_image is None:
            messagebox.showinfo("Thông tin", "Vui lòng mở ảnh trước.")
            return
        
        # Hiển thị chỉ báo xử lý
        self.status_var.set("Đang xử lý: Áp dụng làm mờ Gaussian...")
        self.root.update()
        
        # Lấy tham số
        kernel_size = self.gaussian_kernel_size.get()
        sigma = self.gaussian_sigma.get()
        
        # Áp dụng làm mờ Gaussian
        try:
            # Sử dụng OpenCV để hiệu suất tốt hơn
            result = cv2.GaussianBlur(self.current_image, 
                                     (kernel_size, kernel_size), 
                                     sigma)
            
            # Cập nhật ảnh đã xử lý
            self.processed_image = result
            self.display_image(result, self.processed_canvas, is_processed=True)
            
            # Thêm vào lịch sử
            self.add_to_history(result)
            
            # Cập nhật ảnh hiện tại
            self.current_image = result.copy()
            
            # Chuyển đến tab ảnh đã xử lý
            self.image_tabs.select(1)
            
            # Cập nhật trạng thái
            self.status_var.set("Đã áp dụng làm mờ Gaussian thành công.")
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể áp dụng làm mờ Gaussian: {str(e)}")
            self.status_var.set("Lỗi khi áp dụng làm mờ Gaussian.")

    def preview_effect(self, effect_type):
        """Hiển thị xem trước hiệu ứng mà không áp dụng nó"""
        if self.current_image is None:
            messagebox.showinfo("Thông tin", "Vui lòng mở ảnh trước.")
            return
        
        # Hiển thị chỉ báo xử lý
        self.status_var.set(f"Đang xử lý: Tạo xem trước {effect_type}...")
        self.root.update()
        
        try:
            if effect_type == "clahe":
                # Lấy tham số
                clip_limit = self.clahe_clip_limit.get()
                grid_size = (self.clahe_grid_size.get(), self.clahe_grid_size.get())
                
                # Áp dụng CLAHE
                if self.is_grayscale:
                    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=grid_size)
                    result = clahe.apply(self.current_image.astype(np.uint8))
                else:
                    if self.process_color_var.get():
                        result = np.zeros_like(self.current_image)
                        for i in range(3):
                            clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=grid_size)
                            result[:,:,i] = clahe.apply(self.current_image[:,:,i].astype(np.uint8))
                    else:
                        lab = cv2.cvtColor(self.current_image, cv2.COLOR_RGB2LAB)
                        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=grid_size)
                        lab[:,:,0] = clahe.apply(lab[:,:,0])
                        result = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
                
            elif effect_type == "gaussian":
                # Lấy tham số
                kernel_size = self.gaussian_kernel_size.get()
                sigma = self.gaussian_sigma.get()
                
                # Áp dụng làm mờ Gaussian
                result = cv2.GaussianBlur(self.current_image, 
                                         (kernel_size, kernel_size), 
                                         sigma)
            
            # Hiển thị xem trước
            self.processed_image = result
            self.display_image(result, self.processed_canvas, is_processed=True)
            
            # Chuyển đến tab ảnh đã xử lý
            self.image_tabs.select(1)
            
            # Cập nhật trạng thái
            self.status_var.set(f"Đã tạo xem trước {effect_type.upper()}. Nhấp 'Áp dụng' để giữ thay đổi.")
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tạo xem trước: {str(e)}")
            self.status_var.set("Lỗi khi tạo xem trước.")

    def add_to_history(self, img):
        """Thêm ảnh vào lịch sử xử lý"""
        # Xóa bất kỳ lịch sử phía trước nếu chúng ta không ở cuối
        if self.history_position < len(self.processing_history) - 1:
            self.processing_history = self.processing_history[:self.history_position + 1]
        
        # Thêm ảnh mới vào lịch sử
        self.processing_history.append(img.copy())
        self.history_position = len(self.processing_history) - 1

    def undo(self):
        """Hoàn tác thao tác cuối cùng"""
        if self.history_position > 0:
            self.history_position -= 1
            self.current_image = self.processing_history[self.history_position].copy()
            self.processed_image = self.current_image.copy()
            
            # Cập nhật hiển thị
            self.display_image(self.current_image, self.processed_canvas, is_processed=True)
            
            # Chuyển đến tab ảnh đã xử lý
            self.image_tabs.select(1)
            
            # Cập nhật trạng thái
            self.status_var.set("Hoàn tác thành công.")
        else:
            self.status_var.set("Không có gì để hoàn tác.")

    def redo(self):
        """Làm lại thao tác đã hoàn tác cuối cùng"""
        if self.history_position < len(self.processing_history) - 1:
            self.history_position += 1
            self.current_image = self.processing_history[self.history_position].copy()
            self.processed_image = self.current_image.copy()
            
            # Cập nhật hiển thị
            self.display_image(self.current_image, self.processed_canvas, is_processed=True)
            
            # Chuyển đến tab ảnh đã xử lý
            self.image_tabs.select(1)
            
            # Cập nhật trạng thái
            self.status_var.set("Làm lại thành công.")
        else:
            self.status_var.set("Không có gì để làm lại.")

    def reset_image(self):
        """Đặt lại về ảnh gốc"""
        if self.original_image is None:
            return
        
        # Đặt lại ảnh hiện tại về ảnh gốc
        self.current_image = self.original_image.copy()
        self.processed_image = None
        
        # Đặt lại lịch sử
        self.processing_history = [self.original_image.copy()]
        self.history_position = 0
        
        # Cập nhật hiển thị
        self.display_image(self.current_image, self.processed_canvas, is_processed=True)
        
        # Chuyển đến tab ảnh gốc
        self.image_tabs.select(0)
        
        # Cập nhật trạng thái
        self.status_var.set("Đã đặt lại ảnh về ảnh gốc.")

    def save_image(self):
        """Lưu ảnh đã xử lý"""
        if self.processed_image is None and self.current_image is None:
            messagebox.showinfo("Thông tin", "Không có ảnh đã xử lý để lưu.")
            return
        
        # Lấy đường dẫn lưu
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("Tệp PNG", "*.png"), 
                      ("Tệp JPEG", "*.jpg"), 
                      ("Tất cả các tệp", "*.*")])
        
        if not file_path:
            return
        
        try:
            # Lưu ảnh
            img_to_save = self.processed_image if self.processed_image is not None else self.current_image
            
            if self.is_grayscale and len(img_to_save.shape) == 2:
                img = Image.fromarray(img_to_save.astype(np.uint8), 'L')
            else:
                img = Image.fromarray(img_to_save.astype(np.uint8))
            
            img.save(file_path)
            
            # Cập nhật trạng thái
            self.status_var.set(f"Đã lưu ảnh vào {file_path}")
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu ảnh: {str(e)}")
            self.status_var.set("Lỗi khi lưu ảnh.")

    def zoom(self, amount=0, reset=False):
        """Thu phóng ảnh"""
        if reset:
            self.zoom_level = 100
        else:
            self.zoom_level += amount
            
        # Giới hạn mức thu phóng
        self.zoom_level = max(10, min(500, self.zoom_level))
        
        # Cập nhật nhãn thu phóng
        self.zoom_label.config(text=f"{self.zoom_level}%")
        
        # Cập nhật hiển thị ảnh
        if self.original_image is not None:
            self.display_image(self.original_image, self.original_canvas)
        
        if self.processed_image is not None:
            self.display_image(self.processed_image, self.processed_canvas, is_processed=True)

    def show_about(self):
        """hộp thoại giới thiệu"""
        about_text = """Ứng dụng Nâng cao Chất lượng Ảnh

Phiên bản 1.0

Tính năng:
- Cân bằng Histogram
- CLAHE (Cân bằng Histogram Thích ứng có Giới hạn Độ tương phản)
- Làm mờ Gaussian
- Hiển thị histogram thời gian thực
- So sánh trước/sau
"""
        
        messagebox.showinfo("Giới thiệu", about_text)

    def show_help(self):
        """hộp thoại trợ giúp"""
        help_text = """Cách sử dụng:

1. Mở ảnh bằng Tệp > Mở ảnh hoặc nút Mở ảnh
2. Chọn phương pháp xử lý từ các tab ở bên phải
3. Điều chỉnh tham số nếu cần
4. Nhấp Áp dụng để xử lý ảnh
5. Sử dụng các tab để xem ảnh gốc, ảnh đã xử lý hoặc so sánh
6. Lưu kết quả bằng Tệp > Lưu ảnh đã xử lý

Phím tắt:
- Ctrl+O: Mở ảnh trong tệp
- Ctrl+S: Lưu ảnh đã xử lý
- Ctrl+Z: Hoàn tác
- Ctrl+Y: Làm lại"""
        
        messagebox.showinfo("Trợ giúp!", help_text)

    def show_welcome_message(self):
        """Hiển thị thông báo chào mừng khi khởi động"""
        welcome_text = """Chào mừng đến với Ứng dụng Nâng cao Chất lượng Ảnh

Ứng dụng này cho phép bạn nâng cao chất lượng ảnh bằng:
• Cân bằng Histogram
• CLAHE (Cân bằng Histogram Thích ứng có Giới hạn Độ tương phản)
• Làm mờ Gaussian

Để bắt đầu, hãy mở ảnh bằng nút 'Mở ảnh' hoặc Tệp > Mở ảnh"""
        
        messagebox.showinfo("Chào mừng", welcome_text)

if __name__ == "__main__":
    root = tk.Tk()
    app = UngDungXuLyAnh(root)
    root.mainloop()