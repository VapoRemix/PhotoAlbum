import multiprocessing

bind = '127.0.0.1:8000'  # 指定Gunicorn绑定的IP地址和端口
workers = multiprocessing.cpu_count() * 2 + 1  # 设置Gunicorn工作进程的数量