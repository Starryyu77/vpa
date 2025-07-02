import dashscope
import base64
from PIL import Image
import io
import os


def encode_image(image_path):
    """将图片编码为 base64 字符串"""
    with Image.open(image_path) as img:
        buffered = io.BytesIO()
        img.save(buffered, format=img.format if img.format else "JPEG")
        return base64.b64encode(buffered.getvalue()).decode("utf-8")


def generate_vqa_prompt(image_path1, image_path2):
    """使用 Qwen API 生成 VQA 问题"""
    if not (os.path.exists(image_path1) and os.path.exists(image_path2)):
        return "错误：图片文件不存在"

    img1_base64 = encode_image(image_path1)
    img2_base64 = encode_image(image_path2)

    prompt = """
    分析两张输入图片，生成三道与两张图片中车辆内容相关的单项选择视觉问答题。问题应复杂且多样化，涵盖以下类型：
    1. 计数：统计两张图片中的车辆总数或某类车辆数量（如“两张图片中红色汽车的总数”）。
    2. 匹配：识别图片1中的某辆车对应图片2中的哪辆车（如“图片1中的蓝色轿车对应图片2中的哪辆车”）。
    3. 比较：比较两张图片中车辆的属性（如颜色、类型、数量差异）。
    要求：
    - 每个问题基于图片中车辆的实际内容，避免无关内容。
    - 每个问题提供四个选项（A、B、C、D），选项需合理且具有区分度。
    - 提供正确答案。
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
    """

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

    response = dashscope.MultiModalConversation.call(
        model="qwen-vl-max",
        messages=messages
    )

    if response.status_code == 200 and response.output:
        return response.output.choices[0].message.content
    return f"错误：API 调用失败，状态码：{response.status_code}，消息：{response.message}"


def main():
    # 使用提供的图片路径
    image_dir = "/Users/starryyu/Documents/tinghuasummer/vpa/image_input"
    image_path1 = os.path.join(image_dir, "image1.jpg")
    image_path2 = os.path.join(image_dir, "image2.jpg")

    result = generate_vqa_prompt(image_path1, image_path2)
    print(result)


if __name__ == "__main__":
    main()