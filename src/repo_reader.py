import os


def build_file_tree(root_path, max_depth=3):
    #函数作用：读取一个目录文件的结构，并返回字符串形式的目录树
    #root_path:仓库路径
    #max_depth：最大扫描深度，防止目录过深结果不简洁
    
    if not os.path.exists(root_path):
        return "路径错误"
    
    if not os.path.isdir(root_path):
        return "非文件夹格式"

    ignore_dirs = {
        ".git",
        "__pycache__",
        ".idea",
        "node_modules",
        ".venv",
        "venv"
    }

    lines = []
    #用来装返回目录树的空列表
    root_name = os.path.basename(root_path)
    lines.append(root_name + "/")

    def scan_dir(current_path, prefix="",depth=0):
        if depth>=max_depth:
            return
        #控制扫描深度

        try:
            items = os.listdir(current_path)
        except PermissionError:
            lines.append(prefix+"无法访问该目录")
            return
        #防御，遇到无法访问的目录不直接报错

        items.sort(key=lambda item:(
            not os.path.isdir(os.path.join(current_path, item)),
            #把文件地址补充成完整形式,判断是不是文件夹
            item.lower()
        ))
        #给文件排序，把文件夹放前面

        filtered_items = []
        #筛选需要的名单

        for item in items:
            item_path = os.path.join(current_path, item)

            if os.path.isdir(item_path) and item in ignore_dirs:
                #跳过需要忽略的文件夹
                continue
            
            filtered_items.append(item)

        for index, item in enumerate(filtered_items):
            item_path = os.path.join(current_path,item)
            is_last = (index == len(filtered_items) - 1)

            if is_last:
                connector = "|____ "
                next_prefix = prefix + "     "
            else:
                connector = "|———— "
                next_prefix = prefix + "|     "

            lines.append(prefix + connector + item)

            if os.path.isdir(item_path):
                scan_dir(item_path, next_prefix, depth + 1)

    scan_dir(root_path)

    return "\n".join(lines)             