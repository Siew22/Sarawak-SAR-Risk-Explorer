# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file
COPY requirements.txt .

# Install dependencies
# 🔥 修改点：加了 --user 选项可能会导致路径问题，我们直接全局安装
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir streamlit pandas mysql-connector-python protobuf

# Copy the rest of the backend application code
COPY . .

# Expose the ports
EXPOSE 8000
EXPOSE 8501

# 🔥 修改点：显式添加 Streamlit 的路径到 PATH (以防万一)
ENV PATH="/usr/local/bin:${PATH}"

# Command to run the application
# 注意：这里虽然写了 CMD，但在 docker-compose.yml 里会被覆盖，但这行保留着也没事
CMD ["uvicorn", "main_professional:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]