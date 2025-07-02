# 视觉问答（VQA）项目

本项目包含一个 Python 脚本（`vqa_script.py`），通过阿里云 DashScope API 调用 Qwen 多模态模型（`qwen-vl-max`），基于两张输入图片生成三道与车辆相关的单项选择视觉问答（VQA）问题。问题类型包括计数（例如两张图片中车辆总数）、匹配（例如图片1中的车辆对应图片2中的哪辆车）和比较（例如车辆属性差异）。

## 前提条件

- **操作系统**：macOS（Windows/Linux 可适配，需调整路径）。
- **Miniconda**：用于管理 Python 环境。
- **DashScope API 密钥**：从 [Model Studio](https://modelstudio.aliyun.com/) 获取。
- **图片**：两张包含车辆的 JPG/PNG 图片，放置在指定目录。

## 环境配置

### 1. 安装 Miniconda
- 下载并安装 macOS 版 Miniconda：[Miniconda 安装程序](https://docs.conda.io/en/latest/miniconda.html)。
- 验证安装：
  ```bash
  conda --version
  ```

### 2. 创建 Conda 环境
- 创建名为 `vqa_env` 的环境，使用 Python 3.8：
  ```bash
  conda create -n vqa_env python=3.8
  ```
- 激活环境：
  ```bash
  source /opt/miniconda3/bin/activate vqa_env
  ```

### 3. 安装依赖
- 安装所需 Python 包：
  ```bash
  pip install dashscope pillow
  ```
- 验证安装：
  ```bash
  pip list
  ```
  应显示 `dashscope` 和 `pillow`。

### 4. 配置 DashScope API 密钥
- **获取 API 密钥**：
  - 注册/登录 [Model Studio](https://modelstudio.aliyun.com/)。
  - 转到 **API-KEY > Create API Key**，复制密钥。
- **设置环境变量**：
  ```bash
  export DASHSCOPE_API_KEY="your_api_key"
  ```
  替换 `your_api_key` 为实际密钥。
- **持久化密钥**（可选）：
  编辑 `~/.zshrc`：
  ```bash
  nano ~/.zshrc
  ```
  添加：
  ```bash
  export DASHSCOPE_API_KEY="your_api_key"
  ```
  保存并应用：
  ```bash
  source ~/.zshrc
  ```
- 验证：
  ```bash
  echo $DASHSCOPE_API_KEY
  ```

### 5. 准备图片
- 将两张包含车辆的图片（例如 `image1.jpg` 和 `image2.jpg`）放入：
  ```
  /Users/starryyu/Documents/tinghuasummer/vpa/image_input/
  ```
- 确保图片为 JPG 或 PNG 格式，包含可识别的车辆（例如轿车、卡车）。
- 验证：
  ```bash
  ls /Users/starryyu/Documents/tinghuasummer/vpa/image_input
  ```
- 如果文件名不同，在 `vqa_script.py` 中更新路径：
  ```python
  image_path1 = os.path.join(image_dir, "your_image1.jpg")
  image_path2 = os.path.join(image_dir, "your_image2.jpg")
  ```

## 运行脚本

1. **克隆仓库**：
   ```bash
   git clone https://github.com/Starryyu77/vpa.git
   cd vpa
   ```

2. **运行脚本**：
   - **终端**：
     ```bash
     source /opt/miniconda3/bin/activate vqa_env
     /opt/miniconda3/envs/vqa_env/bin/python vqa_script.py
     ```
   - **PyCharm**：
     - 打开项目，配置解释器：`Preferences > Project > Python Interpreter`，选择 `/opt/miniconda3/envs/vqa_env/bin/python`。
     - 添加环境变量：`Run > Edit Configurations > vqa_script.py`，设置 `DASHSCOPE_API_KEY=your_api_key`。
     - 右键 `vqa_script.py` > `Run 'vqa_script'`。

3. **预期输出**：
   脚本生成三道车辆相关 VQA 问题，例如：
   ```
   2025-07-01 23:20:12,345 - INFO - 处理图片：/Users/starryyu/Documents/tinghuasummer/vpa/image_input/image1.jpg, /Users/starryyu/Documents/tinghuasummer/vpa/image_input/image2.jpg
   2025-07-01 23:20:14,678 - INFO - API 调用成功
   **问题 1**：两张图片中红色汽车的总数是多少？
   **选项**：
   A. 1
   B. 2
   C. 3
   D. 4
   **正确答案**： B

   **问题 2**：图片1中的蓝色轿车对应图片2中的哪辆车？
   **选项**：
   A. 白色 SUV
   B. 蓝色轿车
   C. 黑色卡车
   D. 红色面包车
   **正确答案**： B

   **问题 3**：哪张图片中的卡车数量更多？
   **选项**：
   A. 图片1
   B. 图片2
   C. 数量相同
   D. 无卡车
   **正确答案**： A
   ```
