import streamlit as st
from streamlit_drawable_canvas import st_canvas
import cv2
import numpy as np
from PIL import Image
import io

# 設定網頁標題與寬度
st.set_page_config(page_title="圖片去浮水印工具", layout="wide")

st.title("🖌️ 線上圖片去浮水印工具")
st.markdown("""
**使用說明：**
1. 上傳圖片。
2. 使用滑鼠在圖片上的 **浮水印位置塗抹** (會顯示為白色線條)。
3. 按下左側的 **「開始去除浮水印」** 按鈕。
""")

# 側邊欄設定
st.sidebar.header("工具設定")
stroke_width = st.sidebar.slider("畫筆粗細", 1, 50, 20)
bg_image = st.sidebar.file_uploader("上傳圖片:", type=["png", "jpg", "jpeg"])

def inpaint_image(original_image, mask_image):
    """
    使用 OpenCV 進行修復
    """
    # 轉換 PIL 圖片為 NumPy 陣列 (OpenCV 格式)
    img_np = np.array(original_image.convert('RGB'))
    # OpenCV 讀取是 BGR，PIL 是 RGB，需轉換
    img_cv = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
    
    # 處理遮罩：從 Canvas 取得的遮罩通常是 RGBA，我們只需要 Alpha 通道或灰階
    mask_np = np.array(mask_image.convert('L'))
    
    # 確保遮罩是二值化 (0 或 255)
    _, mask_binary = cv2.threshold(mask_np, 10, 255, cv2.THRESH_BINARY)
    
    # 進行修復 (Inpainting)
    result = cv2.inpaint(img_cv, mask_binary, 3, cv2.INPAINT_TELEA)
    
    # 轉回 RGB 以供網頁顯示
    result_rgb = cv2.cvtColor(result, cv2.COLOR_BGR2RGB)
    return Image.fromarray(result_rgb)

# 主畫面邏輯
if bg_image:
    image = Image.open(bg_image)
    
    # 建立兩欄佈局：左邊畫圖，右邊看結果
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("1. 請在此塗抹浮水印區域")
        # 建立繪圖畫布
        canvas_result = st_canvas(
            fill_color="rgba(255, 255, 255, 1.0)",  # 填充顏色 (這邊用不到)
            stroke_width=stroke_width,              # 畫筆粗細
            stroke_color="#FFFFFF",                 # 畫筆顏色 (白色代表遮罩)
            background_image=image,                 # 背景圖
            update_streamlit=True,
            height=image.height if image.height < 600 else 600, # 限制最大高度以免跑版
            width=image.width if image.width < 800 else 800,
            drawing_mode="freedraw",                # 自由繪圖模式
            key="canvas",
        )

    # 當用戶畫好並按下按鈕
    if st.sidebar.button("✨ 開始去除浮水印"):
        if canvas_result.image_data is not None:
            with st.spinner("正在修復圖片中..."):
                # 取得畫布上的「畫筆軌跡」作為遮罩
                mask_data = canvas_result.image_data
                mask_pil = Image.fromarray(mask_data.astype('uint8'), mode="RGBA")
                
                # 呼叫修復函數
                # 注意：canvas 輸出的尺寸必須跟原圖一致，這裡 library 會自動處理縮放
                # 但若圖片過大被 CSS 縮放，需確保解析度一致。
                # 簡單版我們假設 Canvas 與圖片 1:1 顯示
                
                # 為了確保精確，我們將 mask resize 到原圖大小 (以防 Canvas 顯示時縮放過)
                mask_pil = mask_pil.resize(image.size)

                fixed_image = inpaint_image(image, mask_pil)
                
                with col2:
                    st.subheader("2. 處理結果")
                    st.image(fixed_image, caption="已去除浮水印", use_column_width=True)
                    
                    # 準備下載按鈕
                    buf = io.BytesIO()
                    fixed_image.save(buf, format="PNG")
                    byte_im = buf.getvalue()
                    
                    st.download_button(
                        label="⬇️ 下載圖片",
                        data=byte_im,
                        file_name="fixed_image.png",
                        mime="image/png"
                    )
        else:
            st.warning("請先在左側圖片上塗抹要去除的區域！")
else:
    st.info("👈 請從左側側邊欄上傳圖片以開始使用。")