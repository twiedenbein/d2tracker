# Use an official Python runtime as a parent image
FROM python:3.8

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# fix reconnect
RUN sed -i "s/if op_code == ABNF.OPCODE_CLOSE:/if op_code == ABNF.OPCODE_CLOSE and not reconnect:/g" /usr/local/lib/python3.8/site-packages/websocket/_app.py
# Run the script when the container launches
CMD ["python", "./tracker.py"]
