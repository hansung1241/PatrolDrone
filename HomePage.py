from flask import Flask, render_template, jsonify, send_from_directory
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_images', methods=['GET'])
def get_images():
    image_dir = 'C:\\Users\\LG\\Desktop\\storage'  # 경로 수정
    images = []

    # storage 폴더에서 이미지 목록을 가져옴
    for filename in sorted(os.listdir(image_dir), reverse=True):
        if filename.endswith('.jpg'):
            timestamp = os.path.splitext(filename)[0]  # 파일 이름에서 타임스탬프 추출
            image_url = f"storage/{filename}"  # 이미지 파일의 URL
            images.append({
                'name': filename,
                'url': image_url,
                'timestamp': timestamp
            })

    return jsonify(images=images)

@app.route('/storage/<filename>')
def uploaded_file(filename):
    return send_from_directory('C:/Users/LG/Desktop/storage', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)