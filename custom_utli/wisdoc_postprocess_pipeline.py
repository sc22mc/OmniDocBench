import markdown
import json
import os

def data_postprocess(data):
    for block in data['layout_dets']:
        
        # order string to int 
        block['order'] = int(block['order'])

        # 提取并转换 Markdown 表格为 HTML
        if block['category_type'] == "table":
            md = block['html'].strip()
            block['html'] = markdown.markdown(md, extensions=["tables"])

        # equation 转 key
        if block['category_type'] == "equation_isolated":
            if 'text' in block:
                block['latex'] = block['text']   # 新建 latex 键
                del block['text']                # 删除原来的 text 键
    return data

files = os.listdir('/Users/bytedance/Project/OmniDocBench/OursDataset/jsons')

for file in files:
    print(file)
    if file.endswith('.json'):
        with open(os.path.join('/Users/bytedance/Project/OmniDocBench/OursDataset/jsons', file), 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        data = data_postprocess(data)
        
        with open(os.path.join('/Users/bytedance/Project/OmniDocBench/OursDataset/jsons', file), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
