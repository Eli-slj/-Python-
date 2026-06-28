#图书管理系统

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import datetime
import re
import os

class Book:
    def __init__(self, isbn, title, author, category, publish_date):
        self.isbn = isbn
        self.title = title
        self.author = author
        self.category = category
        self.publish_date = publish_date
        self.is_borrowed = False
        self.borrower = None
        self.borrow_date = None
        self.return_date = None

    def to_dict(self):
        return {
            "isbn": self.isbn,
            "title": self.title,
            "author": self.author,
            "category": self.category,
            "publish_date": self.publish_date,
            "is_borrowed": self.is_borrowed,
            "borrower": self.borrower,
            "borrow_date": self.borrow_date,
            "return_date": self.return_date
        }
    @staticmethod
    def from_dict(data):
        book = Book(
            data["isbn"],
            data["title"],
            data["author"],
            data["category"],
            data["publish_date"]
        )
        book.is_borrowed = data["is_borrowed"]
        book.borrower = data["borrower"]
        book.borrow_date = data["borrow_date"]
        book.return_date = data["return_date"]
        return book

class LibraryManager:
    def __init__(self, data_file="books.json"):
        self.data_file = data_file
        self.books = []
        self.load_data()

    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.books = [Book.from_dict(book_data) for book_data in data]
            except Exception as e:
                messagebox.showerror("错误", f"加载数据失败: {e}")
                self.books = []

    def save_data(self):
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump([book.to_dict() for book in self.books], f, ensure_ascii=False, indent=4)
        except Exception as e:
            messagebox.showerror("错误", f"保存数据失败: {e}")

    def add_book(self, book):
        if any(b.isbn == book.isbn for b in self.books):
            return False, "ISBN已存在，不能重复添加"
        self.books.append(book)
        self.save_data()
        return True, "图书添加成功"

    def search_books(self, keyword, field="all"):
        results = []
        keyword = keyword.lower()
        for book in self.books:
            if (field == "all" and
                (keyword in book.title.lower() or
                 keyword in book.author.lower() or
                 keyword in book.category.lower() or
                 keyword in book.isbn)) or \
                    (field == "title" and keyword in book.title.lower()) or \
                    (field == "author" and keyword in book.author.lower()) or \
                    (field == "category" and keyword in book.category.lower()) or \
                    (field == "isbn" and keyword in book.isbn):
                results.append(book)
        return results

    def get_book_by_isbn(self, isbn):
        for book in self.books:
            if book.isbn == isbn:
                return book
        return None

    def delete_book(self, isbn):
        book = self.get_book_by_isbn(isbn)
        if book:
            self.books.remove(book)
            self.save_data()
            return True, "图书删除成功"
        return False, "没有找到该图书"

    def borrow_book(self, isbn, borrower):
        book = self.get_book_by_isbn(isbn)
        if not book:
            return False, "没有找到该图书"
        if book.is_borrowed:
            return False, "该图书已被借出"
        book.is_borrowed = True
        book.borrower = borrower
        book.borrow_date = datetime.datetime.now().strftime("%Y-%m-%d")
        self.save_data()
        return True, "图书借阅成功"

    def return_book(self, isbn):
        book = self.get_book_by_isbn(isbn)
        if not book:
            return False, "没有找到该图书"
        if not book.is_borrowed:
            return False, "该图书未被借出"
        book.is_borrowed = False
        book.return_date = datetime.datetime.now().strftime("%Y-%m-%d")
        self.save_data()
        return True, "图书归还成功"

    def update_book(self, old_isbn, new_book):
        index = None
        for i, book in enumerate(self.books):
            if book.isbn == old_isbn:
                index = i
                break
        if index is None:
            return False, "没有找到该图书"
        if old_isbn != new_book.isbn and any(b.isbn == new_book.isbn for b in self.books):
            return False, "新ISBN已存在"
        self.books[index] = new_book
        self.save_data()
        return True, "图书信息更新成功"

    def get_statistics(self):
        total = len(self.books)
        available = sum(1 for book in self.books if not book.is_borrowed)
        borrowed = total - available

        categories = {}
        for book in self.books:
            if book.category in categories:
                categories[book.category] += 1
            else:
                categories[book.category] = 1

        return {
            "total": total,
            "available": available,
            "borrowed": borrowed,
            "categories": categories
        }


class LibraryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("个人图书管理系统")
        self.root.geometry("900x600")
        self.root.minsize(800, 500)

        self.library = LibraryManager()

        self.create_widgets()
        self.refresh_book_list()

    def create_widgets(self):
        # 创建选项卡
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 图书列表选项卡
        self.list_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.list_frame, text="图书列表")

        # 添加图书选项卡
        self.add_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.add_frame, text="添加图书")

        # 查询图书选项卡
        self.search_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.search_frame, text="查询图书")

        # 统计信息选项卡
        self.stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.stats_frame, text="统计信息")

        # 图书列表界面
        self.create_list_tab()

        # 添加图书界面
        self.create_add_tab()

        # 查询图书界面
        self.create_search_tab()

        # 统计信息界面
        self.create_stats_tab()

    def create_list_tab(self):
        # 工具栏
        toolbar = ttk.Frame(self.list_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text="刷新", command=self.refresh_book_list).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="修改", command=self.edit_book).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="删除", command=self.delete_book).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="借阅", command=self.borrow_book).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="归还", command=self.return_book).pack(side=tk.LEFT, padx=5)

        # 图书表格
        columns = ("isbn", "title", "author", "category", "publish_date", "status", "borrower")
        self.book_tree = ttk.Treeview(self.list_frame, columns=columns, show="headings")

        # 设置列宽和标题
        self.book_tree.column("isbn", width=120, anchor=tk.CENTER)
        self.book_tree.column("title", width=200, anchor=tk.W)
        self.book_tree.column("author", width=120, anchor=tk.CENTER)
        self.book_tree.column("category", width=100, anchor=tk.CENTER)
        self.book_tree.column("publish_date", width=100, anchor=tk.CENTER)
        self.book_tree.column("status", width=80, anchor=tk.CENTER)
        self.book_tree.column("borrower", width=100, anchor=tk.CENTER)

        self.book_tree.heading("isbn", text="ISBN")
        self.book_tree.heading("title", text="书名")
        self.book_tree.heading("author", text="作者")
        self.book_tree.heading("category", text="分类")
        self.book_tree.heading("publish_date", text="出版日期")
        self.book_tree.heading("status", text="状态")
        self.book_tree.heading("borrower", text="借阅人")

        # 滚动条
        scrollbar = ttk.Scrollbar(self.list_frame, orient=tk.VERTICAL, command=self.book_tree.yview)
        self.book_tree.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.book_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def create_add_tab(self):
        # 表单框架
        form_frame = ttk.LabelFrame(self.add_frame, text="图书信息")
        form_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # 表单字段
        ttk.Label(form_frame, text="ISBN:").grid(row=0, column=0, padx=5, pady=10, sticky=tk.E)
        self.add_isbn = ttk.Entry(form_frame, width=30)
        self.add_isbn.grid(row=0, column=1, padx=5, pady=10, sticky=tk.W)
        ttk.Label(form_frame, text="(10位或13位数字)").grid(row=0, column=2, padx=5, pady=10, sticky=tk.W)

        ttk.Label(form_frame, text="书名:").grid(row=1, column=0, padx=5, pady=10, sticky=tk.E)
        self.add_title = ttk.Entry(form_frame, width=30)
        self.add_title.grid(row=1, column=1, padx=5, pady=10, sticky=tk.W)

        ttk.Label(form_frame, text="作者:").grid(row=2, column=0, padx=5, pady=10, sticky=tk.E)
        self.add_author = ttk.Entry(form_frame, width=30)
        self.add_author.grid(row=2, column=1, padx=5, pady=10, sticky=tk.W)

        ttk.Label(form_frame, text="分类:").grid(row=3, column=0, padx=5, pady=10, sticky=tk.E)
        self.add_category = ttk.Entry(form_frame, width=30)
        self.add_category.grid(row=3, column=1, padx=5, pady=10, sticky=tk.W)

        ttk.Label(form_frame, text="出版日期:").grid(row=4, column=0, padx=5, pady=10, sticky=tk.E)
        self.add_publish_date = ttk.Entry(form_frame, width=30)
        self.add_publish_date.grid(row=4, column=1, padx=5, pady=10, sticky=tk.W)
        ttk.Label(form_frame, text="(格式: YYYY-MM-DD)").grid(row=4, column=2, padx=5, pady=10, sticky=tk.W)

        # 添加按钮
        ttk.Button(form_frame, text="添加图书", command=self.add_book).grid(row=5, column=1, padx=5, pady=20)

    def create_search_tab(self):
        # 查询条件框架
        search_frame = ttk.LabelFrame(self.search_frame, text="查询条件")
        search_frame.pack(fill=tk.X, padx=20, pady=10)

        ttk.Label(search_frame, text="查询方式:").grid(row=0, column=0, padx=5, pady=10, sticky=tk.E)
        self.search_field = tk.StringVar(value="all")
        fields = [
            ("综合查询", "all"),
            ("按书名", "title"),
            ("按作者", "author"),
            ("按分类", "category"),
            ("按ISBN", "isbn")
        ]
        for i, (text, value) in enumerate(fields):
            ttk.Radiobutton(search_frame, text=text, variable=self.search_field, value=value).grid(row=0, column=i + 1,
                                                                                                   padx=10, pady=10)

        ttk.Label(search_frame, text="关键词:").grid(row=1, column=0, padx=5, pady=10, sticky=tk.E)
        self.search_keyword = ttk.Entry(search_frame, width=50)
        self.search_keyword.grid(row=1, column=1, columnspan=4, padx=5, pady=10, sticky=tk.W)

        ttk.Button(search_frame, text="查询", command=self.search_books).grid(row=1, column=5, padx=10, pady=10)

        # 查询结果表格
        result_frame = ttk.LabelFrame(self.search_frame, text="查询结果")
        result_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        columns = ("isbn", "title", "author", "category", "publish_date", "status")
        self.search_tree = ttk.Treeview(result_frame, columns=columns, show="headings")

        self.search_tree.column("isbn", width=120, anchor=tk.CENTER)
        self.search_tree.column("title", width=200, anchor=tk.W)
        self.search_tree.column("author", width=120, anchor=tk.CENTER)
        self.search_tree.column("category", width=100, anchor=tk.CENTER)
        self.search_tree.column("publish_date", width=100, anchor=tk.CENTER)
        self.search_tree.column("status", width=80, anchor=tk.CENTER)

        self.search_tree.heading("isbn", text="ISBN")
        self.search_tree.heading("title", text="书名")
        self.search_tree.heading("author", text="作者")
        self.search_tree.heading("category", text="分类")
        self.search_tree.heading("publish_date", text="出版日期")
        self.search_tree.heading("status", text="状态")

        scrollbar = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.search_tree.yview)
        self.search_tree.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.search_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    def create_stats_tab(self):
        # 统计信息框架
        stats_frame = ttk.LabelFrame(self.stats_frame, text="图书统计")
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.stats_label = ttk.Label(stats_frame, text="", font=("Arial", 12))
        self.stats_label.pack(padx=20, pady=20, anchor=tk.NW)

        ttk.Button(stats_frame, text="刷新统计", command=self.update_stats).pack(padx=20, pady=10, anchor=tk.NW)

        self.update_stats()

    def refresh_book_list(self):
        # 清空表格
        for item in self.book_tree.get_children():
            self.book_tree.delete(item)

        # 插入数据
        for book in self.library.books:
            status = "已借出" if book.is_borrowed else "可借阅"
            borrower = book.borrower if book.is_borrowed else ""
            self.book_tree.insert("", tk.END, values=(
                book.isbn, book.title, book.author, book.category,
                book.publish_date, status, borrower
            ))

    def add_book(self):
        isbn = self.add_isbn.get().strip()
        title = self.add_title.get().strip()
        author = self.add_author.get().strip()
        category = self.add_category.get().strip()
        publish_date = self.add_publish_date.get().strip()

        # 验证输入
        if not re.match(r'^\d{10}(\d{3})?$', isbn):
            messagebox.showerror("错误", "ISBN格式不正确，应为10位或13位数字")
            return

        if not title:
            messagebox.showerror("错误", "书名不能为空")
            return

        book = Book(isbn, title, author, category, publish_date)
        success, message = self.library.add_book(book)

        if success:
            messagebox.showinfo("成功", message)
            # 清空输入框
            self.add_isbn.delete(0, tk.END)
            self.add_title.delete(0, tk.END)
            self.add_author.delete(0, tk.END)
            self.add_category.delete(0, tk.END)
            self.add_publish_date.delete(0, tk.END)
            self.refresh_book_list()
            self.update_stats()
        else:
            messagebox.showerror("错误", message)

    def search_books(self):
        keyword = self.search_keyword.get().strip()
        if not keyword:
            messagebox.showwarning("警告", "请输入查询关键词")
            return

        field = self.search_field.get()
        results = self.library.search_books(keyword, field)

        # 清空表格
        for item in self.search_tree.get_children():
            self.search_tree.delete(item)

        # 插入结果
        for book in results:
            status = "已借出" if book.is_borrowed else "可借阅"
            self.search_tree.insert("", tk.END, values=(
                book.isbn, book.title, book.author, book.category,
                book.publish_date, status
            ))

        if not results:
            messagebox.showinfo("提示", "没有找到匹配的图书")

    def delete_book(self):
        selected = self.book_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要删除的图书")
            return

        item = selected[0]
        values = self.book_tree.item(item, "values")
        isbn = values[0]
        title = values[1]

        confirm = messagebox.askyesno("确认", f"确定要删除《{title}》吗？")
        if confirm:
            success, message = self.library.delete_book(isbn)
            if success:
                messagebox.showinfo("成功", message)
                self.refresh_book_list()
                self.update_stats()
            else:
                messagebox.showerror("错误", message)

    def borrow_book(self):
        selected = self.book_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要借阅的图书")
            return

        item = selected[0]
        values = self.book_tree.item(item, "values")
        isbn = values[0]
        status = values[5]

        if status == "已借出":
            messagebox.showwarning("警告", "该图书已被借出")
            return

        borrower = simpledialog.askstring("借阅", "请输入借阅人姓名:")
        if borrower:
            success, message = self.library.borrow_book(isbn, borrower)
            if success:
                messagebox.showinfo("成功", message)
                self.refresh_book_list()
                self.update_stats()
            else:
                messagebox.showerror("错误", message)

    def return_book(self):
        selected = self.book_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要归还的图书")
            return

        item = selected[0]
        values = self.book_tree.item(item, "values")
        isbn = values[0]
        status = values[5]

        if status == "可借阅":
            messagebox.showwarning("警告", "该图书未被借出")
            return

        success, message = self.library.return_book(isbn)
        if success:
            messagebox.showinfo("成功", message)
            self.refresh_book_list()
            self.update_stats()
        else:
            messagebox.showerror("错误", message)

    def edit_book(self):
        selected = self.book_tree.selection()
        if not selected:
            messagebox.showwarning("警告", "请先选择要修改的图书")
            return

        item = selected[0]
        values = self.book_tree.item(item, "values")
        old_isbn = values[0]

        book = self.library.get_book_by_isbn(old_isbn)
        if not book:
            messagebox.showerror("错误", "没有找到该图书")
            return

        # 创建修改窗口
        edit_window = tk.Toplevel(self.root)
        edit_window.title("修改图书信息")
        edit_window.geometry("400x300")
        edit_window.resizable(False, False)

        # 表单
        ttk.Label(edit_window, text="ISBN:").grid(row=0, column=0, padx=5, pady=10, sticky=tk.E)
        edit_isbn = ttk.Entry(edit_window, width=30)
        edit_isbn.insert(0, book.isbn)
        edit_isbn.grid(row=0, column=1, padx=5, pady=10, sticky=tk.W)

        ttk.Label(edit_window, text="书名:").grid(row=1, column=0, padx=5, pady=10, sticky=tk.E)
        edit_title = ttk.Entry(edit_window, width=30)
        edit_title.insert(0, book.title)
        edit_title.grid(row=1, column=1, padx=5, pady=10, sticky=tk.W)

        ttk.Label(edit_window, text="作者:").grid(row=2, column=0, padx=5, pady=10, sticky=tk.E)
        edit_author = ttk.Entry(edit_window, width=30)
        edit_author.insert(0, book.author)
        edit_author.grid(row=2, column=1, padx=5, pady=10, sticky=tk.W)

        ttk.Label(edit_window, text="分类:").grid(row=3, column=0, padx=5, pady=10, sticky=tk.E)
        edit_category = ttk.Entry(edit_window, width=30)
        edit_category.insert(0, book.category)
        edit_category.grid(row=3, column=1, padx=5, pady=10, sticky=tk.W)

        ttk.Label(edit_window, text="出版日期:").grid(row=4, column=0, padx=5, pady=10, sticky=tk.E)
        edit_publish_date = ttk.Entry(edit_window, width=30)
        edit_publish_date.insert(0, book.publish_date)
        edit_publish_date.grid(row=4, column=1, padx=5, pady=10, sticky=tk.W)

        def save_changes():
            new_isbn = edit_isbn.get().strip()
            new_title = edit_title.get().strip()
            new_author = edit_author.get().strip()
            new_category = edit_category.get().strip()
            new_publish_date = edit_publish_date.get().strip()

            if not re.match(r'^\d{10}(\d{3})?$', new_isbn):
                messagebox.showerror("错误", "ISBN格式不正确，应为10位或13位数字")
                return

            if not new_title:
                messagebox.showerror("错误", "书名不能为空")
                return

            new_book = Book(new_isbn, new_title, new_author, new_category, new_publish_date)
            new_book.is_borrowed = book.is_borrowed
            new_book.borrower = book.borrower
            new_book.borrow_date = book.borrow_date
            new_book.return_date = book.return_date

            success, message = self.library.update_book(old_isbn, new_book)
            if success:
                messagebox.showinfo("成功", message)
                edit_window.destroy()
                self.refresh_book_list()
            else:
                messagebox.showerror("错误", message)

        ttk.Button(edit_window, text="保存", command=save_changes).grid(row=5, column=0, columnspan=2, pady=20)

    def update_stats(self):
        stats = self.library.get_statistics()

        stats_text = f"总藏书量: {stats['total']} 本\n\n"
        stats_text += f"可借阅: {stats['available']} 本\n"
        stats_text += f"已借出: {stats['borrowed']} 本\n\n"
        stats_text += "分类统计:\n"

        for category, count in stats['categories'].items():
            stats_text += f"  {category}: {count} 本\n"

        self.stats_label.config(text=stats_text)


def main():
    root = tk.Tk()
    app = LibraryApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()