import streamlit as st
import boto3
from io import BytesIO
from PIL import Image
import mimetypes

# Initialize S3 client with default AWS profile
s3 = boto3.client('s3')

# Streamlit app configuration
st.set_page_config(page_title="S3 Media Viewer", layout="wide")
st.sidebar.title("S3 Media Viewer")

# Bucket name input
bucket_name = st.sidebar.text_input("S3 Bucket Name")

# Get all folders in the bucket
if bucket_name:
    try:
        # List folder prefixes (CommonPrefixes)
        response = s3.list_objects_v2(Bucket=bucket_name, Delimiter='/')
        folders = [prefix['Prefix'].rstrip('/') for prefix in response.get('CommonPrefixes', [])]
        folders.insert(0, "(Root)")

        # Folder selection
        selected_folder = st.sidebar.selectbox("Select Folder", folders)
        prefix = '' if selected_folder == "(Root)" else selected_folder + '/'

        # List files in selected folder
        try:
            response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
            if 'Contents' in response:
                files = [f for f in response['Contents'] if f['Key'] != prefix]

                # Columns for image/video layout
                col1, col2 = st.columns(2)

                for file in files:
                    file_key = file['Key']
                    file_ext = file_key.split('.')[-1].lower()
                    file_name = file_key.split('/')[-1]

                    if file_ext in ['jpg', 'jpeg', 'png', 'gif']:
                        with col1:
                            try:
                                obj = s3.get_object(Bucket=bucket_name, Key=file_key)
                                image_bytes = obj['Body'].read()
                                image = Image.open(BytesIO(image_bytes))
                                st.image(image, caption=file_key, use_container_width=True)

                                mime_type, _ = mimetypes.guess_type(file_key)
                                st.download_button(
                                    label="Download from S3",
                                    data=image_bytes,
                                    file_name=file_name,
                                    mime=mime_type or "application/octet-stream",
                                    key=f"download_image_{file_key}"
                                )
                            except Exception as e:
                                st.error(f"Error loading image {file_key}: {str(e)}")

                    elif file_ext in ['mp4', 'avi', 'mov']:
                        with col2:
                            try:
                                obj = s3.get_object(Bucket=bucket_name, Key=file_key)
                                video_bytes = obj['Body'].read()
                                st.video(video_bytes)

                                mime_type, _ = mimetypes.guess_type(file_key)
                                st.download_button(
                                    label="Download from S3",
                                    data=video_bytes,
                                    file_name=file_name,
                                    mime=mime_type or "application/octet-stream",
                                    key=f"download_video_{file_key}"
                                )
                            except Exception as e:
                                st.error(f"Error loading video {file_key}: {str(e)}")

        except Exception as e:
            st.error(f"Error accessing folder contents: {str(e)}")

    except Exception as e:
        st.error(f"Error listing folders: {str(e)}")
else:
    st.warning("Please enter a bucket name in the sidebar.")
