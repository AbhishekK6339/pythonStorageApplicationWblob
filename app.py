from flask import Flask, render_template, request, jsonify
import os
import subprocess
import sqlite3
from azure.storage.blob import BlobServiceClient

def create_app():
    app = Flask(__name__)

    # Initialize Azure Blob Storage connection
    blob_service_client = BlobServiceClient.from_connection_string(
        "DefaultEndpointsProtocol=https;AccountName=storageappdemo1;AccountKey=BFez0PUpQlgMwQ9RUuNko4nSGPOb+C8cwWhmhb/gZR7AbuyRAeJVPA5bfzcVC3gzkFJF0kEElbaP+AStnPr47w==;EndpointSuffix=core.windows.net")
    container_name = "uploads"  # Replace with your Azure Blob Storage container name

    @app.route("/", methods=["GET", "POST"])
    def upload_file():
        if request.method == "POST":
            try:
                # Connect to SQLite database or create a new one if it doesn't exist
                conn = sqlite3.connect('file_metadata.db')
                cursor = conn.cursor()

                if "file" not in request.files:
                    return jsonify({"error": "No file part"}), 400
                file = request.files["file"]
                if file.filename == "":
                    return jsonify({"error": "No selected file"}), 400

                # Upload file to Azure Blob Storage
                blob_client = blob_service_client.get_blob_client(container=container_name, blob=file.filename)
                blob_client.upload_blob(file)

                # Scan for viruses (if needed)
                virus_scan_result = scan_for_viruses(file)

                # Insert metadata into SQLite database
                user_details = request.form.get('user_details')  # Assuming user details are sent via a form field
                cursor.execute('''
                    INSERT INTO file_metadata (file_name, virus_scan_result, user_details)
                    VALUES (?, ?, ?)
                ''', (file.filename, virus_scan_result, user_details))
                conn.commit()

                if virus_scan_result:
                    return jsonify({"error": "File contains virus"}), 400
                else:
                    return jsonify({"message": f"File '{file.filename}' uploaded successfully"}), 200
            except Exception as e:
                return jsonify({"error": str(e)}), 500
            finally:
                # Close SQLite connection and cursor
                cursor.close()
                conn.close()
        else:
            return render_template("index.html")

    def scan_for_viruses(file):
        try:
            # Save file temporarily
            file_path = os.path.join("uploads", file.filename)
            file.save(file_path)

            # Run clamscan command to scan the file for viruses
            result = subprocess.run(["clamscan", "--stdout", "--no-summary", "--infected", file_path], capture_output=True,
                                    text=True)

            # Check if any viruses were detected
            virus_scan_result = "Infected files: 1" in result.stdout

            # Remove the file after scanning
            os.remove(file_path)

            return virus_scan_result
        except Exception as e:
            print("Error scanning for viruses:", e)
            return False  # Assume no virus found in case of errors

    return app

if __name__ == "__main__":
    create_app().run(debug=True)

