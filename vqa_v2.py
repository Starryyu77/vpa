import dashscope
import base64
from PIL import Image
import os
import json
import logging
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import io
import time

# 配置日志
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logging.getLogger().setLevel(logging.DEBUG)  # 启用调试日志


# 编码图片为 Base64
def encode_image(image_path):
    try:
        with Image.open(image_path) as img:
            buffered = io.BytesIO()
            img.save(buffered, format=img.format if img.format else "JPEG")
            return base64.b64encode(buffered.getvalue()).decode("utf-8")
    except Exception as e:
        logging.error(f"图片编码失败: {image_path} - {str(e)}")
        raise


# 加载标注文件
def load_annotations(json_path):
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"读取标注文件失败: {json_path} - {str(e)}")
        raise


# 查找图片对应的标注
def find_annotation(annotations, image_name):
    base_name = os.path.basename(image_name).split('.')[0]  # 提取 "00000001"
    logging.debug(f"搜索标注，图片名: {base_name}")
    for ann in annotations:
        ann_base = os.path.basename(ann['img1']).split('.')[0].replace('/data/upload/2/', '')
        logging.debug(f"比较: {ann_base}")
        if ann_base == base_name:
            return ann
    logging.warning(f"未找到 {image_name} 的标注")
    return None


# 解析标注信息
def parse_annotation(ann):
    if not ann:
        return {"count": "未知", "type": [], "who": "未知", "issues": []}
    count = ann.get('Object_count', '未知')
    obj_type = ann.get('Object_type', {})
    obj_type_choices = obj_type.get('choices', obj_type) if isinstance(obj_type, dict) else obj_type
    who = ann.get('Collaboration_who', '未知')
    issues = ann.get('PerceptionIssues', [])
    return {"count": count, "type": obj_type_choices, "who": who, "issues": issues}


# 选择成对图片
def select_image_pair(base_dir, annotations, sort_by):
    pairs = []
    folders = [f for f in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, f)) and f.isdigit()]
    for folder in folders:
        folder_path = os.path.join(base_dir, folder)
        files = [f for f in os.listdir(folder_path) if f.endswith('.jpg')]
        for file in files:
            if ' 2.jpg' not in file:
                base_name = file.replace('.jpg', '')
                pair_file = f"{base_name} 2.jpg"
                img1_path = os.path.join(folder_path, file)
                img2_path = os.path.join(folder_path, pair_file)
                if os.path.exists(img2_path):
                    ann1 = find_annotation(annotations, img1_path)
                    ann2 = find_annotation(annotations, img2_path)
                    if ann1 and ann2 and 'Vehicles' in ann1['Object_type']['choices'] and 'Vehicles' in \
                            ann2['Object_type']['choices']:
                        pairs.append((img1_path, img2_path, ann1, ann2))
    if not pairs:
        logging.error("未找到符合条件的成对图片")
        return None, None, None, None

    if sort_by == "Quality":
        quality_order = {'Excellent (5/5)': 4, 'Good (4/5)': 3, 'Fair (3/5)': 2, 'Poor (2/5)': 1}
        pairs.sort(key=lambda x: quality_order.get(x[2]['Quality'], 0), reverse=True)
    elif sort_by == "Object_count":
        pairs.sort(key=lambda x: int(x[2].get('Object_count', 0)) + int(x[3].get('Object_count', 0)), reverse=True)

    return pairs[0] if pairs else (None, None, None, None)


# 生成 VQA 问题
def generate_vqa_prompt(image_path1, image_path2, ann1, ann2):
    if not (os.path.exists(image_path1) and os.path.exists(image_path2)):
        logging.error(f"图片文件不存在: {image_path1} 或 {image_path2}")
        return "错误：图片文件不存在"

    try:
        img1_base64 = encode_image(image_path1)
        img2_base64 = encode_image(image_path2)
        logging.debug(f"图片1 Base64 长度: {len(img1_base64)}, 图片2 Base64 长度: {len(img2_base64)}")
    except Exception as e:
        return f"错误：图片处理失败 - {str(e)}"

    ann1_data = parse_annotation(ann1)
    ann2_data = parse_annotation(ann2)

    # 预处理标注数据
    type1_str = ', '.join(ann1_data['type']) if ann1_data['type'] else '未知'
    type2_str = ', '.join(ann2_data['type']) if ann2_data['type'] else '未知'
    issues1_str = ', '.join([i['rectanglelabels'][0] for i in ann1_data['issues']]) if ann1_data['issues'] else '无'
    issues2_str = ', '.join([i['rectanglelabels'][0] for i in ann2_data['issues']]) if ann2_data['issues'] else '无'

    prompt = """
你是一个视觉问答助手。请分析两张输入图片，生成三道与图片中车辆内容相关的单项选择视觉问答题。
以下是标注信息：
- 图片1（{0}）：车辆数量 {1}，目标类型 {2}，协作无人机 {3}，感知问题 {4}。
- 图片2（{5}）：车辆数量 {6}，目标类型 {7}，协作无人机 {8}，感知问题 {9}。
问题需复杂且多样化，涵盖以下类型：
1. 计数：统计两张图片中的车辆总数或某类车辆数量（例如“两张图片中车辆总数”）。
2. 匹配：识别图片1中的某辆车对应图片2中的哪辆车（例如“{3} 视角中的某辆车对应 {8} 视角中的哪辆车”）。
3. 比较：比较两张图片中车辆的属性（如数量、类型、感知问题）。
要求：
- 每个问题基于图片和标注的实际内容，确保答案准确。
- 每个问题提供四个选项（A、B、C、D），选项需合理且具有区分度。
- 提供正确答案，参考标注数据（如车辆数量和感知问题）。
- 确保问题清晰、具体，避免歧义。
输出格式如下：
**问题 1**： [您的问题]
**选项**：
A. [选项 A]
B. [选项 B]
C. [选项 C]
D. [选项 D]
**正确答案**： [正确选项]

**问题 2**： [您的问题]
**选项**：
A. [选项 A]
B. [选项 B]
C. [选项 C]
D. [选项 D]
**正确答案**： [正确选项]

**问题 3**： [您的问题]
**选项**：
A. [选项 A]
B. [选项 B]
C. [选项 C]
D. [选项 D]
**正确答案**： [正确选项]
""".format(
        os.path.basename(image_path1), ann1_data['count'], type1_str, ann1_data['who'], issues1_str,
        os.path.basename(image_path2), ann2_data['count'], type2_str, ann2_data['who'], issues2_str
    )

    messages = [
        {
            "role": "user",
            "content": [
                {"image": f"data:image/jpeg;base64,{img1_base64}"},
                {"image": f"data:image/jpeg;base64,{img2_base64}"},
                {"text": prompt}
            ]
        }
    ]

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = dashscope.MultiModalConversation.call(
                model="qwen-vl-max",
                messages=messages,
                timeout=30
            )
            if response.status_code == 200 and response.output:
                logging.info("API 调用成功")
                return response.output.choices[0].message.content
            else:
                logging.error(f"API 调用失败，状态码：{response.status_code}，消息：{response.message}")
                return f"错误：API 调用失败，状态码：{response.status_code}，消息：{response.message}"
        except Exception as e:
            logging.error(f"尝试 {attempt + 1}/{max_retries} 失败: {str(e)}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数退避
            else:
                return f"错误：API 调用异常 - {str(e)}"


class VQAApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VQA 图片上传与问题生成")
        self.root.geometry("600x450")

        self.image_path1 = tk.StringVar()
        self.image_path2 = tk.StringVar()
        self.json_path = tk.StringVar(value="/Users/starryyu/Documents/tinghuasummer/train630/630-1.json")
        self.sort_by = tk.StringVar(value="Quality")

        # 图片选择
        tk.Label(root, text="图片 1:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        tk.Entry(root, textvariable=self.image_path1, width=50).grid(row=0, column=1, padx=5, pady=5)
        tk.Button(root, text="选择", command=self.select_image1).grid(row=0, column=2, padx=5, pady=5)

        tk.Label(root, text="图片 2:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        tk.Entry(root, textvariable=self.image_path2, width=50).grid(row=1, column=1, padx=5, pady=5)
        tk.Button(root, text="选择", command=self.select_image2).grid(row=1, column=2, padx=5, pady=5)

        # 标注文件
        tk.Label(root, text="标注文件:").grid(row=2, column=0, padx=5, pady=5, sticky="e")
        tk.Entry(root, textvariable=self.json_path, width=50).grid(row=2, column=1, padx=5, pady=5)
        tk.Button(root, text="选择", command=self.select_json).grid(row=2, column=2, padx=5, pady=5)

        # 排序选项
        tk.Label(root, text="排序标准:").grid(row=3, column=0, padx=5, pady=5, sticky="e")
        sort_options = ["Quality", "Object_count"]
        ttk.OptionMenu(root, self.sort_by, "Quality", *sort_options).grid(row=3, column=1, columnspan=2, padx=5, pady=5)

        # 运行按钮
        tk.Button(root, text="生成 VQA 问题", command=self.run_vqa).grid(row=4, column=0, columnspan=3, pady=10)

        # 输出区域
        self.output_text = scrolledtext.ScrolledText(root, width=70, height=15)
        self.output_text.grid(row=5, column=0, columnspan=3, padx=5, pady=5)

    def select_image1(self):
        path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.png")],
                                          initialdir="/Users/starryyu/Documents/tinghuasummer/train630")
        if path:
            self.image_path1.set(path)

    def select_image2(self):
        path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.png")],
                                          initialdir="/Users/starryyu/Documents/tinghuasummer/train630")
        if path:
            self.image_path2.set(path)

    def select_json(self):
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")],
                                          initialdir="/Users/starryyu/Documents/tinghuasummer/train630")
        if path:
            self.json_path.set(path)

    def run_vqa(self):
        self.output_text.delete(1.0, tk.END)
        image_path1 = self.image_path1.get()
        image_path2 = self.image_path2.get()
        json_path = self.json_path.get()

        if not (image_path1 and image_path2 and json_path):
            messagebox.showerror("错误", "请确保选择两张图片和标注文件")
            return

        try:
            annotations = load_annotations(json_path)
            base_dir = "/Users/starryyu/Documents/tinghuasummer/train630"
            # 优先使用手动选择，若无匹配标注则自动选择
            if image_path1 and image_path2:
                ann1 = find_annotation(annotations, image_path1)
                ann2 = find_annotation(annotations, image_path2)
                if not (ann1 and ann2):
                    img1_path, img2_path, ann1, ann2 = select_image_pair(base_dir, annotations, self.sort_by.get())
                else:
                    img1_path, img2_path = image_path1, image_path2
            else:
                img1_path, img2_path, ann1, ann2 = select_image_pair(base_dir, annotations, self.sort_by.get())

            if not (img1_path and img2_path and ann1 and ann2):
                messagebox.showerror("错误", "未找到符合条件的成对图片")
                return

            if not ('Vehicles' in ann1['Object_type']['choices'] and 'Vehicles' in ann2['Object_type']['choices']):
                messagebox.showerror("错误", "所选图片不包含车辆")
                return

            logging.info(f"处理图片：{img1_path}, {img2_path}")
            result = generate_vqa_prompt(img1_path, img2_path, ann1, ann2)
            self.output_text.insert(tk.END, result)
        except Exception as e:
            messagebox.showerror("错误", f"运行失败：{str(e)}")
            logging.error(f"运行失败：{str(e)}")


def main():
    root = tk.Tk()
    app = VQAApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()