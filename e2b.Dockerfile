# Make sure to use this base image
FROM e2bdev/code-interpreter:latest

# Copy your CSV file into the container
COPY data_typesense_parcels2_100k.jsonl /app/data.csv
