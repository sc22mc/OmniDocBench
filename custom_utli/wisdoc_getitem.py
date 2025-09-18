import os
import time
import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

API_BASE = "http://wisdoc-rs-dev.atominnolab.com/api/v2"

def upload_file(file_path):
    """上传文件并获取 JOB_ID"""
    print(f"提交文件: {file_path}")
    url = f"{API_BASE}/documents"
    with open(file_path, "rb") as f:
        files = {"file": f}
        resp = requests.post(url, files=files)
        resp.raise_for_status()
        res = resp.json()
        return res.get("job_id") or res.get("JOB_ID")

def check_status(job_id, interval=1):
    """轮询 JOB 状态直到完成，返回 RESULT_FILE_PATH"""
    url = f"{API_BASE}/documents/{job_id}"
    while True:
        resp = requests.get(url)
        resp.raise_for_status()
        res = resp.json()
        status = res.get("status")
        if status == "completed":
            return res.get("result_file_path")
        elif status == "failed":
            raise RuntimeError(f"Job {job_id} failed")
        time.sleep(interval)

def fetch_result(result_file_path):
    """获取解析结果"""
    url = f"{API_BASE}/files/{result_file_path}"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.text

def process_file(file_path, output_folder):
    """处理单个文件：上传 → 等待完成 → 获取结果 → 存文件"""
    job_id = upload_file(file_path)
    result_file_path = check_status(job_id)
    result = fetch_result(result_file_path)

    base_name = os.path.splitext(os.path.basename(file_path))[0]
    output_path = os.path.join(output_folder, f"{base_name}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json_data = json.loads(result)
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    print(f"完成: {file_path} → {output_path}")
    return output_path

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

def get_results(folder_path, output_folder, max_workers=5):
    """并发处理文件夹内所有 PDF 文件"""
    os.makedirs(output_folder, exist_ok=True)

    # 只处理 output_folder 中没有对应输出的 PDF 文件
    files = []
    for f in os.listdir(folder_path):
        if not f.lower().endswith(".pdf"):
            continue
        src_path = os.path.join(folder_path, f)

        # 假设输出文件名与源文件名类似，可以根据需求修改
        output_file = os.path.join("/Users/bytedance/Project/OmniDocBench/Models_ouput/wisdoc_output/pdf_json", f"{os.path.splitext(f)[0]}.json")
  
        if not os.path.exists(output_file):
            files.append(src_path)
        
    files.sort()
    files= [f for f in files if int(f.split('/')[-1].split('.')[0])>57]

    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_file, f, output_folder): f for f in files}
        # 使用 tqdm 添加进度条
        for future in tqdm(as_completed(futures), total=len(futures), desc="处理进度"):
            try:
                results.append(future.result())
            except Exception as e:
                print(f"文件 {futures[future]} 处理失败: {e}")
    return results


if __name__ == "__main__":
    input_folder = "/Users/bytedance/Project/OmniDocBench/OursDataset/pdfs"
    output_folder = "/Users/bytedance/Project/OmniDocBench/Models_ouput/wisdoc_output"

    results = get_results(input_folder, output_folder, max_workers=100)
    print("所有文件处理完成，结果存储在：", output_folder)