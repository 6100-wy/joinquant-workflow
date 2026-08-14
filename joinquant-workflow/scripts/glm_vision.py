#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
glm_vision.py — 用智谱 GLM-4V-Flash（免费视觉模型）识别图片

用途：
  主模型（如 DeepSeek）是纯文本的，遇到需要"看图"的任务时，
  调用本脚本把图片发给 GLM-4V-Flash，拿到文字描述后继续处理。

用法：
  python glm_vision.py <图片路径> ["问题，可选"]
  python glm_vision.py shot.png "这张持仓截图里有哪些股票和金额？"

Key 读取顺序：
  1. 环境变量 ZHIPU_API_KEY
  2. 文件 C:\\Users\\Administrator\\.codex\\zhipu_api_key.txt（一行一个 key）

可换模型：--model glm-4.6v-flash（智谱更新一代免费视觉模型，128K 上下文）
"""

import argparse
import base64
import json
import mimetypes
import os
import sys
import tempfile
import urllib.error
import urllib.request


DEFAULT_MODEL = "glm-4v-flash"
API_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
KEY_FILE = r"C:\Users\Administrator\.codex\zhipu_api_key.txt"
MAX_IMAGE_BYTES = 4 * 1024 * 1024  # 智谱对图片体积有限制，超过 4MB 先提示
MAX_IMAGE_SIDE = 1800              # 压缩后的最长边


def get_api_key():
    """按优先级获取智谱 API Key。"""
    key = os.environ.get("ZHIPU_API_KEY", "").strip()
    if key:
        return key
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "r", encoding="utf-8") as fh:
            key = fh.read().strip()
        if key:
            return key
    return ""


def prepare_image(path):
    """超过 4MB 时用 Pillow 自动压缩到 JPEG；返回（图片路径, mime 类型）。"""
    size = os.path.getsize(path)
    if size > MAX_IMAGE_BYTES:
        try:
            from PIL import Image
        except ImportError:
            print(f"[警告] 图片 {size/1024/1024:.1f}MB，未安装 Pillow 无法自动压缩，可能被 API 拒绝。", file=sys.stderr)
            return path, "image/png"
        img = Image.open(path)
        scale = min(1.0, MAX_IMAGE_SIDE / max(img.width, img.height))
        if scale < 1.0:
            img = img.resize((int(img.width * scale), int(img.height * scale)), Image.LANCZOS)
        fd, tmp = tempfile.mkstemp(suffix=".jpg")
        os.close(fd)
        img.convert("RGB").save(tmp, "JPEG", quality=82)
        print(f"[信息] 原图 {size/1024/1024:.1f}MB，已自动压缩后发送。", file=sys.stderr)
        return tmp, "image/jpeg"
    mime, _ = mimetypes.guess_type(path)
    if mime is None or not mime.startswith("image/"):
        mime = "image/png"
    return path, mime


def image_to_data_uri(path):
    """把本地图片转成 base64 data URI，供 API 的 image_url 使用。"""
    prepared, mime = prepare_image(path)
    try:
        with open(prepared, "rb") as fh:
            b64 = base64.b64encode(fh.read()).decode("ascii")
    finally:
        if prepared != path:
            os.unlink(prepared)
    return f"data:{mime};base64,{b64}"


def call_vision(image_path, question, model):
    """调用智谱 OpenAI 兼容接口，返回模型回答文本。"""
    key = get_api_key()
    if not key:
        sys.exit(
            "未找到智谱 API Key。\n"
            "请先免费注册 https://open.bigmodel.cn/ 创建 API Key，然后：\n"
            "  方式一：设置环境变量 ZHIPU_API_KEY\n"
            "  方式二：把 Key 写入一行文件 " + KEY_FILE
        )
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": question},
                    {"type": "image_url", "image_url": {"url": image_to_data_uri(image_path)}},
                ],
            }
        ],
        "temperature": 0.2,
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        sys.exit(f"API 请求失败 HTTP {exc.code}: {body}")
    except urllib.error.URLError as exc:
        sys.exit(f"网络错误（检查代理/网络）：{exc.reason}")
    try:
        return data["choices"][0]["message"]["content"]
    except (KeyError, IndexError):
        sys.exit(f"响应格式异常：{json.dumps(data, ensure_ascii=False)[:500]}")


def main():
    parser = argparse.ArgumentParser(description="用智谱 GLM-4V-Flash 识别图片")
    parser.add_argument("image", help="图片路径")
    parser.add_argument("question", nargs="?", default="请详细描述这张图片的内容，包括所有可见的文字、数字、表格和图表数据。")
    parser.add_argument("--model", default=os.environ.get("VISION_MODEL", DEFAULT_MODEL), help="视觉模型 ID，默认 glm-4v-flash")
    args = parser.parse_args()
    if not os.path.isfile(args.image):
        sys.exit(f"图片不存在：{args.image}")
    answer = call_vision(args.image, args.question, args.model)
    print(answer)


if __name__ == "__main__":
    main()
