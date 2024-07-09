from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route('/', methods=['POST'])
def receive_data():
    # Parse JSON data sent to the endpoint
    data = request.json
    # Print the data to the console (or log it as needed)
    print("Received data:", data)
    # You can process the data as needed here
    # Respond back with a success message or any result
    return jsonify(message="Data received", yourData=data)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
